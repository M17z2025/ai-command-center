import tempfile
import unittest
from pathlib import Path

from sigma_runtime import MeshConfig, MissionRouter, MissionStore, SigmaOrchestrator
from sigma_runtime.learning import LearningController, LessonEvaluation
from sigma_runtime.memory import (
    DeterministicKnowledgeMemory,
    MemoryEpisode,
    MemoryQuery,
)
from sigma_runtime.provider import DeterministicTestProvider


class SigmaMemoryTests(unittest.TestCase):
    def test_candidate_memory_is_not_retrieved_by_default(self):
        memory = DeterministicKnowledgeMemory()
        memory.add_episode(
            MemoryEpisode.create(
                title="Candidate",
                content="repair tenant isolation with RLS",
                source="test",
                source_type="lesson",
                status="CANDIDATE",
            )
        )
        self.assertEqual(memory.search(MemoryQuery("tenant isolation")), [])

    def test_promoted_memory_is_retrieved(self):
        memory = DeterministicKnowledgeMemory()
        memory.add_episode(
            MemoryEpisode.create(
                title="Promoted",
                content="repair tenant isolation with RLS",
                source="test",
                source_type="lesson",
                status="PROMOTED",
            )
        )
        results = memory.search(MemoryQuery("tenant isolation"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "PROMOTED")

    def test_learning_requires_independent_hard_gates_before_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "runtime.db")
            memory = DeterministicKnowledgeMemory()
            store.create_mission("m1", "test", "ci", {})
            lesson_id = store.add_lesson("m1", "Use RLS hostile-path tests.")
            controller = LearningController(store, memory)

            result = controller.evaluate(
                lesson_id,
                LessonEvaluation(
                    evaluator="sigma-independent-evaluator",
                    benchmark_id="memory-benchmark-1",
                    benchmark_passed=True,
                    security_passed=True,
                    regression_passed=True,
                    rationale="Improves hostile-path detection without regression.",
                ),
            )
            self.assertEqual(result["status"], "EVALUATED")
            promoted = controller.promote(lesson_id, project="owner/repo")
            self.assertEqual(promoted["lesson"]["status"], "PROMOTED")
            self.assertEqual(len(memory.episodes), 1)

    def test_failed_evaluation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "runtime.db")
            memory = DeterministicKnowledgeMemory()
            store.create_mission("m1", "test", "ci", {})
            lesson_id = store.add_lesson("m1", "Unproven lesson.")
            controller = LearningController(store, memory)
            result = controller.evaluate(
                lesson_id,
                LessonEvaluation(
                    evaluator="sigma-independent-evaluator",
                    benchmark_id="memory-benchmark-2",
                    benchmark_passed=False,
                    security_passed=True,
                    regression_passed=True,
                    rationale="No measurable improvement.",
                ),
            )
            self.assertEqual(result["status"], "REJECTED")
            with self.assertRaises(ValueError):
                controller.promote(lesson_id)

    def test_orchestrator_retrieves_promoted_memory_before_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "runtime.db")
            memory = DeterministicKnowledgeMemory()
            memory.add_episode(
                MemoryEpisode.create(
                    title="Known pattern",
                    content="secure AI software services require explicit evidence gates",
                    source="verified-test",
                    source_type="lesson",
                    status="PROMOTED",
                )
            )
            config = MeshConfig(".")
            router = MissionRouter(config)
            orchestrator = SigmaOrchestrator(
                config,
                router,
                DeterministicTestProvider(),
                store,
                memory,
            )
            result = orchestrator.run(
                "Design secure AI software services with evidence gates.",
                evidence=[],
                requested_by="ci",
                max_cycles=1,
            )
            retrieval = [
                event
                for event in result["events"]
                if event["stage"] == "memory-retrieval"
            ]
            self.assertEqual(retrieval[0]["payload"]["results"], 1)


if __name__ == "__main__":
    unittest.main()
