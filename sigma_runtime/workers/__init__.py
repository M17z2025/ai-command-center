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
from .deterministic import DeterministicWorkerAdapter

__all__ = [
    "CapabilityPolicy",
    "WorkerAdapter",
    "WorkerMission",
    "WorkerResult",
    "WorkerStatus",
    "DeterministicWorkerAdapter",
]
