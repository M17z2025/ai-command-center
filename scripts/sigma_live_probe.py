#!/usr/bin/env python3
"""Commissioning probe for a real Sigma mesh runtime service."""

from __future__ import annotations

import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url: str, token: str, method: str = "GET", payload=None):
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=180) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Connection failed: {exc.reason}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description="Probe a commissioned Sigma mesh runtime")
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    parser.add_argument("--prompt")
    parser.add_argument("--read", dest="mission_id")
    args = parser.parse_args(argv)

    token = os.getenv("SIGMA_RUNTIME_TOKEN")
    if not token:
        raise SystemExit("SIGMA_RUNTIME_TOKEN is required")

    base = args.url.rstrip("/")
    if args.mission_id:
        _, mission = request_json(f"{base}/missions/{args.mission_id}", token)
        print(json.dumps(mission, indent=2))
        return 0 if mission.get("id") == args.mission_id else 1

    if not args.prompt:
        raise SystemExit("--prompt or --read is required")

    _, health = request_json(f"{base}/health", token)
    if health.get("status") != "ok":
        raise SystemExit("Sigma health check failed")

    status, mission = request_json(
        f"{base}/missions",
        token,
        "POST",
        {
            "prompt": args.prompt,
            "requested_by": "commissioning-probe",
            "max_cycles": 2,
            "evidence": [
                {
                    "id": "commissioning-probe",
                    "source": "operator",
                    "content": "Real-provider commissioning test; no external factual claim is established by this evidence.",
                }
            ],
        },
    )
    if status != 201:
        raise SystemExit(f"Unexpected create status: {status}")

    mission_id = mission.get("id")
    if not mission_id or mission.get("status") not in {
        "COMPLETE",
        "COMPLETE_WITH_UNVERIFIED_ITEMS",
    }:
        print(json.dumps(mission, indent=2))
        raise SystemExit("Mission did not reach a successful terminal state")

    _, persisted = request_json(f"{base}/missions/{mission_id}", token)
    required = {
        "expert-routing",
        "team-formation",
        "adversarial-critique",
        "evidence-verification",
        "synthesis",
    }
    actual = {event.get("stage") for event in persisted.get("events", [])}
    missing = sorted(required - actual)
    if missing:
        raise SystemExit("Missing persisted stages: " + ", ".join(missing))

    print(
        json.dumps(
            {
                "mission_id": mission_id,
                "status": persisted.get("status"),
                "domains": persisted.get("plan", {}).get("domains", []),
                "leaders": persisted.get("plan", {}).get("leaders", []),
                "thinkers": persisted.get("plan", {}).get("thinkers", []),
                "stages": sorted(actual),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
