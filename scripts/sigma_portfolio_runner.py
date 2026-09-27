#!/usr/bin/env python3
"""CLI for the Sigma autonomous portfolio runner."""

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
from sigma_runtime.portfolio_runner import runner_from_env
from sigma_runtime.provider import provider_from_env


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Sigma autonomous portfolio runner")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--db",
        default=os.getenv("SIGMA_RUNTIME_DB", "runtime-data/sigma-runtime.db"),
    )
    parser.add_argument("--registry", default="projects/registry.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    cycle = sub.add_parser("cycle")
    cycle.add_argument("--trigger", default="manual")
    cycle.add_argument("--execute", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args(argv)

    config = MeshConfig(args.root)
    mission_store = MissionStore(args.db)
    router = MissionRouter(config)

    if args.command == "status":
        from sigma_runtime.portfolio_runner import RunnerStore
        print(json.dumps({"cycles": RunnerStore(args.db).list()}, indent=2))
        return 0

    provider = provider_from_env()
    orchestrator = SigmaOrchestrator(config, router, provider, mission_store)
    runner = runner_from_env(orchestrator, args.db, registry_path=args.registry)
    result = runner.cycle(trigger=args.trigger, execute=args.execute)
    print(json.dumps(result, indent=2))
    return 0 if result.get("state") not in {"BLOCKED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
