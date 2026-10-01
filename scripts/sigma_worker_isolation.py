"""Trusted Docker broker. Repository code never executes in this process.

Only regular file bytes cross the sandbox boundary. Docker is a privileged host
capability: deploy this broker on the private host, never expose its socket to jobs.
"""
from __future__ import annotations

import base64
import io
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile
import threading
import uuid

MAX_RESULT = 8 * 1024 * 1024
MAX_FILES = 500
SHA = re.compile(r"[0-9a-f]{40}\Z")
IMAGE = re.compile(r"(?:sha256:[0-9a-f]{64}|[a-zA-Z0-9./:_-]+@sha256:[0-9a-f]{64})\Z")


class IsolationError(RuntimeError):
    pass


def safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise IsolationError("Invalid change path")
    parts = PurePosixPath(value).parts
    if (value.startswith("/") or "\\" in value or ":" in value
            or any(p in {".", ".."} or p.lower() == ".git" for p in parts)
            or str(PurePosixPath(value)) != value
            or any(ord(c) < 32 for c in value)):
        raise IsolationError("Unsafe change path")
    # These files alter execution/authority and require a separately reviewed job.
    if (parts[0].lower() in {".github", ".sigma", ".agents", ".codex", "headquarters"}
            or any(p.lower() in {".gitmodules", ".gitattributes", "agents.md"} for p in parts)):
        raise IsolationError("Change affects a protected control path")
    return value


def validate_changes(raw: bytes) -> dict[str, bytes | None]:
    if len(raw) > MAX_RESULT:
        raise IsolationError("Change result too large")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise IsolationError("Duplicate change key")
            result[key] = value
        return result
    try:
        data = json.loads(raw, object_pairs_hook=unique)
        if not isinstance(data, dict) or not 0 < len(data) <= MAX_FILES:
            raise IsolationError("Empty or excessive change set")
        result = {}
        for path, content in data.items():
            safe_path(path)
            if content is not None and not isinstance(content, str):
                raise IsolationError("Invalid file content")
            result[path] = None if content is None else base64.b64decode(content, validate=True)
        names = {p.casefold() for p in result}
        if len(names) != len(result):
            raise IsolationError("Case-conflicting paths")
        for path in result:
            if any(str(p).casefold() in names for p in PurePosixPath(path).parents if str(p) != "."):
                raise IsolationError("Overlapping change paths")
        return result
    except (ValueError, TypeError) as exc:
        raise IsolationError("Malformed change result") from exc


def apply_changes(root: Path, changes: dict[str, bytes | None]) -> None:
    for path, content in changes.items():
        safe_path(path)
        dest = root / path
        if any(p.is_symlink() for p in [dest, *dest.parents] if p != root.parent):
            raise IsolationError("Symlink in change path")
        if dest.exists() and not dest.is_file():
            raise IsolationError("Change path is not a regular file")
        if content is None:
            dest.unlink(missing_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)


def clean_env() -> dict[str, str]:
    # No inherited GIT_CONFIG_COUNT, shell functions, proxy, preload or Python vars.
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "LANG": "C.UTF-8"}


def git(args: list[str], *, cwd: Path, env=None, input=None):
    command = ["git", "-c", "core.hooksPath=/dev/null", "-c", "credential.helper=",
               "-c", "core.attributesFile=/dev/null", "-c", "core.fsmonitor=false",
               "-c", "protocol.file.allow=never", "-c", "protocol.ext.allow=never",
               "-c", "submodule.recurse=false", *args]
    result = subprocess.run(command, cwd=cwd, env=env or clean_env(), input=input,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    if result.returncode:
        raise IsolationError("Trusted git operation failed: " + args[0])
    return result.stdout


def fetch_source(root: Path, repository: str, source_sha: str, env: dict) -> None:
    if not SHA.fullmatch(source_sha):
        raise IsolationError("A full lowercase source_sha is required")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise IsolationError("Invalid repository")
    root.mkdir(mode=0o700)
    git(["init", "--template=", str(root)], cwd=root)
    url = f"https://github.com/{repository}.git"
    git(["remote", "add", "origin", url], cwd=root)
    git(["fetch", "--no-tags", "--depth=1", "origin", source_sha], cwd=root, env=env)
    actual = git(["rev-parse", "FETCH_HEAD^{commit}"], cwd=root).decode().strip()
    if actual != source_sha:
        raise IsolationError("Fetched source SHA differs from mission")
    # Reject links/submodules before materializing source in a credential process.
    for record in git(["ls-tree", "-rz", source_sha], cwd=root).split(b"\0"):
        if record and record.split(b" ", 1)[0] not in {b"100644", b"100755"}:
            raise IsolationError("Source contains links or submodules")
    git(["checkout", "--detach", source_sha], cwd=root)


def source_archive(root: Path, source_sha: str) -> bytes:
    return git(["archive", "--format=tar", source_sha], cwd=root)


def workspace_archive(root: Path) -> bytes:
    out = io.BytesIO()
    total = 0
    with tarfile.open(fileobj=out, mode="w") as tar:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if ".git" in relative.parts:
                continue
            if path.is_symlink():
                raise IsolationError("Workspace contains link")
            if path.is_file():
                total += path.stat().st_size + 1024
                if total > 48 * 1024 * 1024:
                    raise IsolationError("Source exceeds sandbox transfer budget")
                tar.add(path, arcname=str(relative).replace("\\", "/"), recursive=False)
    return out.getvalue()


class DockerSandbox:
    def __init__(self, image: str, network: str = "none"):
        if not IMAGE.fullmatch(image):
            raise IsolationError("Sandbox image must be an immutable digest or image ID")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", network):
            raise IsolationError("Invalid sandbox network")
        self.image, self.network = image, network
        self.owner = os.getenv("SIGMA_WORKER_BROKER_ID", "sigma-worker")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", self.owner):
            raise IsolationError("Invalid broker identity")

    def cleanup_orphans(self) -> int:
        """Called before accepting jobs after restart; never during a live mission."""
        ids = self.docker(["ps", "--all", "--quiet", "--filter", "label=sigma.broker=" + self.owner]).decode().split()
        if any(not re.fullmatch(r"[0-9a-f]{12,64}", item) for item in ids):
            raise IsolationError("Unexpected Docker container identity")
        if ids:
            self.docker(["rm", "--force", *ids])
        return len(ids)

    def docker(self, args, *, data=None, timeout=60, max_output=MAX_RESULT + 65536):
        # Bound both output streams while reading, including deliberate floods.
        proc = subprocess.Popen(["docker", *args], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=clean_env())
        output = bytearray()
        exceeded = threading.Event()
        stopping = threading.Event()
        def drain(stream, retain):
            total = 0
            try:
                while not stopping.is_set():
                    # Unbuffered fd reads avoid a Python BufferedReader lock when
                    # the bounded shutdown path closes a stalled stream.
                    chunk = os.read(stream.fileno(), 65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_output:
                        exceeded.set()
                        proc.kill()
                        break
                    if retain:
                        output.extend(chunk)
            except (OSError, ValueError):
                pass
        def feed():
            try:
                if data:
                    remaining = memoryview(data)
                    while remaining and not stopping.is_set():
                        size = os.write(proc.stdin.fileno(), remaining[:65536])
                        remaining = remaining[size:]
                proc.stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                pass
        threads = [threading.Thread(target=drain, args=(proc.stdout, True), daemon=True),
                   threading.Thread(target=drain, args=(proc.stderr, False), daemon=True),
                   threading.Thread(target=feed, daemon=True)]
        for thread in threads:
            thread.start()
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            proc.wait()
            raise IsolationError("Docker operation timed out") from exc
        finally:
            for thread in threads:
                thread.join(timeout=5)
            stopping.set()
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                stream.close()
        if any(thread.is_alive() for thread in threads):
            raise IsolationError("Docker stream shutdown exceeded bound")
        if exceeded.is_set():
            raise IsolationError("Docker result exceeds bound")
        if code:
            raise IsolationError("Docker operation failed: " + args[0])
        return bytes(output)

    def check_network(self):
        if self.network == "none":
            return []
        info = json.loads(self.docker(["network", "inspect", self.network]))[0]
        peers = list(info.get("Containers", {}).values())
        if (not info.get("Internal") or len(peers) != 1 or info.get("Driver") != "bridge"
                or info.get("EnableIPv6")
                or info.get("Options", {}).get("com.docker.network.bridge.gateway_mode_ipv4") != "isolated"):
            raise IsolationError("Inference network must be internal with only its gateway")
        gateway = json.loads(self.docker(["inspect", peers[0]["Name"]]))[0]
        expected = os.getenv("SIGMA_WORKER_GATEWAY_IMAGE", "")
        if not IMAGE.fullmatch(expected):
            raise IsolationError("Inference gateway image is not pinned")
        expected_id = self.docker(["image", "inspect", "--format={{.Id}}", expected]).decode().strip()
        if gateway["Image"] != expected_id:
            raise IsolationError("Inference gateway image is not the approved immutable image")
        if gateway["Config"].get("Labels", {}).get("sigma.role") != "inference-gateway":
            raise IsolationError("Inference gateway identity missing")
        if not gateway.get("State", {}).get("Running"):
            raise IsolationError("Inference gateway is not running")
        address = str(ipaddress.IPv4Interface(peers[0]["IPv4Address"]).ip)
        return ["--dns=127.0.0.1", "--add-host=inference-gateway:" + address]

    def run(self, archive: bytes, request: dict, *, timeout: int = 900) -> bytes:
        network_options = self.check_network()
        name = "sigma-job-" + uuid.uuid4().hex
        try:
            self.docker(["create", "--name", name, "--network", self.network, *network_options,
                         "--label=sigma.broker=" + self.owner,
                         "--log-driver=none",
                         "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                         "--pids-limit=128", "--memory=2g", "--cpus=2", "--user=10001:10001",
                         "--ulimit=nofile=1024:1024", "--tmpfs=/tmp:rw,noexec,nosuid,size=128m",
                         "--tmpfs=/workspace:rw,nosuid,size=512m,uid=10001,gid=10001",
                         "--tmpfs=/home/sigmaworker:rw,nosuid,size=32m,uid=10001,gid=10001",
                         "--env=HOME=/home/sigmaworker", "--env=PYTHONDONTWRITEBYTECODE=1",
                         "--interactive", self.image, "python", "/app/sigma_worker_sandbox.py"])
            # Start with tar+request on stdin. No host mount, daemon socket or secrets.
            package = io.BytesIO()
            with tarfile.open(fileobj=package, mode="w") as tar:
                for filename, value in (("source.tar", archive), ("request.json", json.dumps(request).encode())):
                    member = tarfile.TarInfo(filename)
                    member.size = len(value)
                    tar.addfile(member, io.BytesIO(value))
            output = self.docker(["start", "--attach", "--interactive", name], data=package.getvalue(),
                                 timeout=timeout)
            state = json.loads(self.docker(["inspect", "--format={{json .State}}", name]))
            if state.get("Running") or state.get("OOMKilled") or state.get("ExitCode") != 0:
                raise IsolationError("Sandbox did not exit successfully")
            return b'{"verification_exit":0}' if request.get("mode") == "verify" else output
        finally:
            try:
                self.docker(["rm", "--force", name])
            except IsolationError:
                pass
