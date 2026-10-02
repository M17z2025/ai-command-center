#!/usr/bin/env python3
"""Run one real, bounded Sigma autonomous engineering proof end-to-end."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import uuid

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sigma_runtime import MeshConfig, MissionRouter, MissionStore, SigmaOrchestrator
from sigma_runtime.delivery_supervisor import DeliverySupervisor
from sigma_runtime.memory import memory_from_env
from sigma_runtime.portfolio_runner import runner_from_env
from sigma_runtime.provider import provider_from_env


def main() -> int:
    repository = os.getenv(
        "SIGMA_PROOF_REPOSITORY",
        "M17z2025/ai-command-center",
    )
    db = os.getenv("SIGMA_RUNTIME_DB", "/data/sigma-runtime.db")
    nonce = uuid.uuid4().hex[:12]

    config = MeshConfig(REPO_ROOT)
    store = MissionStore(db)
    orchestrator = SigmaOrchestrator(
        config,
        MissionRouter(config),
        provider_from_env(),
        store,
        memory_from_env(),
    )
    runner = runner_from_env(
        orchestrator,
        db,
        registry_path=REPO_ROOT / "projects" / "registry.yaml",
    )
    if not runner.github.allow_write:
        raise RuntimeError("SIGMA_RUNNER_ALLOW_WRITE must be enabled for proof")
    if runner.worker is None:
        raise RuntimeError("SIGMA_WORKER_ENDPOINT is required for proof")

    objective = (
        "Complete a bounded Sigma autonomous commissioning proof by creating or "
        "updating runtime-proof/SIGMA_AUTONOMOUS_PROOF.md with a new bullet "
        f"'proof {nonce}'. Preserve existing proof history. Update PROJECT_STATUS.md "
        "with a factual commissioning-proof entry for this nonce. Do not change "
        "runtime code, dependencies, infrastructure, security controls or workflows."
    )
    issue_body = (
        "Acceptance criteria:\n"
        f"- runtime-proof/SIGMA_AUTONOMOUS_PROOF.md contains 'proof {nonce}'.\n"
        "- Existing proof history is preserved.\n"
        "- PROJECT_STATUS.md records the same proof nonce factually.\n"
        "- Repository declared tests pass.\n"
        "- Change reaches main only through PR, exact-head CI, independent review "
        "and independent security verification.\n"
    )

    issue = runner.github.create_issue(
        repository,
        f"[P0][COMMISSION] Sigma autonomous proof {nonce}",
        issue_body,
    )
    issue_number = int(issue["number"])

    mission = orchestrator.run(
        (
            f"Sigma autonomous commissioning task for {repository}#{issue_number}. "
            f"{objective}"
        ),
        evidence=[
            {
                "id": "commissioning-acceptance",
                "source": f"github:{repository}#{issue_number}",
                "content": issue_body,
            }
        ],
        requested_by="sigma-end-to-end-commissioning",
        max_cycles=1,
    )
    mission_id = str(mission.get("id") or "")
    if not mission_id:
        raise RuntimeError("Sigma planning mission did not produce an id")

    worker_result = runner.worker.dispatch(
        {
            "mission_id": mission_id,
            "repository": repository,
            "issue_number": issue_number,
            "objective": objective,
            "issue_body": issue_body,
            "sigma_mission": mission,
            "authority": {
                "production_release": False,
                "destructive_actions": False,
                "paid_spend": False,
                "direct_main_push": False,
            },
        }
    )
    if str(worker_result.get("status", "")).upper() not in {"CHANGED", "TESTED"}:
        runner.github.comment_issue(
            repository,
            issue_number,
            "Sigma commissioning worker failed before PR delivery.\n\n"
            + "json:\n"
            + json.dumps(worker_result, ensure_ascii=False, default=str)[:6000],
        )
        raise RuntimeError("Sigma worker did not produce a tested repository change")

    delivery = DeliverySupervisor(
        runner.github,
        runner.worker,
        orchestrator,
        poll_seconds=float(os.getenv("SIGMA_RUNNER_CI_POLL_SECONDS", "10")),
        ci_timeout_seconds=int(
            os.getenv("SIGMA_RUNNER_CI_TIMEOUT_SECONDS", "1200")
        ),
        max_repairs=int(os.getenv("SIGMA_RUNNER_MAX_REPAIRS", "2")),
    ).finish(
        repository=repository,
        issue_number=issue_number,
        mission_id=mission_id,
        objective=objective,
        issue_body=issue_body,
        worker_result=worker_result,
    )

    result = {
        "status": "PASS" if delivery.state == "DONE" else "FAIL",
        "repository": repository,
        "issue_number": issue_number,
        "proof_nonce": nonce,
        "planning_mission_id": mission_id,
        "worker": worker_result,
        "delivery": delivery.as_dict(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if delivery.state != "DONE":
        runner.github.comment_issue(
            repository,
            issue_number,
            "Sigma end-to-end commissioning did not reach DONE.\n\n"
            + "json:\n"
            + json.dumps(delivery.as_dict(), ensure_ascii=False)[:6000],
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
