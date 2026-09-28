"""Pull-request supervision for Sigma autonomous delivery.

This module observes exact PR-head GitHub Actions evidence and classifies the
next safe Sigma state. It never merges, deploys, or treats CI success as
independent security/user verification.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol


_PR_URL_RE = re.compile(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)(?:/.*)?$")


class PullRequestEvidenceClient(Protocol):
    def pull_request(self, repository: str, number: int) -> dict[str, Any]:
        ...

    def workflow_runs_for_head(self, repository: str, head_sha: str) -> list[dict[str, Any]]:
        ...


@dataclass(frozen=True)
class PullRequestAssessment:
    state: str
    repository: str
    pull_number: int
    head_sha: str
    workflow_runs: tuple[dict[str, Any], ...]
    failed_runs: tuple[dict[str, Any], ...] = ()
    next_gate: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "repository": self.repository,
            "pull_number": self.pull_number,
            "head_sha": self.head_sha,
            "workflow_runs": list(self.workflow_runs),
            "failed_runs": list(self.failed_runs),
            "next_gate": self.next_gate,
        }


def parse_pull_request_url(url: str) -> tuple[str, int]:
    match = _PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("pull_request_url must be a canonical github.com PR URL")
    return match.group(1), int(match.group(2))


class PullRequestSupervisor:
    """Classify exact-head CI state without over-claiming verification."""

    def __init__(self, github: PullRequestEvidenceClient) -> None:
        self.github = github

    def assess(self, expected_repository: str, pull_request_url: str) -> PullRequestAssessment:
        repository, number = parse_pull_request_url(pull_request_url)
        if repository.lower() != expected_repository.lower():
            raise ValueError("Worker PR repository does not match selected repository")

        pr = self.github.pull_request(repository, number)
        head = pr.get("head") or {}
        head_sha = str(head.get("sha") or pr.get("head_sha") or "").strip()
        if not head_sha:
            raise ValueError("Pull request has no head SHA")

        runs = tuple(self.github.workflow_runs_for_head(repository, head_sha))
        if not runs:
            return PullRequestAssessment(
                state="CI_PENDING",
                repository=repository,
                pull_number=number,
                head_sha=head_sha,
                workflow_runs=runs,
                next_gate="wait for exact-head CI evidence",
            )

        active = [
            run for run in runs
            if str(run.get("status", "")).lower() not in {"completed"}
        ]
        if active:
            return PullRequestAssessment(
                state="CI_PENDING",
                repository=repository,
                pull_number=number,
                head_sha=head_sha,
                workflow_runs=runs,
                next_gate="wait for exact-head CI completion",
            )

        failed = tuple(
            run
            for run in runs
            if str(run.get("conclusion", "")).lower()
            not in {"success", "skipped", "neutral"}
        )
        if failed:
            return PullRequestAssessment(
                state="CHANGES_REQUIRED",
                repository=repository,
                pull_number=number,
                head_sha=head_sha,
                workflow_runs=runs,
                failed_runs=failed,
                next_gate="diagnose failed exact-head CI and dispatch bounded repair",
            )

        return PullRequestAssessment(
            state="CI_PASSED",
            repository=repository,
            pull_number=number,
            head_sha=head_sha,
            workflow_runs=runs,
            next_gate="independent critic/security/evidence verification",
        )
