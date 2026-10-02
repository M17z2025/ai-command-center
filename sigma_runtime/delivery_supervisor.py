"""End-to-end pull-request delivery supervision for Sigma.

This module advances a governed worker change through exact-head CI, bounded
repair, independent Sigma review, merge, and durable issue closure. It never
grants production deployment or secret-management authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Any, Protocol

from .pr_supervisor import PullRequestAssessment, PullRequestSupervisor


class DeliveryGitHub(Protocol):
    allow_write: bool

    def pull_request(self, repository: str, number: int) -> dict[str, Any]:
        ...

    def workflow_runs_for_head(
        self, repository: str, head_sha: str
    ) -> list[dict[str, Any]]:
        ...

    def workflow_run_jobs(
        self, repository: str, run_id: int
    ) -> list[dict[str, Any]]:
        ...

    def pull_request_files(
        self, repository: str, number: int
    ) -> list[dict[str, Any]]:
        ...

    def merge_pull_request(
        self, repository: str, number: int, expected_head_sha: str
    ) -> dict[str, Any]:
        ...

    def comment_issue(self, repository: str, number: int, body: str) -> None:
        ...

    def close_issue(self, repository: str, number: int) -> None:
        ...


class DeliveryWorker(Protocol):
    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class DeliveryOrchestrator(Protocol):
    def run(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class DeliveryResult:
    state: str
    pull_request_url: str
    pull_number: int
    head_sha: str
    repair_attempts: int
    review_mission_id: str = ""
    security_mission_id: str = ""
    merge_sha: str = ""
    evidence: tuple[str, ...] = ()
    blocker: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "pull_request_url": self.pull_request_url,
            "pull_number": self.pull_number,
            "head_sha": self.head_sha,
            "repair_attempts": self.repair_attempts,
            "review_mission_id": self.review_mission_id,
            "security_mission_id": self.security_mission_id,
            "merge_sha": self.merge_sha,
            "evidence": list(self.evidence),
            "blocker": self.blocker,
        }


class DeliverySupervisor:
    """Drive one worker PR to a valid repository terminal state."""

    def __init__(
        self,
        github: DeliveryGitHub,
        worker: DeliveryWorker,
        orchestrator: DeliveryOrchestrator,
        *,
        poll_seconds: float = 10.0,
        ci_timeout_seconds: int = 900,
        max_repairs: int = 2,
    ) -> None:
        self.github = github
        self.worker = worker
        self.orchestrator = orchestrator
        self.poll_seconds = max(0.0, float(poll_seconds))
        self.ci_timeout_seconds = max(1, int(ci_timeout_seconds))
        self.max_repairs = max(0, min(int(max_repairs), 5))

    def finish(
        self,
        *,
        repository: str,
        issue_number: int,
        mission_id: str,
        objective: str,
        issue_body: str,
        worker_result: dict[str, Any],
    ) -> DeliveryResult:
        pull_request_url = str(worker_result.get("pull_request_url") or "").strip()
        branch = str(worker_result.get("branch") or "").strip()
        if not pull_request_url or not branch:
            return DeliveryResult(
                state="BLOCKED",
                pull_request_url=pull_request_url,
                pull_number=0,
                head_sha="",
                repair_attempts=0,
                blocker="Worker result has no branch/pull-request evidence.",
            )

        supervisor = PullRequestSupervisor(self.github)
        repairs = 0

        while True:
            assessment = self._wait_for_ci(
                supervisor, repository, pull_request_url, branch
            )
            if assessment.state == "CI_PENDING":
                return DeliveryResult(
                    state="CI_PENDING",
                    pull_request_url=pull_request_url,
                    pull_number=assessment.pull_number,
                    head_sha=assessment.head_sha,
                    repair_attempts=repairs,
                    blocker="Exact-head CI did not reach a terminal state before timeout.",
                    evidence=(assessment.next_gate,),
                )

            if assessment.state == "CHANGES_REQUIRED":
                if repairs >= self.max_repairs:
                    return DeliveryResult(
                        state="BLOCKED",
                        pull_request_url=pull_request_url,
                        pull_number=assessment.pull_number,
                        head_sha=assessment.head_sha,
                        repair_attempts=repairs,
                        blocker="Bounded automatic repair attempts exhausted.",
                        evidence=tuple(self._failure_evidence(repository, assessment)),
                    )

                failure_evidence = self._failure_evidence(repository, assessment)
                repair_result = self.worker.dispatch(
                    {
                        "mission_id": f"{mission_id}-repair-{repairs + 1}",
                        "repository": repository,
                        "issue_number": issue_number,
                        "objective": objective,
                        "issue_body": issue_body,
                        "existing_branch": branch,
                        "pull_request_url": pull_request_url,
                        "failure_evidence": failure_evidence,
                        "repair_attempt": repairs + 1,
                        "authority": {
                            "production_release": False,
                            "destructive_actions": False,
                            "paid_spend": False,
                            "direct_main_push": False,
                        },
                    }
                )
                repair_status = str(repair_result.get("status", "BLOCKED")).upper()
                if repair_status not in {"CHANGED", "TESTED"}:
                    return DeliveryResult(
                        state="BLOCKED",
                        pull_request_url=pull_request_url,
                        pull_number=assessment.pull_number,
                        head_sha=assessment.head_sha,
                        repair_attempts=repairs,
                        blocker="Governed worker could not repair failed CI.",
                        evidence=tuple(
                            failure_evidence
                            + [
                                json.dumps(
                                    repair_result,
                                    ensure_ascii=False,
                                    default=str,
                                )[:4000]
                            ]
                        ),
                    )
                if (
                    str(repair_result.get("branch") or "") != branch
                    or str(repair_result.get("pull_request_url") or "")
                    != pull_request_url
                ):
                    return DeliveryResult(
                        state="BLOCKED",
                        pull_request_url=pull_request_url,
                        pull_number=assessment.pull_number,
                        head_sha=assessment.head_sha,
                        repair_attempts=repairs,
                        blocker="Repair worker did not preserve the existing PR/branch.",
                    )
                repairs += 1
                continue

            if assessment.state != "CI_PASSED":
                return DeliveryResult(
                    state="BLOCKED",
                    pull_request_url=pull_request_url,
                    pull_number=assessment.pull_number,
                    head_sha=assessment.head_sha,
                    repair_attempts=repairs,
                    blocker=f"Unsupported PR state: {assessment.state}",
                )

            evidence = self._review_evidence(repository, assessment)
            review = self.orchestrator.run(
                (
                    "Independently review this exact-head pull request as Sigma's "
                    "code/evidence critic. Determine whether the implementation "
                    "satisfies the issue, repository contract, tests and stated "
                    "acceptance criteria. Treat supplied GitHub evidence as authoritative. "
                    "Return PASS only when material implementation concerns are resolved."
                ),
                evidence=evidence,
                requested_by="sigma-delivery-supervisor",
                max_cycles=1,
            )
            review_status = str(review.get("status") or "")
            review_id = str(review.get("id") or "")
            if review_status != "COMPLETE":
                return DeliveryResult(
                    state="REVIEW_BLOCKED",
                    pull_request_url=pull_request_url,
                    pull_number=assessment.pull_number,
                    head_sha=assessment.head_sha,
                    repair_attempts=repairs,
                    review_mission_id=review_id,
                    blocker=f"Independent code/evidence review status: {review_status}",
                )

            security = self.orchestrator.run(
                (
                    "Perform an independent Sigma Cybersecurity Division release "
                    "review of this exact-head pull request. Check applicable trust "
                    "boundaries, secrets, dependency/supply-chain risk, authorization, "
                    "data isolation, infrastructure and AI-agent controls using only "
                    "the supplied repository evidence. Missing required evidence must "
                    "fail closed rather than be assumed."
                ),
                evidence=evidence,
                requested_by="sigma-security-gatekeeper",
                max_cycles=1,
            )
            security_status = str(security.get("status") or "")
            security_id = str(security.get("id") or "")
            if security_status != "COMPLETE":
                return DeliveryResult(
                    state="SECURITY_BLOCKED",
                    pull_request_url=pull_request_url,
                    pull_number=assessment.pull_number,
                    head_sha=assessment.head_sha,
                    repair_attempts=repairs,
                    review_mission_id=review_id,
                    security_mission_id=security_id,
                    blocker=f"Independent security review status: {security_status}",
                )

            if not self.github.allow_write:
                return DeliveryResult(
                    state="VERIFIED",
                    pull_request_url=pull_request_url,
                    pull_number=assessment.pull_number,
                    head_sha=assessment.head_sha,
                    repair_attempts=repairs,
                    review_mission_id=review_id,
                    security_mission_id=security_id,
                    blocker="Repository write/merge authority is disabled.",
                    evidence=("CI passed", "independent review passed", "security review passed"),
                )

            merged = self.github.merge_pull_request(
                repository,
                assessment.pull_number,
                assessment.head_sha,
            )
            if not merged.get("merged"):
                return DeliveryResult(
                    state="BLOCKED",
                    pull_request_url=pull_request_url,
                    pull_number=assessment.pull_number,
                    head_sha=assessment.head_sha,
                    repair_attempts=repairs,
                    review_mission_id=review_id,
                    security_mission_id=security_id,
                    blocker=str(merged.get("message") or "GitHub refused merge."),
                )

            merge_sha = str(merged.get("sha") or "")
            close_body = (
                "Sigma autonomous delivery evidence:\n"
                f"- PR: {pull_request_url}\n"
                f"- exact head: {assessment.head_sha}\n"
                f"- CI: passed\n"
                f"- independent review mission: {review_id}\n"
                f"- security mission: {security_id}\n"
                f"- merge commit: {merge_sha}\n"
                f"- automatic repair attempts: {repairs}\n"
            )
            self.github.comment_issue(repository, issue_number, close_body)
            self.github.close_issue(repository, issue_number)
            return DeliveryResult(
                state="DONE",
                pull_request_url=pull_request_url,
                pull_number=assessment.pull_number,
                head_sha=assessment.head_sha,
                repair_attempts=repairs,
                review_mission_id=review_id,
                security_mission_id=security_id,
                merge_sha=merge_sha,
                evidence=(
                    "exact-head CI passed",
                    "independent review passed",
                    "independent security review passed",
                    "pull request merged",
                    "issue closed with durable evidence",
                ),
            )

    def _wait_for_ci(
        self,
        supervisor: PullRequestSupervisor,
        repository: str,
        pull_request_url: str,
        branch: str,
    ) -> PullRequestAssessment:
        deadline = time.monotonic() + self.ci_timeout_seconds
        dispatched = False
        while True:
            assessment = supervisor.assess(repository, pull_request_url)
            if assessment.state != "CI_PENDING":
                return assessment

            if not assessment.workflow_runs and not dispatched:
                configured = [
                    item.strip()
                    for item in os.getenv(
                        "SIGMA_RUNNER_CI_WORKFLOWS", ""
                    ).split(",")
                    if item.strip()
                ]
                dispatcher = getattr(self.github, "dispatch_workflow", None)
                if configured and callable(dispatcher):
                    for workflow_id in configured:
                        dispatcher(repository, workflow_id, branch)
                    dispatched = True

            if time.monotonic() >= deadline:
                return assessment
            time.sleep(self.poll_seconds)

    def _failure_evidence(
        self,
        repository: str,
        assessment: PullRequestAssessment,
    ) -> list[str]:
        evidence: list[str] = []
        for run in assessment.failed_runs:
            run_id = int(run.get("id") or 0)
            if not run_id:
                continue
            evidence.append(
                "failed workflow "
                f"{run.get('name', run_id)} conclusion={run.get('conclusion')}"
            )
            try:
                jobs = self.github.workflow_run_jobs(repository, run_id)
            except Exception as exc:
                evidence.append(f"job evidence unavailable: {type(exc).__name__}")
                continue
            for job in jobs:
                if str(job.get("conclusion") or "").lower() in {
                    "success",
                    "skipped",
                    "neutral",
                }:
                    continue
                steps = job.get("steps") or []
                failed_steps = [
                    str(step.get("name") or "")
                    for step in steps
                    if str(step.get("conclusion") or "").lower()
                    not in {"success", "skipped", "neutral", ""}
                ]
                evidence.append(
                    f"job={job.get('name')} conclusion={job.get('conclusion')} "
                    f"failed_steps={failed_steps}"
                )
        return evidence[:30]

    def _review_evidence(
        self,
        repository: str,
        assessment: PullRequestAssessment,
    ) -> list[dict[str, Any]]:
        files = self.github.pull_request_files(repository, assessment.pull_number)
        compact_files = []
        for item in files[:100]:
            compact_files.append(
                {
                    "filename": item.get("filename"),
                    "status": item.get("status"),
                    "additions": item.get("additions"),
                    "deletions": item.get("deletions"),
                    "patch": str(item.get("patch") or "")[:12000],
                }
            )
        return [
            {
                "id": "pull-request",
                "source": f"github:{repository}#pull-{assessment.pull_number}",
                "content": json.dumps(
                    {
                        "head_sha": assessment.head_sha,
                        "files": compact_files,
                    },
                    ensure_ascii=False,
                )[:50000],
            },
            {
                "id": "exact-head-ci",
                "source": f"github-actions:{repository}@{assessment.head_sha}",
                "content": json.dumps(
                    list(assessment.workflow_runs),
                    ensure_ascii=False,
                    default=str,
                )[:30000],
            },
        ]
