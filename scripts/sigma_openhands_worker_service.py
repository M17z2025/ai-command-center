#!/usr/bin/env python3
"""Private Sigma trusted broker; repository execution uses disposable containers."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hmac
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sigma_worker_isolation import (DockerSandbox, IsolationError, SHA, apply_changes,
                                    clean_env, fetch_source, git, validate_changes, workspace_archive)


MAX_BODY = 500_000
BRANCH_RE = re.compile(r"[^a-zA-Z0-9._/-]+")


class WorkerError(RuntimeError):
    pass


def _allowed_repositories() -> set[str]:
    raw = os.getenv(
        "SIGMA_WORKER_ALLOWED_REPOSITORIES",
        "M17z2025/ai-command-center",
    )
    return {item.strip() for item in raw.split(",") if item.strip()}


def _branch_name(issue_number: int | None, mission_id: str) -> str:
    suffix = mission_id.replace("-", "")[:8]
    issue = f"issue-{issue_number}" if issue_number else "mission"
    branch = f"sigma/{issue}-{suffix}"
    return BRANCH_RE.sub("-", branch).strip("-/")


def _git_env() -> tuple[dict[str, str], Path | None]:
    token = os.getenv("SIGMA_GITHUB_TOKEN", "")
    allow_write = os.getenv("SIGMA_WORKER_ALLOW_WRITE", "0") == "1"
    env = clean_env()
    env.update({"GIT_AUTHOR_NAME": "Sigma Worker", "GIT_AUTHOR_EMAIL": "sigma-worker@localhost",
                "GIT_COMMITTER_NAME": "Sigma Worker", "GIT_COMMITTER_EMAIL": "sigma-worker@localhost"})
    if not token:
        if allow_write:
            raise WorkerError("SIGMA_GITHUB_TOKEN is required when worker write mode is enabled")
        # Public read-only proof may fetch anonymously. Private repository fetches
        # still fail closed, and no write/PR path is reachable without a token.
        return env, None
    root = Path(os.getenv("SIGMA_WORKER_ROOT", "/workspaces"))
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    askpass = root / ".git-askpass.sh"
    askpass.write_text('#!/bin/sh\ncase "$1" in\n *Username*) echo x-access-token ;;\n *Password*) echo "$SIGMA_GITHUB_TOKEN" ;;\nesac\n', encoding="utf-8")
    askpass.chmod(0o700)
    env.update({"SIGMA_GITHUB_TOKEN": token, "GIT_ASKPASS": str(askpass)})
    return env, askpass


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _verify_command(repository: str) -> list[str]:
    if repository == "M17z2025/ai-command-center":
        return [
            "bash",
            "-lc",
            "python -m unittest discover -s tests -p 'test_*.py' "
            "&& python scripts/validate_control_plane.py",
        ]
    raise WorkerError(f"No independent verification command registered for {repository}")


def _github_pr(
    repository: str,
    *,
    branch: str,
    title: str,
    body: str,
    token: str,
) -> dict[str, Any]:
    payload = json.dumps(
        {
            "title": title,
            "head": branch,
            "base": "main",
            "body": body,
            "maintainer_can_modify": True,
        }
    ).encode("utf-8")
    req = Request(
        f"https://api.github.com/repos/{repository}/pulls",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "sigma-openhands-worker/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise WorkerError(f"GitHub PR creation failed HTTP {exc.code}: {detail}") from exc



def _mission_prompt(payload: dict[str, Any]) -> str:
    objective = str(payload.get("objective", "")).strip()
    issue_body = str(payload.get("issue_body", "")).strip()
    if not objective:
        raise WorkerError("objective is required")
    return (
        "You are a bounded coding worker under Sigma authority.\n"
        "Work only in the current repository checkout.\n"
        "Do not deploy, manage secrets, change repository settings, push branches, "
        "open pull requests, or modify production systems. The wrapper handles GitHub.\n"
        "Make the smallest correct code change needed for the task.\n"
        "Run relevant local tests where useful, but do not claim VERIFIED or RELEASED.\n\n"
        f"OBJECTIVE:\n{objective}\n\n"
        f"ISSUE DETAILS:\n{issue_body[:16000]}\n"
    )


def run_mission(payload: dict[str, Any]) -> dict[str, Any]:
    repository = str(payload.get("repository", "")).strip()
    if repository not in _allowed_repositories():
        raise WorkerError("Repository is not in SIGMA_WORKER_ALLOWED_REPOSITORIES")
    authority = payload.get("authority") or {}
    for forbidden in ("production_release", "destructive_actions", "paid_spend", "direct_main_push",
                      "secret_management", "security_control_reduction"):
        if authority.get(forbidden):
            raise WorkerError(f"Forbidden worker authority requested: {forbidden}")
    source_sha = str(payload.get("source_sha", ""))
    if not SHA.fullmatch(source_sha):
        raise WorkerError("A full source_sha is required")
    mission_id = str(payload.get("mission_id", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", mission_id):
        raise WorkerError("Invalid mission_id")
    issue_number = payload.get("issue_number")
    branch = _branch_name(int(issue_number) if issue_number else None, mission_id)
    prompt = _mission_prompt(payload)
    verify_args = _verify_command(repository)
    root = Path(os.getenv("SIGMA_WORKER_ROOT", "/workspaces"))
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        sandbox = DockerSandbox(os.getenv("SIGMA_WORKER_SANDBOX_IMAGE", ""),
                                os.getenv("SIGMA_WORKER_INFERENCE_NETWORK", "none"))
        if sandbox.network == "none":
            raise WorkerError("A dedicated internal inference gateway network is required")
        verifier = DockerSandbox(sandbox.image)
        env, _ = _git_env()
        with tempfile.TemporaryDirectory(prefix="mission-", dir=root) as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            fetch_source(source, repository, source_sha, env)
            # Credential process never invokes tests, shell scripts or SDK from source.
            archive = workspace_archive(source)
            raw = sandbox.run(archive, {"mode": "edit", "prompt": prompt,
                                       "model": os.getenv("SIGMA_WORKER_MODEL", "qwen2.5:7b")})
            changes = validate_changes(raw)
            fetch_source(target, repository, source_sha, env)
            apply_changes(target, changes)
            git(["diff", "--check"], cwd=target)
            candidate = workspace_archive(target)
            verification = json.loads(verifier.run(candidate, {"mode": "verify", "command": verify_args}))
            evidence = [f"source_sha={source_sha}", f"sandbox_image={sandbox.image}",
                        "execution_boundary=disposable-container", "verification_network=none",
                        f"changed_files={len(changes)}", f"verification_exit={verification.get('verification_exit')}"]
            result = {"status": "BLOCKED", "mission_id": mission_id, "source_sha": source_sha,
                      "branch": branch, "tests_executed": [" ".join(verify_args)], "evidence": evidence}
            if verification.get("verification_exit") != 0:
                result["unresolved_failures"] = ["Isolated independent verification failed"]
                return result
            result["status"] = "TESTED"
            if os.getenv("SIGMA_WORKER_ALLOW_WRITE", "0") != "1":
                result["next_action"] = "Write mode is disabled; complete host commissioning evidence."
                return result
            git(["checkout", "-b", branch], cwd=target)
            git(["add", "-A"], cwd=target)
            git(["commit", "--no-verify", "-m", "Sigma bounded mission " + mission_id], cwd=target, env=env)
            sha = git(["rev-parse", "HEAD"], cwd=target).decode().strip()
            # Only this generated branch can be written, never arbitrary payload refs.
            git(["push", "origin", f"HEAD:refs/heads/{branch}"], cwd=target, env=env)
            pr = _github_pr(repository, branch=branch,
                            title=f"Sigma worker: {payload.get('objective', 'bounded change')[:100]}",
                            body=f"Bounded mission {mission_id} from exact source `{source_sha}`.\n\n"
                                 f"Issue: #{issue_number}\n\nDisposable credential-free verification passed. "
                                 "Independent Sigma security and release gates remain required.",
                            token=env["SIGMA_GITHUB_TOKEN"])
            result.update(commit_sha=sha, pull_request_url=pr.get("html_url"),
                          next_action="Sigma independent critic/security/evidence review.")
            return result
    except IsolationError as exc:
        raise WorkerError(str(exc)) from exc


def build_server() -> ThreadingHTTPServer:
    host = os.getenv("SIGMA_WORKER_HOST", "0.0.0.0")
    port = int(os.getenv("SIGMA_WORKER_PORT", "8091"))
    token = os.getenv("SIGMA_WORKER_TOKEN", "")
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise WorkerError("SIGMA_WORKER_TOKEN is required for non-loopback binding")
    lock = threading.Lock()

    class BoundedServer(ThreadingHTTPServer):
        slots = threading.BoundedSemaphore(16)

        def process_request(self, request, client_address):
            if not self.slots.acquire(blocking=False):
                self.shutdown_request(request)
                return
            try:
                super().process_request(request, client_address)
            except Exception:
                self.slots.release()
                raise

        def process_request_thread(self, request, client_address):
            try:
                super().process_request_thread(request, client_address)
            finally:
                self.slots.release()

    class Handler(BaseHTTPRequestHandler):
        server_version = "SigmaWorker/1"

        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def _json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            return not token or hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}")

        def do_GET(self) -> None:
            if self.path == "/health":
                self._json(
                    200,
                    {
                        "status": "ok",
                        "worker": "openhands-isolated-broker",
                        "write_enabled": os.getenv("SIGMA_WORKER_ALLOW_WRITE", "0") == "1",
                        "allowed_repositories": sorted(_allowed_repositories()),
                    },
                )
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/missions":
                self._json(404, {"error": "not found"})
                return
            if not self._authorized():
                self._json(401, {"error": "unauthorized"})
                return
            if not lock.acquire(blocking=False):
                self._json(409, {"status": "BLOCKED", "error": "worker is busy"})
                return
            try:
                self.connection.settimeout(10)
                if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
                    self._json(400, {"error": "invalid request framing"})
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY:
                    self._json(400, {"error": "invalid request size"})
                    return
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    self._json(400, {"error": "JSON object required"})
                    return
                result = run_mission(payload)
                self._json(200, result)
            except WorkerError as exc:
                self._json(409, {"status": "BLOCKED", "error": str(exc)})
            except Exception as exc:
                self._json(500, {"status": "BLOCKED", "error": type(exc).__name__})
            finally:
                lock.release()

        def log_message(self, format: str, *args: Any) -> None:
            if os.getenv("SIGMA_WORKER_HTTP_LOG") == "1":
                super().log_message(format, *args)

    return BoundedServer((host, port), Handler)


def main() -> int:
    image = os.getenv("SIGMA_WORKER_SANDBOX_IMAGE", "")
    if image:
        # Restart reconciliation precedes mission intake. Multiple brokers on one
        # host must use different broker IDs and private mission endpoints.
        removed = DockerSandbox(image).cleanup_orphans()
        print(f"Sigma worker recovered {removed} orphaned containers", flush=True)
    server = build_server()
    print(f"Sigma worker listening on {server.server_address}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
