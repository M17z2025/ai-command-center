"""Controlled Sigma lesson evaluation and memory promotion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .memory import KnowledgeMemory, MemoryEpisode
from .store import MissionStore


@dataclass(frozen=True)
class LessonEvaluation:
    evaluator: str
    benchmark_id: str
    benchmark_passed: bool
    security_passed: bool
    regression_passed: bool
    rationale: str

    @property
    def promotable(self) -> bool:
        return (
            bool(self.evaluator.strip())
            and bool(self.benchmark_id.strip())
            and self.benchmark_passed
            and self.security_passed
            and self.regression_passed
            and bool(self.rationale.strip())
        )


class LearningController:
    """Promotes only independently evaluated lessons into trusted memory."""

    def __init__(self, store: MissionStore, memory: KnowledgeMemory) -> None:
        self.store = store
        self.memory = memory

    def evaluate(self, lesson_id: str, evaluation: LessonEvaluation) -> dict[str, Any]:
        lesson = self.store.get_lesson(lesson_id)
        if not lesson:
            raise KeyError(lesson_id)
        if lesson["status"] != "CANDIDATE":
            raise ValueError(
                f"Lesson {lesson_id} must be CANDIDATE before evaluation; "
                f"current={lesson['status']}"
            )
        status = "EVALUATED" if evaluation.promotable else "REJECTED"
        metadata = {
            "evaluation": {
                "evaluator": evaluation.evaluator,
                "benchmark_id": evaluation.benchmark_id,
                "benchmark_passed": evaluation.benchmark_passed,
                "security_passed": evaluation.security_passed,
                "regression_passed": evaluation.regression_passed,
                "rationale": evaluation.rationale,
            }
        }
        self.store.set_lesson_status(lesson_id, status, metadata)
        return self.store.get_lesson(lesson_id) or {}

    def promote(
        self,
        lesson_id: str,
        *,
        project: str | None = None,
        source: str = "sigma-reviewed-lesson",
    ) -> dict[str, Any]:
        lesson = self.store.get_lesson(lesson_id)
        if not lesson:
            raise KeyError(lesson_id)
        if lesson["status"] != "EVALUATED":
            raise ValueError(
                f"Lesson {lesson_id} must be EVALUATED before promotion; "
                f"current={lesson['status']}"
            )
        evaluation = (lesson.get("metadata") or {}).get("evaluation") or {}
        hard_gates = (
            evaluation.get("benchmark_passed") is True
            and evaluation.get("security_passed") is True
            and evaluation.get("regression_passed") is True
            and bool(str(evaluation.get("evaluator", "")).strip())
        )
        if not hard_gates:
            raise ValueError("Lesson evaluation does not satisfy promotion hard gates")

        episode = MemoryEpisode.create(
            title=f"Promoted Sigma lesson {lesson_id}",
            content=lesson["lesson"],
            source=source,
            source_type="reviewed_lesson",
            project=project,
            classification="private",
            provenance={
                "lesson_id": lesson_id,
                "mission_id": lesson["mission_id"],
                "evaluator": str(evaluation.get("evaluator", "")),
                "benchmark_id": str(evaluation.get("benchmark_id", "")),
            },
            status="PROMOTED",
        )
        stored = self.memory.add_episode(episode)
        self.store.set_lesson_status(
            lesson_id,
            "PROMOTED",
            {"memory_episode_id": episode.id, "memory_adapter": self.memory.adapter_id},
        )
        return {
            "lesson": self.store.get_lesson(lesson_id),
            "memory": stored,
        }

    def reject(self, lesson_id: str, *, reviewer: str, reason: str) -> dict[str, Any]:
        if not reviewer.strip() or not reason.strip():
            raise ValueError("reviewer and reason are required")
        lesson = self.store.get_lesson(lesson_id)
        if not lesson:
            raise KeyError(lesson_id)
        if lesson["status"] == "PROMOTED":
            raise ValueError("Promoted lessons require a supersession/correction flow")
        self.store.set_lesson_status(
            lesson_id,
            "REJECTED",
            {"rejection": {"reviewer": reviewer, "reason": reason}},
        )
        return self.store.get_lesson(lesson_id) or {}
