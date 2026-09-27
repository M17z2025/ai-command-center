#!/usr/bin/env python3
"""Probe the configured private inference endpoint without exposing credentials."""

from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


def main() -> int:
    endpoint = os.getenv("SIGMA_LLM_ENDPOINT", "").strip()
    model = os.getenv("SIGMA_LLM_MODEL", "").strip()
    protocol = os.getenv("SIGMA_LLM_PROTOCOL", "chat-completions")
    if not endpoint or not model:
        raise SystemExit("SIGMA_LLM_ENDPOINT and SIGMA_LLM_MODEL are required")
    if protocol != "chat-completions":
        raise SystemExit("probe currently requires chat-completions protocol")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with exactly SIGMA_INFERENCE_OK"},
            {"role": "user", "content": "health check"},
        ],
        "temperature": 0,
    }
    headers = {"Content-Type": "application/json"}
    key = os.getenv("SIGMA_LLM_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(
        req,
        timeout=int(os.getenv("SIGMA_LLM_TIMEOUT_SECONDS", "120")),
    ) as response:
        data = json.loads(response.read().decode("utf-8"))
    choices = data.get("choices") or []
    text = ""
    if choices:
        text = str((choices[0].get("message") or {}).get("content") or "")
    if "SIGMA_INFERENCE_OK" not in text:
        raise SystemExit("Inference endpoint responded but failed deterministic probe")
    print(json.dumps({"status": "ok", "model": model, "protocol": protocol}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
