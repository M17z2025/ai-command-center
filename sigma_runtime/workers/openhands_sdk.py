"""Sandboxed OpenHands SDK runner for the Sigma proof phase.

The OpenHands dependency is imported lazily so Sigma's base runtime remains
dependency-light. Commissioning requires an explicitly pinned agent-server
image and an approved local/private OpenAI-compatible model endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
from urllib.parse import urlparse

from .base import WorkerMission, WorkerResult, WorkerStatus


_PRIVATE_HOST_SUFFIXES = (".internal", ".local")


@dataclass(frozen=True)
class OpenHandsSDKRunnerConfig:
    model: str
    base_url: str
    server_image: str
    api_key: str = "local"
    platform_name: str | None = None

    def validate(self) -> None:
        if not self.model.strip():
            raise ValueError("OpenHands model is required")
        if not self.base_url.strip():
            raise ValueError("OpenHands base_url is required")
        if not self.server_image.strip():
            raise ValueError("A pinned OpenHands agent-server image is required")
        if ":latest" in self.server_image or self.server_image.endswith(":latest-python"):
            raise ValueError("OpenHands proof runner refuses unpinned latest images")
        if not self._is_private_endpoint(self.base_url):
            raise ValueError(
                "Proof phase requires a loopback/private model endpoint; "
                "public model providers need separate owner authorisation."
            )

    @staticmethod
    def _is_private_endpoint(value: str) -> bool:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = (parsed.hostname or "").lower()
        if host in {"localhost", "127.0.0.1", "::1"}:
            return True
        if host.startswith("10.") or host.startswith("192.168."):
            return True
        if host.endswith(_PRIVATE_HOST_SUFFIXES):
            return True
        if host.startswith("172."):
            parts = host.split(".")
            if len(parts) >= 2 and parts[1].isdigit():
                return 16 <= int(parts[1]) <= 31
        return False

    def docker_platform(self) -> str:
        if self.platform_name:
            return self.platform_name
        machine = platform.machine().lower()
        return "linux/arm64" if ("arm" in machine or "aarch64" in machine) else "linux/amd64"


class OpenHandsSDKRunner:
    """Execute one bounded mission inside OpenHands DockerWorkspace."""

    def __init__(self, config: OpenHandsSDKRunnerConfig) -> None:
        config.validate()
        self.config = config

    def __call__(self, mission: WorkerMission) -> WorkerResult:
        if len(mission.filesystem_scope) != 1:
            return self._blocked(mission, "Proof runner requires exactly one filesystem scope.")

        host_workspace = Path(mission.filesystem_scope[0]).expanduser().resolve()
        if not host_workspace.exists() or not host_workspace.is_dir():
            return self._blocked(mission, "Filesystem scope must be an existing directory.")
        if ":" in str(host_workspace):
            return self._blocked(mission, "Filesystem scope contains an unsupported ':' character.")

        try:
            from pydantic import SecretStr
            from openhands.sdk import LLM, Conversation
            from openhands.tools.preset.default import get_default_agent
            from openhands.workspace import DockerWorkspace
        except ImportError:
            return self._blocked(
                mission,
                "OpenHands SDK dependencies are not installed in this runtime.",
            )

        llm = LLM(
            usage_id=f"sigma:{mission.mission_id}",
            model=self.config.model,
            base_url=self.config.base_url,
            api_key=SecretStr(self.config.api_key),
        )
        agent = get_default_agent(llm=llm, cli_mode=True)

        prompt = self._mission_prompt(mission)
        events: list[str] = []

        def callback(event) -> None:
            events.append(type(event).__name__)

        try:
            with DockerWorkspace(
                server_image=self.config.server_image,
                platform=self.config.docker_platform(),
                volumes=[f"{host_workspace}:/workspace"],
                working_dir="/workspace",
                extra_ports=False,
                enable_gpu=False,
            ) as workspace:
                conversation = Conversation(
                    agent=agent,
                    workspace=workspace,
                    callbacks=[callback],
                )
                try:
                    conversation.send_message(prompt)
                    conversation.run()
                    execution_status = str(conversation.state.execution_status)
                    try:
                        cost = float(
                            conversation.conversation_stats
                            .get_combined_metrics()
                            .accumulated_cost
                            or 0
                        )
                    except Exception:
                        cost = 0.0
                finally:
                    conversation.close()
        except Exception as exc:
            return WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.BLOCKED,
                unresolved_failures=(f"OpenHands execution failed: {type(exc).__name__}",),
                evidence=(f"events={len(events)}",),
                next_action="Inspect sandbox logs; do not claim the mission verified.",
                metadata={"adapter": "openhands-sdk"},
            )

        if cost > mission.spend_ceiling:
            return WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.BLOCKED,
                unresolved_failures=(
                    f"Reported model cost {cost} exceeded authorised ceiling "
                    f"{mission.spend_ceiling}.",
                ),
                evidence=(f"openhands_status={execution_status}", f"events={len(events)}"),
                next_action="Stop worker use and review inference configuration.",
                metadata={"adapter": "openhands-sdk", "model_cost": str(cost)},
            )

        return WorkerResult(
            mission_id=mission.mission_id,
            status=WorkerStatus.CHANGED,
            changes=("OpenHands completed a bounded sandbox execution.",),
            evidence=(f"openhands_status={execution_status}", f"events={len(events)}"),
            next_action=(
                "Sigma must independently inspect the diff and run declared build/tests "
                "before promoting this result to TESTED."
            ),
            metadata={"adapter": "openhands-sdk", "model_cost": str(cost)},
        )

    @staticmethod
    def _blocked(mission: WorkerMission, reason: str) -> WorkerResult:
        return WorkerResult(
            mission_id=mission.mission_id,
            status=WorkerStatus.BLOCKED,
            unresolved_failures=(reason,),
            next_action="Satisfy the proof-runner precondition and retry.",
            metadata={"adapter": "openhands-sdk"},
        )

    @staticmethod
    def _mission_prompt(mission: WorkerMission) -> str:
        criteria = "\n".join(f"- {item}" for item in mission.acceptance_criteria)
        prohibited = "\n".join(f"- {item}" for item in mission.prohibited_actions) or "- none"
        return (
            "You are an execution worker under Sigma authority. Do not broaden scope.\n\n"
            f"Mission: {mission.objective}\n\n"
            f"Acceptance criteria:\n{criteria}\n\n"
            f"Prohibited actions:\n{prohibited}\n\n"
            "Work only inside /workspace. Make the minimum necessary code changes. "
            "Run relevant local tests when possible. Do not deploy, manage secrets, "
            "purchase services, or claim VERIFIED/RELEASED. Leave the workspace in "
            "an inspectable state and report unresolved failures."
        )
