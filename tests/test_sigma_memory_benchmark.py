import unittest

from sigma_runtime.memory import DeterministicKnowledgeMemory, MemoryEpisode
from sigma_runtime.memory_benchmark import (
    MemoryBenchmarkCase,
    run_memory_benchmark,
)


class SigmaMemoryBenchmarkTests(unittest.TestCase):
    def test_benchmark_passes_promoted_recall(self):
        memory = DeterministicKnowledgeMemory()
        memory.add_episode(
            MemoryEpisode.create(
                title="Invoiceit repair",
                content="Tenant isolation requires hostile RLS read and write tests.",
                source="verified",
                source_type="repair",
                project="invoiceit",
                status="PROMOTED",
            )
        )
        result = run_memory_benchmark(
            memory,
            [
                MemoryBenchmarkCase(
                    id="tenant-isolation",
                    query="tenant isolation RLS",
                    expected_substrings=("hostile rls",),
                    project="invoiceit",
                )
            ],
        )
        self.assertTrue(result.passes)
        self.assertEqual(result.recall_rate, 1.0)

    def test_benchmark_detects_stale_forbidden_fact(self):
        memory = DeterministicKnowledgeMemory()
        memory.add_episode(
            MemoryEpisode.create(
                title="Old provider",
                content="Alysha uses legacy-provider-x for voice.",
                source="old",
                source_type="historical",
                project="alysha",
                status="PROMOTED",
            )
        )
        result = run_memory_benchmark(
            memory,
            [
                MemoryBenchmarkCase(
                    id="provider-current",
                    query="Alysha voice provider",
                    expected_substrings=(),
                    forbidden_substrings=("legacy-provider-x",),
                    project="alysha",
                )
            ],
        )
        self.assertFalse(result.passes)
        self.assertEqual(result.stale_fact_failures, 1)


if __name__ == "__main__":
    unittest.main()
