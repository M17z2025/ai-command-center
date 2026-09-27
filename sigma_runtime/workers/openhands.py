"""Opt-in OpenHands software-engineering worker.

This adapter deliberately does not import or launch OpenHands unless a caller
explicitly supplies a sandboxed runner. Sigma owns policy, scoping and final
verification; OpenHands is only an execution worker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .base import AuditSink, WorkerMission, WorkerResult, WorkerStatus, emit_audit


OpenHandsRunner = Callable[[WorkerMission], WorkerResult]


@dataclass(frozen=True)
class OpenHandsWorkerConfig:
    enabled: bool = False
    require_zero_spend: bool = True
    require_sandbox: bool = True


class OpenHandsWorkerAdapter:
    adapter_id = "openhands-software-engineering-worker"

    def __init__(
        self,
        *,
        runner: OpenHandsRunner | None = None,
        config: OpenHandsWorkerConfig | None = None,
    ) -> None:
        self.runner = runner
        self.config = config or OpenHandsWorkerConfig()

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
                "enabled": self.config.enabled,
            },
        )

        blocked_reason = self._blocked_reason(mission)
        if blocked_reason:
            result = WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.BLOCKED,
                unresolved_failures=(blocked_reason,),
                next_action="Satisfy the Sigma worker gate before invoking OpenHands.",
                metadata={"adapter_id": self.adapter_id},
            )
        else:
            assert self.runner is not None
            result = self.runner(mission)
            if result.mission_id != mission.mission_id:
                raise ValueError("OpenHands runner returned a mismatched mission_id")

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

    def _blocked_reason(self, mission: WorkerMission) -> str | None:
        if not self.config.enabled:
            return "OpenHands worker is disabled by default."
        if self.runner is None:
            return "No sandboxed OpenHands runner is configured."
        if self.config.require_zero_spend and mission.spend_ceiling != 0:
            return "OpenHands proof adapter requires zero authorised spend."
        if self.config.require_sandbox and not mission.capabilities.permits("sandbox_execution"):
            return "OpenHands requires explicit sandbox_execution capability."
        if mission.capabilities.permits("production_release"):
            return "OpenHands proof adapter cannot receive production_release capability."
        if mission.credential_scope:
            return "OpenHands proof adapter does not accept credentials during proof phase."
        if not mission.filesystem_scope:
            return "OpenHands requires an explicit filesystem scope."
        return None
