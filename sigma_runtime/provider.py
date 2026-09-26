"""Model-provider adapters for Sigma runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


@dataclass
class CompletionRequest:
    kind: str
    system: str
    user: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider:
    def complete(self, request: CompletionRequest) -> str:
        raise NotImplementedError


class HTTPModelProvider(ModelProvider):
    """Vendor-neutral HTTP adapter supporting Responses or chat-completions shapes."""

    def __init__(
        self,
        endpoint: str,
        model: str,
        api_key: str | None = None,
        protocol: str = "responses",
        timeout: int = 120,
    ) -> None:
        if protocol not in {"responses", "chat-completions"}:
            raise ProviderError("SIGMA_LLM_PROTOCOL must be responses or chat-completions")
        if not endpoint.startswith(("https://", "http://")):
            raise ProviderError("SIGMA_LLM_ENDPOINT must be an absolute HTTP(S) URL")
        if not model:
            raise ProviderError("SIGMA_LLM_MODEL is required")
        self.endpoint = endpoint
        self.model = model
        self.api_key = api_key
        self.protocol = protocol
        self.timeout = timeout

    def complete(self, request: CompletionRequest) -> str:
        if self.protocol == "responses":
            payload = {
                "model": self.model,
                "input": [
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
            }
        else:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user},
                ],
                "temperature": 0.2,
            }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "sigma-expert-mesh-runtime/1",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ProviderError(f"Model endpoint HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Model endpoint failed: {exc}") from exc

        text = self._extract_text(data)
        if not text.strip():
            raise ProviderError("Model endpoint returned no text")
        return text.strip()

    def _extract_text(self, data: dict[str, Any]) -> str:
        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                return content
        output = data.get("output")
        if isinstance(output, list):
            chunks: list[str] = []
            for item in output:
                for content in item.get("content", []) if isinstance(item, dict) else []:
                    if isinstance(content, dict):
                        value = content.get("text")
                        if isinstance(value, str):
                            chunks.append(value)
            if chunks:
                return "\n".join(chunks)
        raise ProviderError("Unrecognized model response shape")


class DeterministicTestProvider(ModelProvider):
    """Non-intelligent provider used only for deterministic CI/runtime smoke tests."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.critic_calls = 0

    def complete(self, request: CompletionRequest) -> str:
        self.calls.append(request.kind)
        if request.kind == "analysis":
            domain = request.metadata.get("domain", "unknown")
            return (
                f"EXPERT ANALYSIS [{domain}]\n"
                "Assumptions are explicit. The proposal is bounded and testable. "
                "Evidence supplied with the mission should be preferred over unsupported claims."
            )
        if request.kind == "critic":
            self.critic_calls += 1
            if self.critic_calls == 1:
                return "VERDICT: REPAIR\nFINDINGS: tighten assumptions and preserve uncertainty."
            return "VERDICT: PASS\nFINDINGS: repaired analysis is internally coherent."
        if request.kind == "verifier":
            return "VERDICT: PASS\nEVIDENCE: test provider confirms evidence-handling path only."
        if request.kind == "development-plan":
            return (
                "SIGMA DEVELOPMENT ADVISORY PLAN\n"
                "Objective, specialist recommendations, architecture, legal/security/commercial implications, "
                "delivery phases, ordered pull plan, acceptance criteria, evidence requirements and exact next actions."
            )
        if request.kind == "synthesis":
            return (
                "SIGMA FINAL SYNTHESIS\n"
                "Multiple expert analyses were routed, challenged, verified and synthesized. "
                "This deterministic result proves orchestration, not subject-matter intelligence."
            )
        if request.kind == "postmortem":
            return "LESSON: preserve explicit assumptions and independent verification in future missions."
        if request.kind == "repair":
            return "REPAIRED ANALYSIS\nAssumptions and uncertainty are now explicit."
        return f"TEST RESPONSE [{request.kind}]"


def provider_from_env(*, allow_test: bool = False) -> ModelProvider:
    provider = os.getenv("SIGMA_RUNTIME_PROVIDER", "http").strip().lower()
    if provider == "test":
        if not allow_test and os.getenv("SIGMA_ALLOW_TEST_PROVIDER") != "1":
            raise ProviderError("Test provider is disabled outside explicit smoke/test mode")
        return DeterministicTestProvider()
    if provider != "http":
        raise ProviderError(f"Unsupported SIGMA_RUNTIME_PROVIDER: {provider}")

    endpoint = os.getenv("SIGMA_LLM_ENDPOINT", "").strip()
    model = os.getenv("SIGMA_LLM_MODEL", "").strip()
    if not endpoint or not model:
        raise ProviderError(
            "Live runtime requires SIGMA_LLM_ENDPOINT and SIGMA_LLM_MODEL. "
            "SIGMA_LLM_API_KEY is optional for authenticated/self-hosted endpoints."
        )
    return HTTPModelProvider(
        endpoint=endpoint,
        model=model,
        api_key=os.getenv("SIGMA_LLM_API_KEY") or None,
        protocol=os.getenv("SIGMA_LLM_PROTOCOL", "responses"),
        timeout=int(os.getenv("SIGMA_LLM_TIMEOUT_SECONDS", "120")),
    )
