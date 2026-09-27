import unittest

from sigma_runtime.workers import CapabilityPolicy, WorkerMission, WorkerResult, WorkerStatus
from sigma_runtime.workers.benchmark import benchmark_from_result
from sigma_runtime.workers.openhands import OpenHandsWorkerAdapter, OpenHandsWorkerConfig


class OpenHandsWorkerTests(unittest.TestCase):
    def mission(self, **overrides):
        values = {
            "mission_id": "openhands-proof",
            "parent_agent": "algorithmic-engineering-director",
            "project": "M17z2025/ai-command-center",
            "objective": "Make a bounded change in an isolated test repository.",
            "acceptance_criteria": ("Tests pass.",),
            "capabilities": CapabilityPolicy(
                allow=frozenset({"read_repository", "write_repository", "run_tests", "sandbox_execution"}),
                deny=frozenset({"production_release", "manage_secrets"}),
            ),
            "filesystem_scope": ("/workspace/test-repo",),
        }
        values.update(overrides)
        return WorkerMission(**values)

    def runner(self, mission):
        return WorkerResult(
            mission_id=mission.mission_id,
            status=WorkerStatus.TESTED,
            changes=("bounded test change",),
            tests_executed=("python -m unittest",),
            evidence=("sandbox-run",),
            next_action="Independent Sigma verification.",
        )

    def test_disabled_by_default(self):
        result = OpenHandsWorkerAdapter(runner=self.runner).execute(self.mission())
        self.assertEqual(result.status, WorkerStatus.BLOCKED)

    def test_requires_sandbox_capability(self):
        mission = self.mission(
            capabilities=CapabilityPolicy(
                allow=frozenset({"read_repository", "write_repository", "run_tests"})
            )
        )
        adapter = OpenHandsWorkerAdapter(
            runner=self.runner,
            config=OpenHandsWorkerConfig(enabled=True),
        )
        self.assertEqual(adapter.execute(mission).status, WorkerStatus.BLOCKED)

    def test_rejects_credentials_in_proof_phase(self):
        adapter = OpenHandsWorkerAdapter(
            runner=self.runner,
            config=OpenHandsWorkerConfig(enabled=True),
        )
        result = adapter.execute(self.mission(credential_scope=("GITHUB_TOKEN",)))
        self.assertEqual(result.status, WorkerStatus.BLOCKED)

    def test_rejects_production_release_capability(self):
        mission = self.mission(
            capabilities=CapabilityPolicy(
                allow=frozenset({"sandbox_execution", "production_release"})
            )
        )
        adapter = OpenHandsWorkerAdapter(
            runner=self.runner,
            config=OpenHandsWorkerConfig(enabled=True),
        )
        self.assertEqual(adapter.execute(mission).status, WorkerStatus.BLOCKED)

    def test_executes_in_bounded_proof_configuration(self):
        events = []
        adapter = OpenHandsWorkerAdapter(
            runner=self.runner,
            config=OpenHandsWorkerConfig(enabled=True),
        )
        result = adapter.execute(
            self.mission(),
            audit_sink=lambda event, payload: events.append((event, payload)),
        )
        self.assertEqual(result.status, WorkerStatus.TESTED)
        self.assertEqual([event for event, _ in events], ["worker.started", "worker.finished"])

    def test_benchmark_hard_gates(self):
        result = self.runner(self.mission())
        benchmark = benchmark_from_result(
            "openhands-software-engineering-worker",
            result,
            elapsed_seconds=12.0,
            tests_passed=6,
        )
        self.assertTrue(benchmark.passes_hard_gates)

        failed = benchmark_from_result(
            "openhands-software-engineering-worker",
            result,
            elapsed_seconds=12.0,
            tests_passed=5,
            tests_failed=1,
        )
        self.assertFalse(failed.passes_hard_gates)


if __name__ == "__main__":
    unittest.main()
