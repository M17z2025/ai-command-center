"""Opt-in, conservative routing to reviewed free-tier OpenAI-compatible APIs.

The upstream awesome-freellm-apis project is a discovery directory, not an
inference service. This adapter never fetches or executes its remote data.
Quota limits here are per process, not provider/account-wide guarantees.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import json
import os
import re
from threading import Lock
from time import monotonic
from urllib.parse import urlsplit

from .provider import CompletionRequest, HTTPModelProvider, ModelProvider, ProviderError


# Each endpoint must be deliberately reviewed before it is admitted.
ALLOWED_HOSTS = frozenset({
    "api.groq.com",
    "api.cerebras.ai",
    "integrate.api.nvidia.com",
    "openrouter.ai",
})
ALLOWED_KINDS = frozenset({"analysis", "postmortem"})


@dataclass
class _Route:
    name: str
    provider: HTTPModelProvider
    per_minute: int
    per_day: int
    minute_calls: deque[float] = field(default_factory=deque)
    day_calls: deque[float] = field(default_factory=deque)
    cooldown_until: float = 0.0


class FreeTierModelProvider(ModelProvider):
    """Send explicitly public, low-risk tasks to approved free-tier providers.

    Everything else goes to the configured primary provider. If a qualifying
    task exhausts its free-tier routes, use primary ONLY with explicit opt-in.
    """

    def __init__(
        self,
        primary: ModelProvider,
        routes: list[_Route],
        *,
        allow_primary_fallback: bool = False,
        clock=monotonic,
    ) -> None:
        if not routes:
            raise ProviderError("Enabled free-tier routing requires at least one route")
        self.primary = primary
        self.routes = routes
        self.allow_primary_fallback = allow_primary_fallback
        self.clock = clock
        self._lock = Lock()

    def _reserve(self, route: _Route) -> bool:
        with self._lock:
            now = self.clock()
            while route.minute_calls and route.minute_calls[0] <= now - 60:
                route.minute_calls.popleft()
            while route.day_calls and route.day_calls[0] <= now - 86400:
                route.day_calls.popleft()
            if (
                now < route.cooldown_until
                or len(route.minute_calls) >= route.per_minute
                or len(route.day_calls) >= route.per_day
            ):
                return False
            route.minute_calls.append(now)
            route.day_calls.append(now)
            return True

    def complete(self, request: CompletionRequest) -> str:
        # Never forward unknown, internal, sensitive or unclassified prompts.
        if (
            request.kind not in ALLOWED_KINDS
            or request.metadata.get("data_classification") != "public"
            or request.metadata.get("allow_free_tier") is not True
        ):
            return self.primary.complete(request)

        for route in self.routes:
            if not self._reserve(route):
                continue
            try:
                return route.provider.complete(request)
            except ProviderError:
                # Do not propagate untrusted provider errors or response bodies.
                with self._lock:
                    route.cooldown_until = max(route.cooldown_until, self.clock() + 60)
                continue

        if self.allow_primary_fallback:
            return self.primary.complete(request)
        raise ProviderError(
            "Approved free-tier inference unavailable or quota exhausted; "
            "primary fallback is disabled"
        )


def free_tier_from_env(primary: ModelProvider) -> ModelProvider:
    """Construct a reviewed, capped router only if explicitly enabled."""
    if os.getenv("SIGMA_FREE_LLM_ENABLED", "0") != "1":
        return primary

    try:
        definitions = json.loads(os.getenv("SIGMA_FREE_LLM_ROUTES_JSON", "[]"))
    except json.JSONDecodeError as exc:
        raise ProviderError("Invalid SIGMA_FREE_LLM_ROUTES_JSON") from exc
    if not isinstance(definitions, list) or not 1 <= len(definitions) <= 4:
        raise ProviderError("Free-tier routing requires 1 to 4 approved routes")

    routes: list[_Route] = []
    names: set[str] = set()
    for item in definitions:
        if not isinstance(item, dict):
            raise ProviderError("Each free-tier route must be an object")
        name = item.get("name")
        endpoint = item.get("endpoint")
        model = item.get("model")
        key_env = item.get("key_env")
        if (
            not isinstance(name, str) or not re.fullmatch(r"[a-z0-9_-]{1,32}", name)
            or name in names
            or not isinstance(endpoint, str)
            or not isinstance(model, str) or not model or len(model) > 180
            or not isinstance(key_env, str)
            or not re.fullmatch(r"SIGMA_FREE_LLM_KEY_[A-Z0-9_]{1,40}", key_env)
        ):
            raise ProviderError("Invalid or duplicate free-tier route configuration")
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
            or parsed.path != "/v1/chat/completions"
            or parsed.query or parsed.fragment
        ):
            raise ProviderError("Free-tier endpoint must be an approved HTTPS API")
        key = os.getenv(key_env, "")
        if not key:
            raise ProviderError(f"Required free-tier credential is missing: {key_env}")
        try:
            rpm = int(item.get("max_requests_per_minute", 5))
            rpd = int(item.get("max_requests_per_day", 100))
            timeout = int(item.get("timeout_seconds", 20))
        except (TypeError, ValueError) as exc:
            raise ProviderError("Invalid free-tier limits or timeout") from exc
        if not (1 <= rpm <= 60 and 1 <= rpd <= 1000 and 1 <= timeout <= 60):
            raise ProviderError("Free-tier limits exceed configured safety bounds")
        routes.append(
            _Route(
                name=name,
                provider=HTTPModelProvider(
                    endpoint=endpoint,
                    model=model,
                    api_key=key,
                    protocol="chat-completions",
                    timeout=timeout,
                    max_tokens=512,
                    context_tokens=4096,
                ),
                per_minute=rpm,
                per_day=rpd,
            )
        )
        names.add(name)

    return FreeTierModelProvider(
        primary,
        routes,
        allow_primary_fallback=os.getenv(
            "SIGMA_FREE_LLM_ALLOW_PRIMARY_FALLBACK", "0"
        ) == "1",
    )
