"""Comparable evidence records for Sigma worker evaluations."""

from __future__ import annotations

from dataclasses import dataclass

from .base import WorkerResult, WorkerStatus


@dataclass(frozen=True)
class WorkerBenchmark:
    adapter_id: str
    mission_id: str
    status: WorkerStatus
    elapsed_seconds: float
    model_cost: float
    tests_passed: int
    tests_failed: int
    regressions: int
    security_violations: int
    repair_actions_required: int

    def __post_init__(self) -> None:
        numeric = (
            self.elapsed_seconds,
            self.model_cost,
            self.tests_passed,
            self.tests_failed,
            self.regressions,
            self.security_violations,
            self.repair_actions_required,
        )
        if any(value < 0 for value in numeric):
            raise ValueError("Benchmark metrics cannot be negative")

    @property
    def passes_hard_gates(self) -> bool:
        return (
            self.status == WorkerStatus.TESTED
            and self.tests_failed == 0
            and self.regressions == 0
            and self.security_violations == 0
        )


def benchmark_from_result(
    adapter_id: str,
    result: WorkerResult,
    *,
    elapsed_seconds: float,
    model_cost: float = 0.0,
    tests_passed: int = 0,
    tests_failed: int = 0,
    regressions: int = 0,
    security_violations: int = 0,
    repair_actions_required: int = 0,
) -> WorkerBenchmark:
    return WorkerBenchmark(
        adapter_id=adapter_id,
        mission_id=result.mission_id,
        status=result.status,
        elapsed_seconds=elapsed_seconds,
        model_cost=model_cost,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        regressions=regressions,
        security_violations=security_violations,
        repair_actions_required=repair_actions_required,
    )
