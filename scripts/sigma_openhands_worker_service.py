#!/usr/bin/env python3
"""Private Sigma coding-worker service using OpenHands LocalWorkspace."""

from __future__ import annotations

from contextlib import contextmanager
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

import yaml

from sigma_coding_harness import (
    HarnessPolicyError,
    build_mission_prompt,
    critical_capability_profile,
    repository_context,
    validate_changed_paths,
)


MAX_BODY = 500_000
BRANCH_RE = re.compile(r"[^a-zA-Z0-9._/-]+")
_SECRET_ENV_NAMES = (
    "SIGMA_GITHUB_TOKEN",
    "SIGMA_WORKER_TOKEN",
    "SIGMA_RUNTIME_TOKEN",
    "SIGMA_LLM_API_KEY",
)


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


def _safe_exec_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in _SECRET_ENV_NAMES:
        env.pop(name, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


@contextmanager
def _secrets_hidden_from_agent():
    saved = {name: os.environ.get(name) for name in _SECRET_ENV_NAMES}
    try:
        for name in _SECRET_ENV_NAMES:
            os.environ.pop(name, None)
        yield
    finally:
        for name, value in saved.items():
            if value is not None:
                os.environ[name] = value
            else:
                os.environ.pop(name, None)


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


def _verification_commands(workspace: Path) -> list[str]:
    manifest_path = workspace / ".sigma" / "project.yaml"
    if not manifest_path.exists():
        raise WorkerError("Repository is missing .sigma/project.yaml")
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WorkerError("Repository Sigma manifest is invalid YAML") from exc
    commands = manifest.get("commands", {}) if isinstance(manifest, dict) else {}
    if not isinstance(commands, dict):
        raise WorkerError("Repository Sigma manifest commands section is invalid")

    ordered_keys = ["install", "lint", "typecheck", "test"]
    selected: list[str] = []
    for key in ordered_keys:
        value = commands.get(key)
        if isinstance(value, str) and value.strip() and value.strip() not in selected:
            selected.append(value.strip())

    # If a repository has no normal verification command but does define a build,
    # use the build as the independent gate. Otherwise fail closed.
    if not any(
        isinstance(commands.get(key), str) and str(commands.get(key)).strip()
        for key in ("lint", "typecheck", "test")
    ):
        build = commands.get("build")
        if isinstance(build, str) and build.strip():
            selected.append(build.strip())

    verification = [
        item
        for item in selected
        if item != str(commands.get("install") or "").strip()
    ]
    if not verification:
        raise WorkerError(
            "Repository manifest has no independent lint/typecheck/test/build command"
        )
    return selected


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
            "User-Agent": "sigma-openhands-worker/2",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise WorkerError(
            f"GitHub PR creation failed HTTP {exc.code}: {detail}"
        ) from exc


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

    # The agent edits source but never receives wrapper-held GitHub/runtime secrets.
    with _secrets_hidden_from_agent():
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


def _mission_prompt(
    payload: dict[str, Any],
    context: str = "",
) -> str:
    try:
        return build_mission_prompt(payload, context)
    except HarnessPolicyError as exc:
        raise WorkerError(str(exc)) from exc


def _working_tree_paths(workspace: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    tracked = _run(
        ["git", "diff", "--name-only", "--no-renames", "-z", "HEAD"],
        cwd=workspace,
        env=_safe_exec_env(),
    )
    if tracked.returncode != 0:
        raise WorkerError(f"git diff path scan failed: {tracked.stderr[-800:]}")
    untracked = _run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=workspace,
        env=_safe_exec_env(),
    )
    if untracked.returncode != 0:
        raise WorkerError(
            f"git untracked path scan failed: {untracked.stderr[-800:]}"
        )

    tracked_paths = tuple(
        item for item in tracked.stdout.split("\x00") if item.strip()
    )
    untracked_paths = tuple(
        item for item in untracked.stdout.split("\x00") if item.strip()
    )
    return tracked_paths, untracked_paths

def run_mission(payload: dict[str, Any]) -> dict[str, Any]:
    repository = str(payload.get("repository", "")).strip()
    if repository not in _allowed_repositories():
        raise WorkerError(
            "Repository is not in SIGMA_WORKER_ALLOWED_REPOSITORIES"
        )

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
    existing_branch = str(payload.get("existing_branch") or "").strip()
    existing_pr = str(payload.get("pull_request_url") or "").strip()
    repair_mode = bool(existing_branch and existing_pr)
    branch = (
        existing_branch
        if repair_mode
        else _branch_name(
            int(issue_number) if issue_number is not None else None,
            mission_id,
        )
    )

    worker_root = Path(os.getenv("SIGMA_WORKER_ROOT", "/workspaces")).resolve()
    workspace = (worker_root / mission_id).resolve()
    if worker_root not in workspace.parents:
        raise WorkerError("Invalid workspace path")
    if workspace.exists():
        shutil.rmtree(workspace)

    git_env, _ = _git_env()
    clone_args = ["git", "clone", "--depth", "1"]
    if repair_mode:
        clone_args.extend(["--branch", branch, "--single-branch"])
    clone_args.extend([f"https://github.com/{repository}.git", str(workspace)])
    clone = _run(clone_args, env=git_env, timeout=300)
    if clone.returncode != 0:
        raise WorkerError(f"git clone failed: {clone.stderr[-800:]}")

    if not repair_mode:
        checkout = _run(
            ["git", "checkout", "-b", branch],
            cwd=workspace,
            env=git_env,
        )
        if checkout.returncode != 0:
            raise WorkerError(
                f"branch creation failed: {checkout.stderr[-800:]}"
            )

    locked_context = repository_context(workspace)
    agent_result = _open_hands_edit(
        workspace,
        _mission_prompt(payload, locked_context),
        mission_id,
    )

    tracked_paths, untracked_paths = _working_tree_paths(workspace)
    try:
        validated_paths = validate_changed_paths(
            workspace,
            (*tracked_paths, *untracked_paths),
        )
    except HarnessPolicyError as exc:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "branch": branch,
            "pull_request_url": existing_pr or None,
            "unresolved_failures": ["Coding harness path policy rejected worker output"],
            "evidence": [
                f"harness_policy_error={exc}",
                f"openhands_status={agent_result['status']}",
            ],
        }

    diff_check = _run(
        ["git", "diff", "--check"],
        cwd=workspace,
        env=_safe_exec_env(),
    )
    if diff_check.returncode != 0:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "branch": branch,
            "pull_request_url": existing_pr or None,
            "unresolved_failures": ["git diff --check failed"],
            "evidence": [diff_check.stderr[-1200:]],
        }

    verify_commands = _verification_commands(workspace)
    verification_outputs: list[str] = []
    tests_executed: list[str] = []
    verification_exit = 0
    for command in verify_commands:
        tests_executed.append(command)
        completed = _run(
            ["bash", "-lc", command],
            cwd=workspace,
            env=_safe_exec_env(),
            timeout=int(
                os.getenv("SIGMA_WORKER_VERIFY_TIMEOUT_SECONDS", "900")
            ),
        )
        verification_outputs.append(
            f"$ {command}\n{(completed.stdout + completed.stderr)[-4000:]}"
        )
        if completed.returncode != 0:
            verification_exit = completed.returncode
            break

    evidence = [
        f"openhands_status={agent_result['status']}",
        f"openhands_events={agent_result['events']}",
        f"changed_files={len(validated_paths)}",
        f"validated_paths={','.join(validated_paths)[:2000]}",
        f"harness_context_chars={len(locked_context)}",
        f"verification_exit={verification_exit}",
        f"verification_commands={len(tests_executed)}",
        "coding_harness=plan-inspect-edit-test-review",
        "github_authority=trusted-wrapper-only",
        "sandbox_execution=private-docker-worker",
        "agent_secret_exposure=blocked_by_wrapper",
    ]
    if verification_exit != 0:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "branch": branch,
            "pull_request_url": existing_pr or None,
            "tests_executed": tests_executed,
            "unresolved_failures": ["Independent manifest verification failed"],
            "evidence": evidence + verification_outputs[-2:],
        }

    post_tracked_paths, post_untracked_paths = _working_tree_paths(workspace)
    validated_set = set(validated_paths)
    post_change_set = set(post_tracked_paths).union(post_untracked_paths)
    missing_model_changes = sorted(validated_set.difference(post_change_set))
    unexpected_tracked_changes = sorted(
        set(post_tracked_paths).difference(validated_set)
    )
    if missing_model_changes or unexpected_tracked_changes:
        return {
            "status": "BLOCKED",
            "mission_id": mission_id,
            "branch": branch,
            "pull_request_url": existing_pr or None,
            "tests_executed": tests_executed,
            "unresolved_failures": [
                "Verification changed the governed source change set"
            ],
            "evidence": evidence
            + [
                "missing_model_changes="
                + ",".join(missing_model_changes)[:1200],
                "unexpected_tracked_changes="
                + ",".join(unexpected_tracked_changes)[:1200],
            ],
        }

    if os.getenv("SIGMA_WORKER_ALLOW_WRITE", "0") != "1":
        return {
            "status": "TESTED",
            "mission_id": mission_id,
            "branch": branch,
            "pull_request_url": existing_pr or None,
            "tests_executed": tests_executed,
            "evidence": evidence + ["write_mode=disabled"],
            "next_action": (
                "Enable SIGMA_WORKER_ALLOW_WRITE only after worker proof review."
            ),
        }

    add = _run(
        ["git", "add", "-A", "--", *validated_paths],
        cwd=workspace,
        env=git_env,
    )
    if add.returncode != 0:
        raise WorkerError("git add failed")
    commit = _run(
        [
            "git",
            "commit",
            "-m",
            (
                "Sigma repair: "
                if repair_mode
                else "Sigma worker: "
            )
            + str(payload.get("objective", "bounded change"))[:80],
        ],
        cwd=workspace,
        env=git_env,
    )
    if commit.returncode != 0:
        raise WorkerError(f"git commit failed: {commit.stderr[-800:]}")
    sha = _run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        env=_safe_exec_env(),
    ).stdout.strip()

    push = _run(
        ["git", "push", "-u", "origin", branch],
        cwd=workspace,
        env=git_env,
        timeout=300,
    )
    if push.returncode != 0:
        raise WorkerError(f"git push failed: {push.stderr[-1200:]}")

    if repair_mode:
        pr_url = existing_pr
    else:
        token = os.getenv("SIGMA_GITHUB_TOKEN", "")
        pr = _github_pr(
            repository,
            branch=branch,
            title=(
                f"Sigma worker: "
                f"{str(payload.get('objective', 'bounded change'))[:100]}"
            ),
            body=(
                f"Automated bounded worker change for mission {mission_id}.\n\n"
                f"Issue: #{issue_number}\n\n"
                "Independent manifest verification executed by the worker wrapper "
                "before push. This PR is not VERIFIED/RELEASED until Sigma's "
                "independent gates complete."
            ),
            token=token,
        )
        pr_url = str(pr.get("html_url") or "")

    keep = os.getenv("SIGMA_WORKER_KEEP_WORKSPACE", "0") == "1"
    if not keep:
        shutil.rmtree(workspace, ignore_errors=True)

    return {
        "status": "TESTED",
        "mission_id": mission_id,
        "branch": branch,
        "commit_sha": sha,
        "pull_request_url": pr_url,
        "tests_executed": tests_executed,
        "evidence": evidence,
        "repair_mode": repair_mode,
        "next_action": "Sigma delivery supervisor exact-head CI and independent gates.",
    }


def build_server() -> ThreadingHTTPServer:
    host = os.getenv("SIGMA_WORKER_HOST", "0.0.0.0")
    port = int(os.getenv("SIGMA_WORKER_PORT", "8091"))
    token = os.getenv("SIGMA_WORKER_TOKEN", "")
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise WorkerError(
            "SIGMA_WORKER_TOKEN is required for non-loopback binding"
        )
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        server_version = "SigmaWorker/3"

        def _json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _authorized(self) -> bool:
            return (
                not token
                or self.headers.get("Authorization") == f"Bearer {token}"
            )

        def do_GET(self) -> None:
            if self.path == "/health":
                self._json(
                    200,
                    {
                        "status": "ok",
                        "worker": "openhands-local",
                        "version": 3,
                        "write_enabled": (
                            os.getenv("SIGMA_WORKER_ALLOW_WRITE", "0") == "1"
                        ),
                        "allowed_repositories": sorted(
                            _allowed_repositories()
                        ),
                        "manifest_verification": True,
                        "repair_existing_pr": True,
                        "agent_secret_exposure": False,
                        "critical_capabilities": critical_capability_profile(),
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
                self._json(
                    409,
                    {"status": "BLOCKED", "error": "worker is busy"},
                )
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > MAX_BODY:
                    self._json(400, {"error": "invalid request size"})
                    return
                payload = json.loads(
                    self.rfile.read(length).decode("utf-8")
                )
                if not isinstance(payload, dict):
                    self._json(400, {"error": "JSON object required"})
                    return
                result = run_mission(payload)
                self._json(200, result)
            except WorkerError as exc:
                self._json(
                    409,
                    {"status": "BLOCKED", "error": str(exc)},
                )
            except Exception as exc:
                self._json(
                    500,
                    {"status": "BLOCKED", "error": type(exc).__name__},
                )
            finally:
                lock.release()

        def log_message(self, format: str, *args: Any) -> None:
            if os.getenv("SIGMA_WORKER_HTTP_LOG") == "1":
                super().log_message(format, *args)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> int:
    server = build_server()
    print(
        f"Sigma worker listening on {server.server_address}",
        flush=True,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
