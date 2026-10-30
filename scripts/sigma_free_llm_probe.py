#!/usr/bin/env python3
"""Optional live synthetic probe of the free-tier router (no business data)."""

from __future__ import annotations

import json
import os

from sigma_runtime.free_tier import FreeTierModelProvider
from sigma_runtime.provider import CompletionRequest, ProviderError, provider_from_env


def main() -> int:
    if os.getenv("SIGMA_FREE_LLM_ENABLED") != "1":
        raise SystemExit("Set SIGMA_FREE_LLM_ENABLED=1 for a live free-tier probe")
    if os.getenv("SIGMA_FREE_LLM_ALLOW_PRIMARY_FALLBACK", "0") == "1":
        raise SystemExit("Disable primary fallback before verifying a free-tier endpoint")
    try:
        provider = provider_from_env()
        if not isinstance(provider, FreeTierModelProvider):
            raise ProviderError("Free-tier router did not initialise")
        answer = provider.complete(
            CompletionRequest(
                kind="analysis",
                system="You are a connectivity test. Respond with exactly SIGMA_FREE_LLM_OK.",
                user="Public synthetic connectivity check only.",
                metadata={"data_classification": "public", "allow_free_tier": True},
            )
        )
    except ProviderError as exc:
        # Avoid exposing model endpoint response bodies or credentials.
        raise SystemExit("Free-tier inference probe failed; inspect restricted host logs") from None
    if "SIGMA_FREE_LLM_OK" not in answer:
        raise SystemExit("Free-tier inference probe returned an unexpected response")
    print(json.dumps({"status": "ok", "route": "free-tier", "payload": "synthetic-public"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
