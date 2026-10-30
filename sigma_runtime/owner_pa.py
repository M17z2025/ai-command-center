"""Owner-personal-assistant interface for the existing Sigma Mesh.

Mitz PA is NOT a second agent runtime. This adapter uses Sigma's existing
orchestrator and audit store, and never pretends advisory output is a completed
external action. Live actions require separately commissioned secure connectors.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


MAX_OWNER_PROMPT_CHARS = 3000


class MissionOrchestrator(Protocol):
    def run(
        self, prompt: str, *, evidence: list[dict[str, Any]] | None = None,
        requested_by: str = "owner", max_cycles: int = 2,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class OwnerAssistantOutcome:
    mission_id: str
    advisory_status: str
    summary: str
    action_executed: bool
    external_action_status: str
    interface: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "advisory_status": self.advisory_status,
            "summary": self.summary,
            "action_executed": self.action_executed,
            "external_action_status": self.external_action_status,
            "interface": self.interface,
            "source": self.source,
        }


class SigmaMitzPA:
    """The Mitz PA role inside Sigma; no other process, model or database."""

    def __init__(self, orchestrator: MissionOrchestrator):
        self.orchestrator = orchestrator

    def advise(self, prompt: str) -> OwnerAssistantOutcome:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A non-empty assistant request is required")
        if len(prompt) > MAX_OWNER_PROMPT_CHARS:
            raise ValueError("Assistant request exceeds the bounded input size")

        # The caller cannot forge the owner audit identity, inject external
        # evidence or skip an independent action-approval process.
        result = self.orchestrator.run(
            prompt.strip(), evidence=[], requested_by="mitz-pa-owner",
            max_cycles=0,
        )
        if not isinstance(result, dict):
            raise RuntimeError("Sigma mission returned no durable result")
        mission_id = result.get("id") or result.get("mission_id")
        if not isinstance(mission_id, str) or not mission_id:
            raise RuntimeError("Sigma mission lacks a durable identifier")
        summary = result.get("final_output")
        if not isinstance(summary, str):
            summary = ""
        state = result.get("status")
        return OwnerAssistantOutcome(
            mission_id=mission_id,
            advisory_status=state if isinstance(state, str) else "UNKNOWN",
            summary=summary[:12000],
            action_executed=False,
            external_action_status="NOT_EXECUTED",
            interface="sigma-mitz-pa",
            source="M17z2025/ai-command-center",
        )
