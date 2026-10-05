#!/usr/bin/env python3
"""Sigma-native coding-harness controls.

These controls adapt the useful safety/structure patterns from the critical
coding examples in Arindam200/awesome-ai-apps while keeping Sigma's existing
private, zero-paid execution architecture. The model is treated as untrusted:
workspace boundaries, path validation, deterministic verification and GitHub
authority are enforced outside the model.
"""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MAX_CONTEXT_CHARS = 24_000
MAX_CONTEXT_FILES = 400
_BLOCKED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "dist",
    "build",
    "coverage",
}
_SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".netrc",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "credentials.json",
    "service-account.json",
    "secrets.toml",
}
_SENSITIVE_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".keystore",
}


class HarnessPolicyError(RuntimeError):
    """Raised when a proposed workspace change violates Sigma policy."""


def critical_capability_profile() -> dict[str, Any]:
    """Return the five critical upstream patterns as Sigma-owned capabilities."""

    return {
        "multi_agent_coding_harness": "sigma-plan+worker-execute+delivery-supervisor",
        "coding_harness_starter": "locked-workspace+deterministic-verification+bounded-repair",
        "local_file_editing_agent": "mechanical-path-gate+scoped-checkout",
        "sandboxed_code_execution_mcp": "private-docker-worker+wrapper-owned-tests",
        "github_mcp_agent": "trusted-control-plane-github-client",
        "paid_external_dependencies": False,
        "agent_has_github_credentials": False,
    }


def _normalise_relative(path: str) -> PurePosixPath:
    raw = str(path).strip()
    if not raw or "\x00" in raw:
        raise HarnessPolicyError("Changed path is empty or contains NUL")
    raw = raw.replace("\\", "/")
    relative = PurePosixPath(raw)
    if relative.is_absolute():
        raise HarnessPolicyError(f"Absolute path is forbidden: {raw}")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise HarnessPolicyError(f"Traversal/non-canonical path is forbidden: {raw}")
    return relative


def _reject_sensitive(relative: PurePosixPath) -> None:
    lowered = [part.lower() for part in relative.parts]
    if any(part in _BLOCKED_DIRS for part in lowered):
        raise HarnessPolicyError(
            f"Generated/VCS path is outside coding scope: {relative.as_posix()}"
        )
    name = lowered[-1]
    if name.startswith(".env") and name not in {
        ".env.example",
        ".env.sample",
        ".env.template",
    }:
        raise HarnessPolicyError(
            f"Sensitive environment file is outside coding scope: {relative.as_posix()}"
        )
    if name in _SENSITIVE_NAMES:
        raise HarnessPolicyError(
            f"Sensitive file is outside coding scope: {relative.as_posix()}"
        )
    if any(name.endswith(suffix) for suffix in _SENSITIVE_SUFFIXES):
        raise HarnessPolicyError(
            f"Credential/key material is outside coding scope: {relative.as_posix()}"
        )


def validate_workspace_path(workspace: Path, path: str) -> str:
    """Validate one model-changed path against the locked checkout root."""

    root = workspace.resolve()
    relative = _normalise_relative(path)
    _reject_sensitive(relative)
    target = root.joinpath(*relative.parts)

    current = root
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise HarnessPolicyError(
                f"Symlink path is forbidden: {relative.as_posix()}"
            )

    resolved = target.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise HarnessPolicyError(
            f"Changed path resolves outside workspace: {relative.as_posix()}"
        )
    if target.exists() and target.is_dir():
        raise HarnessPolicyError(
            f"Changed path must be a file: {relative.as_posix()}"
        )
    return relative.as_posix()


def validate_changed_paths(workspace: Path, paths: Iterable[str]) -> tuple[str, ...]:
    """Validate and canonicalise the complete model-produced change set."""

    validated: list[str] = []
    seen: set[str] = set()
    for path in paths:
        canonical = validate_workspace_path(workspace, path)
        if canonical not in seen:
            seen.add(canonical)
            validated.append(canonical)
    if not validated:
        raise HarnessPolicyError("Worker produced no valid repository file changes")
    return tuple(validated)


def _safe_context_file(workspace: Path, relative: str, limit: int) -> str:
    try:
        canonical = validate_workspace_path(workspace, relative)
    except HarnessPolicyError:
        return ""
    path = workspace / canonical
    if not path.is_file() or path.is_symlink():
        return ""
    try:
        data = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    return data[:limit]


def repository_context(
    workspace: Path,
    *,
    max_files: int = MAX_CONTEXT_FILES,
    max_chars: int = MAX_CONTEXT_CHARS,
) -> str:
    """Build bounded, secret-safe context from the locked checkout.

    This replaces the need to give the coding model a GitHub token/MCP server.
    Sigma's trusted control plane gathers remote GitHub state; the worker sees
    only bounded repository material inside its checkout plus the Sigma mission.
    """

    root = workspace.resolve()
    file_inventory: list[str] = []

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name.lower() not in _BLOCKED_DIRS
        )
        for filename in sorted(filenames):
            candidate = Path(current_root) / filename
            relative = candidate.relative_to(root).as_posix()
            try:
                canonical = validate_workspace_path(root, relative)
            except HarnessPolicyError:
                continue
            if candidate.is_symlink() or not candidate.is_file():
                continue
            file_inventory.append(canonical)
            if len(file_inventory) >= max_files:
                break
        if len(file_inventory) >= max_files:
            break

    sections = [
        "FILE INVENTORY (bounded):\n" + "\n".join(file_inventory),
    ]
    for label, path, limit in (
        ("SIGMA MANIFEST", ".sigma/project.yaml", 6_000),
        ("PROJECT STATUS", "PROJECT_STATUS.md", 6_000),
        ("README", "README.md", 6_000),
        ("AGENT CONTRACT", "AGENTS.md", 4_000),
    ):
        text = _safe_context_file(root, path, limit)
        if text:
            sections.append(f"{label}:\n{text}")

    joined = "\n\n".join(sections)
    return joined[:max_chars]


def build_mission_prompt(payload: dict[str, Any], context: str) -> str:
    """Build the bounded plan/inspect/edit/review contract for OpenHands."""

    objective = str(payload.get("objective", "")).strip()
    issue_body = str(payload.get("issue_body", "")).strip()
    if not objective:
        raise HarnessPolicyError("objective is required")

    sigma_mission = payload.get("sigma_mission")
    mission_text = ""
    if sigma_mission:
        try:
            mission_text = json.dumps(
                sigma_mission, ensure_ascii=False, sort_keys=True
            )[:12_000]
        except (TypeError, ValueError):
            mission_text = str(sigma_mission)[:12_000]

    failure_evidence = payload.get("failure_evidence") or []
    repair_attempt = payload.get("repair_attempt")
    repair_text = ""
    if failure_evidence:
        repair_text = (
            "\nTHIS IS A BOUNDED REPAIR PASS. Diagnose the supplied exact-head "
            "failure evidence and repair only the demonstrated defect.\n"
            f"REPAIR ATTEMPT: {repair_attempt}\n"
            f"FAILURE EVIDENCE:\n"
            f"{json.dumps(failure_evidence, ensure_ascii=False)[:12_000]}\n"
        )

    return (
        "You are the bounded coding worker inside Sigma's governed coding harness.\n"
        "Sigma, not you, owns mission authority, GitHub writes, CI, security review, "
        "merge and release decisions. GitHub/runtime credentials are deliberately "
        "outside your environment.\n\n"
        "EXECUTION CONTRACT — follow these phases in order:\n"
        "1. PLAN: use the supplied Sigma mission and repository context; state the "
        "smallest implementation approach internally before changing files.\n"
        "2. INSPECT: read the relevant existing files/tests before editing. Never "
        "guess repository state.\n"
        "3. EDIT: make the smallest correct change inside the current checkout only. "
        "Do not touch .git, secrets, credential files, dependency/generated trees, "
        "or paths outside the checkout. Do not deploy, push branches, open pull requests, change repo "
        "settings, manage secrets, or perform paid actions.\n"
        "4. SELF-REVIEW: inspect your diff against the issue and Sigma mission. "
        "Remove accidental/unrelated changes. You may run local diagnostics, but "
        "only the wrapper-owned manifest verification is accepted as test evidence.\n"
        "5. HANDOFF: finish with the checkout changed and leave GitHub/CI actions to "
        "the Sigma wrapper and delivery supervisor. Never claim VERIFIED/RELEASED.\n\n"
        f"OBJECTIVE:\n{objective}\n\n"
        f"ISSUE DETAILS:\n{issue_body[:16_000]}\n\n"
        f"SIGMA PLAN/MISSION:\n{mission_text or '(not supplied)'}\n\n"
        f"LOCKED REPOSITORY CONTEXT:\n{context[:MAX_CONTEXT_CHARS]}\n"
        f"{repair_text}"
    )
