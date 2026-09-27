"""Core contract for bounded third-party or native Sigma workers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Protocol, Sequence


class WorkerStatus(str, Enum):
    """States a worker may report.

    VERIFIED and RELEASED are intentionally absent: only Sigma's independent
    gates may issue those states.
    """

    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    CHANGED = "CHANGED"
    TESTED = "TESTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CapabilityPolicy:
    """Explicit least-privilege capability boundary for one worker mission."""

    allow: frozenset[str] = field(default_factory=frozenset)
    deny: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        overlap = self.allow.intersection(self.deny)
        if overlap:
            raise ValueError(
                "Capabilities cannot be both allowed and denied: "
                + ", ".join(sorted(overlap))
            )

    def permits(self, capability: str) -> bool:
        return capability in self.allow and capability not in self.deny

    def require(self, capability: str) -> None:
        if not self.permits(capability):
            raise PermissionError(f"Worker capability not permitted: {capability}")


@dataclass(frozen=True)
class WorkerMission:
    mission_id: str
    parent_agent: str
    project: str
    objective: str
    acceptance_criteria: tuple[str, ...]
    capabilities: CapabilityPolicy
    filesystem_scope: tuple[str, ...] = ()
    network_scope: tuple[str, ...] = ()
    credential_scope: tuple[str, ...] = ()
    model_provider: str = ""
    model_name: str = ""
    spend_ceiling: float = 0.0
    timeout_seconds: int = 900
    data_classification: str = "internal"
    prohibited_actions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    termination_conditions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.mission_id.strip():
            raise ValueError("mission_id is required")
        if not self.parent_agent.strip():
            raise ValueError("parent_agent is required")
        if not self.project.strip():
            raise ValueError("project is required")
        if not self.objective.strip():
            raise ValueError("objective is required")
        if self.spend_ceiling < 0:
            raise ValueError("spend_ceiling cannot be negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class WorkerResult:
    mission_id: str
    status: WorkerStatus
    changes: tuple[str, ...] = ()
    commands_executed: tuple[str, ...] = ()
    tests_executed: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    unresolved_failures: tuple[str, ...] = ()
    security_sensitive_actions: tuple[str, ...] = ()
    next_action: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)


AuditSink = Callable[[str, Mapping[str, object]], None]


class WorkerAdapter(Protocol):
    """Protocol implemented by all bounded execution workers."""

    adapter_id: str

    def execute(
        self,
        mission: WorkerMission,
        *,
        audit_sink: AuditSink | None = None,
    ) -> WorkerResult:
        """Execute a mission without exceeding its declared capability boundary."""
        ...


def emit_audit(
    audit_sink: AuditSink | None,
    event: str,
    payload: Mapping[str, object],
) -> None:
    if audit_sink is not None:
        audit_sink(event, payload)


def normalize_sequence(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(value for value in values if value)
