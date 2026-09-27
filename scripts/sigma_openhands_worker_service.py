#!/usr/bin/env python3
"""Private Sigma coding-worker service using OpenHands LocalWorkspace."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
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


def _git_env() -> tuple[dict[str, str], Path]:
    token = os.getenv("SIGMA_GITHUB_TOKEN", "")
    if not token:
        raise WorkerError("SIGMA_GITHUB_TOKEN is required")
    root = Path(os.getenv("SIGMA_WORKER_ROOT", "/workspaces"))
    root.mkdir(parents=True, exist_ok=True)
    askpass = root / ".git-askpass.sh"
    askpass.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  *Username*) echo x-access-token ;;\n"
        "  *Password*) echo \"$SIGMA_GITHUB_TOKEN\" ;;\n"
        "  *) echo ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    askpass.chmod(0o700)
    env = os.environ.copy()
    env.update(
        {
            "GIT_ASKPASS": str(askpass),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Sigma Worker",
            "GIT_AUTHOR_EMAIL": "sigma-worker@localhost",
            "GIT_COMMITTER_NAME": "Sigma Worker",
            "GIT_COMMITTER_EMAIL": "sigma-worker@localhost",
        }
    )
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


def _open_hands_edit(workspace: Path, prompt: str, mission_id: str) -> dict[str, Any]:
    try:
        from pydantic import SecretStr
        from openhands.sdk import Agent, Conversation, LLM, LocalWorkspace
        from openhands.sdk.tool import Tool
        from openhands.tools.preset.default import register_default_tools
        from openhands.tools.terminal import TerminalTool
    except ImportError as exc:
        raise WorkerError("OpenHands worker dependencies are not installed") from exc

    model = os.getenv("SIGMA_WORKER_MODEL", "qwen2.5:7b")
    ollama_url = os.getenv("SIGMA_WORKER_OLLAMA_URL", "http://ollama:11434")
    timeout = int(os.getenv("SIGMA_WORKER_MODEL_TIMEOUT_SECONDS", "900"))

    llm = LLM(
        usage_id=f"sigma-worker:{mission_id}",
        model=f"ollama_chat/{model}",
        base_url=ollama_url,
        api_key=SecretStr("ollama"),
        reasoning_effort="none",
        num_retries=3,
        timeout=timeout,
    )
    register_default_tools(enable_browser=False)
    agent = Agent(
        llm=llm,
        tools=[Tool(name=TerminalTool.name)],
        system_prompt_kwargs={"cli_mode": True},
    )
    events: list[str] = []

    def callback(event: Any) -> None:
        events.append(type(event).__name__)

    with LocalWorkspace(working_dir=workspace) as local_workspace:
        conversation = Conversation(
            agent=agent,
            workspace=local_workspace,
            callbacks=[callback],
        )
        try:
            conversation.send_message(prompt)
            conversation.run()
            status = str(conversation.state.execution_status)
        finally:
            conversation.close()

    return {"status": status, "events": len(events)}


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
    for forbidden in (
        "production_release",
        "destructive_actions",
        "paid_spend",
        "direct_main_push",
    ):
        if authority.get(forbidden):
            raise WorkerError(f"Forbidden worker authority requested: {forbidden}")

    mission_id = str(payload.get("mission_id", "")).strip()
    if not mission_id:
        raise WorkerError("mission_id is required")
    issue_number = payload.get("issue_number")
    branch = _branch_name(
        int(issue_number) if issue_number is not None else None,
        mission_id,
    )

    worker_root = Path(os.getenv("SIGMA_WORKER_ROOT", "/workspaces")).resolve()
    workspace = (worker_root / mission_id).resolve()
    if worker_root not in workspace.parents:
        raise WorkerError("Invalid workspace path")
    if workspace.exists():
        shutil.rmtree(workspace)

    env, _ = _git_env()
    clone = _run(
        ["git", "clone", "--depth", "1", f"https://github.com/{repository}.git", str(workspace)],
        env=env,
        timeout=300,
    )
    if clone.returncode != 0:
        raise WorkerError(f"git clone failed: {clone.stderr[-800:]}")

    checkout = _run(["git", "checkout", "-b", branch], cwd=workspace, env=env)
    if checkout.returncode != 0:
        raise WorkerError(f"branch creation failed: {checkout.stderr[-800:]}")

    agent_result = _open_hands_edit(
        workspace,
        _mission_prompt(payload),
        mission_id,
    )

    diff_check = _run(["git", "diff", "--check"], cwd=workspace, env=env)
    if diff_check.returncode != 0:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "unresolved_failures": ["git diff --check failed"],
            "evidence": [diff_check.stderr[-1200:]],
        }

    status = _run(["git", "status", "--porcelain"], cwd=workspace, env=env)
    changed = [line for line in status.stdout.splitlines() if line.strip()]
    if not changed:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "unresolved_failures": ["OpenHands produced no repository changes"],
            "evidence": [f"openhands_status={agent_result['status']}"],
        }

    verify_args = _verify_command(repository)
    verification = _run(
        verify_args,
        cwd=workspace,
        env=env,
        timeout=int(os.getenv("SIGMA_WORKER_VERIFY_TIMEOUT_SECONDS", "900")),
    )
    tests_passed = verification.returncode == 0
    evidence = [
        f"openhands_status={agent_result['status']}",
        f"openhands_events={agent_result['events']}",
        f"changed_files={len(changed)}",
        f"verification_exit={verification.returncode}",
    ]
    if not tests_passed:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "branch": branch,
            "tests_executed": [" ".join(verify_args)],
            "unresolved_failures": ["Independent verification failed"],
            "evidence": evidence + [(verification.stdout + verification.stderr)[-3000:]],
        }

    if os.getenv("SIGMA_WORKER_ALLOW_WRITE", "0") != "1":
        return {
            "status": "TESTED",
            "mission_id": mission_id,
            "branch": branch,
            "tests_executed": [" ".join(verify_args)],
            "evidence": evidence + ["write_mode=disabled"],
            "next_action": "Enable SIGMA_WORKER_ALLOW_WRITE only after worker proof review.",
        }

    add = _run(["git", "add", "-A"], cwd=workspace, env=env)
    if add.returncode != 0:
        raise WorkerError("git add failed")
    commit = _run(
        ["git", "commit", "-m", f"Sigma worker: {payload.get('objective', 'bounded change')[:80]}"],
        cwd=workspace,
        env=env,
    )
    if commit.returncode != 0:
        raise WorkerError(f"git commit failed: {commit.stderr[-800:]}")
    sha = _run(["git", "rev-parse", "HEAD"], cwd=workspace, env=env).stdout.strip()

    push = _run(["git", "push", "-u", "origin", branch], cwd=workspace, env=env, timeout=300)
    if push.returncode != 0:
        raise WorkerError(f"git push failed: {push.stderr[-1200:]}")

    token = os.getenv("SIGMA_GITHUB_TOKEN", "")
    pr = _github_pr(
        repository,
        branch=branch,
        title=f"Sigma worker: {payload.get('objective', 'bounded change')[:100]}",
        body=(
            f"Automated bounded worker change for mission {mission_id}.\n\n"
            f"Issue: #{issue_number}\n\n"
            "Independent verification executed by the worker wrapper before push. "
            "This PR is not VERIFIED/RELEASED until Sigma's independent gates complete."
        ),
        token=token,
    )

    keep = os.getenv("SIGMA_WORKER_KEEP_WORKSPACE", "0") == "1"
    if not keep:
        shutil.rmtree(workspace, ignore_errors=True)

    return {
        "status": "TESTED",
        "mission_id": mission_id,
        "branch": branch,
        "commit_sha": sha,
        "pull_request_url": pr.get("html_url"),
        "tests_executed": [" ".join(verify_args)],
        "evidence": evidence,
        "next_action": "Sigma independent critic/security/evidence review.",
    }


def build_server() -> ThreadingHTTPServer:
    host = os.getenv("SIGMA_WORKER_HOST", "0.0.0.0")
    port = int(os.getenv("SIGMA_WORKER_PORT", "8091"))
    token = os.getenv("SIGMA_WORKER_TOKEN", "")
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise WorkerError("SIGMA_WORKER_TOKEN is required for non-loopback binding")
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        server_version = "SigmaWorker/1"

        def _json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            return not token or self.headers.get("Authorization") == f"Bearer {token}"

        def do_GET(self) -> None:
            if self.path == "/health":
                self._json(
                    200,
                    {
                        "status": "ok",
                        "worker": "openhands-local",
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

    return ThreadingHTTPServer((host, port), Handler)


def main() -> int:
    server = build_server()
    print(f"Sigma worker listening on {server.server_address}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
