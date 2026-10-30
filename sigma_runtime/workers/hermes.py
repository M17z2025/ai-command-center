"""Hermes Agent as a bounded, opt-in Sigma research/execution candidate worker.

Hermes is NEVER an independent evidence, security or release authority.
This adapter requires a separately isolated Hermes deployment; textual
instructions do not substitute for sandbox enforcement on its host.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .base import AuditSink, WorkerMission, WorkerResult, WorkerStatus, emit_audit


@dataclass(frozen=True)
class HermesWorkerConfig:
    endpoint: str = ""
    api_key: str = ""
    enabled: bool = False
    sandbox_verified: bool = False
    poll_seconds: float = 2.0

    def __post_init__(self):
        if not self.enabled:
            return
        parsed = urlsplit(self.endpoint)
        if (parsed.scheme != "https" and
                not (parsed.scheme == "http" and parsed.hostname in
                     {"localhost", "127.0.0.1", "hermes"})):
            raise ValueError("Hermes must use HTTPS or a trusted loopback/container endpoint")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Hermes URL cannot contain credentials, query or fragment")
        if parsed.path.rstrip("/") not in ("", "/v1"):
            raise ValueError("Hermes URL must be a server root or /v1")
        if len(self.api_key) < 8:
            raise ValueError("Hermes API bearer token is required")
        if self.poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")


class HermesWorkerAdapter:
    """Dispatch to Hermes Runs API, treating its output as UNVERIFIED candidate work."""

    adapter_id = "hermes-governed-worker"

    def __init__(self, config: HermesWorkerConfig | None = None):
        self.config = config or HermesWorkerConfig()

    def _request(self, method: str, path: str, body: dict | None = None, *,
                 idempotency: str | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if idempotency:
            headers["Idempotency-Key"] = idempotency
        request = Request(
            self.config.endpoint.rstrip("/").removesuffix("/v1") + path,
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not isinstance(result, dict):
                raise ValueError("Invalid Hermes response shape")
            return result
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            # Avoid echoing upstream response bodies (they may contain private data).
            raise RuntimeError("Hermes request failed or returned invalid JSON") from exc

    def execute(self, mission: WorkerMission, *, audit_sink: AuditSink | None = None) -> WorkerResult:
        cfg = self.config
        reason = None
        if not cfg.enabled:
            reason = "Hermes worker is disabled."
        elif not cfg.sandbox_verified:
            reason = "Hermes sandbox isolation has not been independently verified."
        elif not mission.capabilities.permits("sandbox_execution"):
            reason = "Explicit sandbox_execution capability is required."
        elif not mission.filesystem_scope:
            reason = "An explicit filesystem scope is required."
        elif mission.credential_scope:
            reason = "Hermes proof worker cannot receive credentials."
        elif mission.capabilities.permits("production_release"):
            reason = "Hermes worker cannot exercise production_release."
        elif mission.spend_ceiling != 0:
            reason = "Hermes pilot requires zero authorised spend."
        if reason:
            return WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.BLOCKED,
                unresolved_failures=(reason,),
                next_action="Confirm isolation, credentials and the Sigma capability gate.",
                metadata={"adapter_id": self.adapter_id},
            )

        emit_audit(audit_sink, "worker.started",
                   {"adapter_id": self.adapter_id, "mission_id": mission.mission_id})
        prompt = (
            "You are a subordinate Sigma worker in a sandbox. Do not deploy, publish, "
            "send messages, access secrets, spend money or claim independent verification. "
            "All outputs are candidates subject to Sigma's own tests and review. "
            f"Project: {mission.project}\nObjective: {mission.objective}\n"
            f"Acceptance criteria: {json.dumps(mission.acceptance_criteria)}\n"
            f"Filesystem scope: {json.dumps(mission.filesystem_scope)}\n"
            f"Forbidden actions: {json.dumps(mission.prohibited_actions)}"
        )
        try:
            run = self._request(
                "POST", "/v1/runs",
                {"input": prompt, "session_id": f"sigma-{mission.mission_id}"},
                idempotency=f"sigma-{mission.mission_id}",
            )
            run_id = run.get("run_id")
            if not isinstance(run_id, str) or not run_id or len(run_id) > 180:
                raise RuntimeError("Hermes did not return a valid run_id")
            deadline = time.monotonic() + min(mission.timeout_seconds, 900)
            while True:
                state = self._request("GET", f"/v1/runs/{quote(run_id, safe='')}")
                status = state.get("status")
                if status in ("completed", "failed", "cancelled", "canceled", "incomplete"):
                    break
                if status not in ("started", "running", "queued", "pending", "waiting"):
                    raise RuntimeError("Hermes returned an unknown run status")
                if time.monotonic() >= deadline:
                    raise TimeoutError("Hermes execution exceeded bounded timeout")
                time.sleep(min(cfg.poll_seconds, max(0.01, deadline - time.monotonic())))
            if status != "completed":
                raise RuntimeError("Hermes run did not complete successfully")
            output = state.get("output")
            if not isinstance(output, str) or not output.strip():
                raise RuntimeError("Hermes run completed without usable output")
            # A model response is not proof of changed code, tests or delivery.
            result = WorkerResult(
                mission_id=mission.mission_id,
                status=WorkerStatus.PLANNED,
                evidence=(f"hermes_run_id:{run_id}",),
                next_action="Independently verify changes, PR head, CI and security before promotion.",
                metadata={"adapter_id": self.adapter_id, "run_id": run_id,
                          "candidate_summary": output[:2000]},
            )
        except (RuntimeError, TimeoutError) as exc:
            result = WorkerResult(
                mission_id=mission.mission_id, status=WorkerStatus.BLOCKED,
                unresolved_failures=(str(exc),),
                next_action="Inspect the private Hermes gateway and independent execution evidence.",
                metadata={"adapter_id": self.adapter_id},
            )
        emit_audit(audit_sink, "worker.finished", {
            "adapter_id": self.adapter_id, "mission_id": mission.mission_id,
            "status": result.status.value,
        })
        return result
