"""Governed external-worker adapter primitives for Sigma.

External agent frameworks are workers under Sigma authority. They cannot certify
their own work as VERIFIED or RELEASED.
"""

from .base import (
    CapabilityPolicy,
    WorkerAdapter,
    WorkerMission,
    WorkerResult,
    WorkerStatus,
)
from .benchmark import WorkerBenchmark, benchmark_from_result
from .deterministic import DeterministicWorkerAdapter
from .openhands import OpenHandsWorkerAdapter, OpenHandsWorkerConfig

__all__ = [
    "CapabilityPolicy",
    "WorkerAdapter",
    "WorkerMission",
    "WorkerResult",
    "WorkerStatus",
    "WorkerBenchmark",
    "benchmark_from_result",
    "DeterministicWorkerAdapter",
    "OpenHandsWorkerAdapter",
    "OpenHandsWorkerConfig",
]
