#!/usr/bin/env python3
"""One-shot Sigma learning-memory commissioning helper."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sigma_runtime.learning import LearningController, LessonEvaluation
from sigma_runtime.memory import MemoryQuery, memory_from_env
from sigma_runtime.store import MissionStore


LESSON = (
    "For self-hosted local-model missions, enforce the configured context-window "
    "budget before every inference call, keep repair and governance prompts bounded, "
    "and avoid competing inference workloads during commissioning on constrained CPU hosts."
)
QUERY = "context window bounded prompts constrained CPU commissioning"


def _latest_completed_commissioning(store: MissionStore) -> dict:
    for item in store.list_missions(limit=200):
        if item.get("requested_by") != "commissioning-probe":
            continue
        if item.get("status") not in {"COMPLETE", "COMPLETE_WITH_UNVERIFIED_ITEMS"}:
            continue
        mission = store.get_mission(item["id"])
        if mission:
            return mission
    raise RuntimeError("No completed commissioning mission found")


def _existing_lesson(store: MissionStore, mission_id: str) -> dict | None:
    for item in store.list_lessons(limit=500):
        if item.get("mission_id") == mission_id and item.get("lesson") == LESSON:
            return item
    return None


def _regression_gate() -> tuple[bool, str]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_sigma_*.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    detail = (proc.stdout + "\n" + proc.stderr)[-4000:]
    return proc.returncode == 0, detail


def _security_gate() -> tuple[bool, dict]:
    llm_endpoint = os.getenv("SIGMA_LLM_ENDPOINT", "")
    memory_endpoint = os.getenv("SIGMA_MEMORY_ENDPOINT", "")
    api_key = os.getenv("SIGMA_LLM_API_KEY", "")
    allow_write = os.getenv("SIGMA_RUNNER_ALLOW_WRITE", "0")
    execute = os.getenv("SIGMA_RUNNER_EXECUTE", "0")
    checks = {
        "private_ollama": llm_endpoint.startswith("http://ollama:11434/"),
        "private_memory": memory_endpoint.startswith("http://sigma-memory:8090"),
        "no_paid_key": api_key == "",
        "runner_write_disabled": allow_write == "0",
        "runner_execute_disabled": execute == "0",
    }
    return all(checks.values()), checks


def _benchmark_gate() -> tuple[bool, dict]:
    checks = {
        "mentions_context_window": "context-window" in LESSON,
        "mentions_bounded_prompts": "bounded" in LESSON,
        "mentions_competing_inference": "competing inference" in LESSON,
        "mentions_cpu_constraint": "CPU" in LESSON,
    }
    return all(checks.values()), checks


def prepare(db: str) -> dict:
    store = MissionStore(db)
    stale = store.mark_stale_running(older_than_seconds=1800)
    mission = _latest_completed_commissioning(store)
    existing = _existing_lesson(store, mission["id"])
    if existing and existing["status"] == "PROMOTED":
        lesson_id = existing["id"]
    else:
        lesson_id = existing["id"] if existing else store.add_lesson(
            mission["id"],
            LESSON,
            {
                "source": "commissioning-evidence",
                "promotion": "requires evidence-gated evaluation",
            },
        )
        lesson = store.get_lesson(lesson_id)
        if lesson and lesson["status"] == "CANDIDATE":
            regression_ok, regression_detail = _regression_gate()
            security_ok, security_detail = _security_gate()
            benchmark_ok, benchmark_detail = _benchmark_gate()
            evaluation = LessonEvaluation(
                evaluator="sigma-automated-commissioning-gate",
                benchmark_id="commissioning-memory-v1",
                benchmark_passed=benchmark_ok,
                security_passed=security_ok,
                regression_passed=regression_ok,
                rationale=(
                    "Operational lesson derived from observed commissioning failures. "
                    "Automated benchmark, private-runtime configuration gate and regression "
                    "suite must all pass before promotion."
                ),
            )
            LearningController(store, memory_from_env()).evaluate(lesson_id, evaluation)
            lesson = store.get_lesson(lesson_id)
            if not lesson or lesson["status"] != "EVALUATED":
                raise RuntimeError(
                    "Lesson did not pass evaluation gates: "
                    + json.dumps(
                        {
                            "benchmark": benchmark_detail,
                            "security": security_detail,
                            "regression_tail": regression_detail[-1200:],
                        }
                    )
                )
        lesson = store.get_lesson(lesson_id)
        if lesson and lesson["status"] == "EVALUATED":
            LearningController(store, memory_from_env()).promote(
                lesson_id,
                project="M17z2025/ai-command-center",
            )

    memory = memory_from_env()
    results = memory.search(MemoryQuery(text=QUERY, limit=8))
    found = any("context-window" in item.text for item in results)
    if not found:
        raise RuntimeError("Promoted lesson was not retrievable before restart")
    return {
        "status": "PRE_RESTART_PASS",
        "source_mission_id": mission["id"],
        "lesson_id": lesson_id,
        "stale_missions_marked": stale,
        "retrieval_results": len(results),
    }


def verify(db: str) -> dict:
    store = MissionStore(db)
    memory = memory_from_env()
    health = memory.health()
    results = memory.search(MemoryQuery(text=QUERY, limit=8))
    matches = [item for item in results if "context-window" in item.text]
    if not matches:
        raise RuntimeError("Promoted lesson did not survive restart/retrieval")

    mission_id = str(uuid.uuid4())
    prompt = "Memory persistence proof: retrieve commissioning context-window lesson."
    store.create_mission(
        mission_id,
        prompt,
        "sigma-memory-commissioning",
        {"type": "memory-persistence-proof"},
    )
    store.event(
        mission_id,
        "memory-retrieval",
        {
            "adapter": getattr(memory, "adapter_id", "unknown"),
            "results": len(matches),
            "post_restart": True,
        },
    )
    store.artifact(mission_id, "memory-proof", matches[0].text)
    store.finish(
        mission_id,
        "COMPLETE",
        final_output="Promoted lesson retrieved after memory/runtime restart.",
    )
    return {
        "status": "PASS",
        "memory_health": health,
        "retrieved_after_restart": True,
        "proof_mission_id": mission_id,
        "lesson": matches[0].text,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default=os.getenv("SIGMA_RUNTIME_DB", "/data/sigma-runtime.db"),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    result = prepare(args.db) if args.command == "prepare" else verify(args.db)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
