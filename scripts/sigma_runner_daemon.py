#!/usr/bin/env python3
"""Always-on Sigma portfolio runner loop."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sigma_runtime import MeshConfig, MissionRouter, MissionStore, SigmaOrchestrator
from sigma_runtime.portfolio_runner import runner_from_env
from sigma_runtime.provider import provider_from_env
from sigma_runtime.memory import memory_from_env


def main() -> int:
    interval = max(60, int(os.getenv("SIGMA_RUNNER_INTERVAL_SECONDS", "60")))
    execute = os.getenv("SIGMA_RUNNER_EXECUTE", "0") == "1"
    db = os.getenv("SIGMA_RUNTIME_DB", "/data/sigma-runtime.db")
    root = Path(os.getenv("SIGMA_REPO_ROOT", ".")).resolve()

    config = MeshConfig(root)
    mission_store = MissionStore(db)
    router = MissionRouter(config)
    provider = provider_from_env()
    memory = memory_from_env()
    orchestrator = SigmaOrchestrator(config, router, provider, mission_store, memory)
    runner = runner_from_env(
        orchestrator,
        db,
        registry_path=root / "projects/registry.yaml",
    )

    stopping = False

    def stop(*_args):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    while not stopping:
        started = time.monotonic()
        try:
            result = runner.cycle(trigger="scheduled", execute=execute)
            print(
                f"Sigma runner cycle {result.get('cycle_id')} "
                f"state={result.get('state')}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"Sigma runner cycle error: {type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )

        remaining = max(0.0, interval - (time.monotonic() - started))
        deadline = time.monotonic() + remaining
        while not stopping and time.monotonic() < deadline:
            time.sleep(min(5.0, deadline - time.monotonic()))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
