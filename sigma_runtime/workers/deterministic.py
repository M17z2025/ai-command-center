"""Deterministic worker used to prove the Sigma worker contract in CI."""

from __future__ import annotations

from .base import AuditSink, WorkerMission, WorkerResult, WorkerStatus, emit_audit


class DeterministicWorkerAdapter:
    """A zero-network, zero-spend adapter for contract and orchestration tests."""

    adapter_id = "deterministic-test-worker"

    def execute(
        self,
        mission: WorkerMission,
        *,
        audit_sink: AuditSink | None = None,
    ) -> WorkerResult:
        emit_audit(
            audit_sink,
            "worker.started",
            {
                "adapter_id": self.adapter_id,
                "mission_id": mission.mission_id,
                "project": mission.project,
                "spend_ceiling": mission.spend_ceiling,
                "timeout_seconds": mission.timeout_seconds,
            },
        )

        if mission.spend_ceiling != 0:
            result = WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.BLOCKED,
                unresolved_failures=("Deterministic worker requires zero spend.",),
                next_action="Set spend_ceiling to 0 or use an explicitly authorised adapter.",
            )
        else:
            result = WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.TESTED,
                changes=("No external changes; deterministic contract exercised.",),
                tests_executed=("worker-contract-smoke",),
                evidence=("deterministic-test-worker",),
                next_action="Run independent Sigma verification before any VERIFIED claim.",
            )

        emit_audit(
            audit_sink,
            "worker.finished",
            {
                "adapter_id": self.adapter_id,
                "mission_id": mission.mission_id,
                "status": result.status.value,
            },
        )
        return result
