"""Small reproducible benchmark harness for Sigma memory strategies.

This is not a replacement for AgentMemoryBench. It provides a fast CI gate for
Sigma-specific recall, stale-memory and repair cases; larger continual-memory
evaluation can use AgentMemoryBench offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .memory import KnowledgeMemory, MemoryQuery


@dataclass(frozen=True)
class MemoryBenchmarkCase:
    id: str
    query: str
    expected_substrings: tuple[str, ...]
    forbidden_substrings: tuple[str, ...] = ()
    project: str | None = None


@dataclass(frozen=True)
class MemoryBenchmarkResult:
    cases: int
    passed: int
    failed: int
    recall_rate: float
    stale_fact_failures: int

    @property
    def passes(self) -> bool:
        return self.failed == 0 and self.stale_fact_failures == 0


def run_memory_benchmark(
    memory: KnowledgeMemory,
    cases: Iterable[MemoryBenchmarkCase],
) -> MemoryBenchmarkResult:
    total = 0
    passed = 0
    stale = 0

    for case in cases:
        total += 1
        results = memory.search(
            MemoryQuery(text=case.query, project=case.project, limit=8)
        )
        text = "\n".join(item.text.lower() for item in results)
        expected = all(item.lower() in text for item in case.expected_substrings)
        forbidden = any(item.lower() in text for item in case.forbidden_substrings)
        if forbidden:
            stale += 1
        if expected and not forbidden:
            passed += 1

    failed = total - passed
    return MemoryBenchmarkResult(
        cases=total,
        passed=passed,
        failed=failed,
        recall_rate=(passed / total) if total else 0.0,
        stale_fact_failures=stale,
    )
