#!/usr/bin/env python3
"""CLI and HTTP entrypoint for the operational Sigma expert mesh."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sigma_runtime import MeshConfig, MissionRouter, MissionStore, SigmaOrchestrator
from sigma_runtime.provider import provider_from_env
from sigma_runtime.server import build_server


def build_components(args, *, allow_test=False):
    config = MeshConfig(args.root)
    store = MissionStore(args.db)
    router = MissionRouter(config)
    provider = provider_from_env(allow_test=allow_test)
    orchestrator = SigmaOrchestrator(config, router, provider, store)
    return config, store, router, orchestrator


def load_evidence(paths: list[str]) -> list[dict]:
    evidence = []
    for raw in paths:
        path = Path(raw)
        text = path.read_text(encoding="utf-8")
        evidence.append({"id": path.name, "source": str(path), "content": text[:50000]})
    return evidence


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sigma operational expert-mesh runtime")
    parser.add_argument("--root", default=".")
    parser.add_argument("--db", default=os.getenv("SIGMA_RUNTIME_DB", "runtime-data/sigma-runtime.db"))
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan")
    plan_p.add_argument("prompt")

    run_p = sub.add_parser("run")
    run_p.add_argument("prompt")
    run_p.add_argument("--evidence-file", action="append", default=[])
    run_p.add_argument("--max-cycles", type=int, default=2)
    run_p.add_argument("--requested-by", default="owner")

    sub.add_parser("missions")
    mission_p = sub.add_parser("mission")
    mission_p.add_argument("mission_id")
    sub.add_parser("lessons")

    serve_p = sub.add_parser("serve")
    serve_p.add_argument("--host", default=os.getenv("SIGMA_RUNTIME_HOST", "127.0.0.1"))
    serve_p.add_argument("--port", type=int, default=int(os.getenv("PORT", os.getenv("SIGMA_RUNTIME_PORT", "8080"))))

    sub.add_parser("smoke")

    args = parser.parse_args(argv)
    config = MeshConfig(args.root)
    store = MissionStore(args.db)
    router = MissionRouter(config)

    if args.command == "plan":
        print(json.dumps(router.route(args.prompt).to_dict(), indent=2))
        return 0
    if args.command == "missions":
        print(json.dumps(store.list_missions(), indent=2))
        return 0
    if args.command == "mission":
        mission = store.get_mission(args.mission_id)
        if not mission:
            print("mission not found", file=sys.stderr)
            return 2
        print(json.dumps(mission, indent=2))
        return 0
    if args.command == "lessons":
        print(json.dumps(store.list_lessons(), indent=2))
        return 0

    allow_test = args.command == "smoke"
    provider = provider_from_env(allow_test=allow_test)
    orchestrator = SigmaOrchestrator(config, router, provider, store)

    if args.command == "run":
        result = orchestrator.run(
            args.prompt,
            evidence=load_evidence(args.evidence_file),
            requested_by=args.requested_by,
            max_cycles=args.max_cycles,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "smoke":
        result = orchestrator.run(
            "Design a secure AI software service with evidence verification.",
            evidence=[{"id": "smoke", "source": "ci", "content": "deterministic smoke evidence"}],
            requested_by="ci",
            max_cycles=2,
        )
        if result.get("status") != "COMPLETE":
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1
        print(json.dumps({"mission_id": result["id"], "status": result["status"]}, indent=2))
        return 0

    if args.command == "serve":
        token = os.getenv("SIGMA_RUNTIME_TOKEN") or None
        server = build_server(args.host, args.port, orchestrator, config, store, token)
        print(f"Sigma mesh runtime listening on http://{args.host}:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
