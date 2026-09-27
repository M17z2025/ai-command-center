import unittest

from sigma_runtime.workers import (
    CapabilityPolicy,
    DeterministicWorkerAdapter,
    WorkerMission,
    WorkerStatus,
)


class WorkerContractTests(unittest.TestCase):
    def mission(self, **overrides):
        values = {
            "mission_id": "mission-59-smoke",
            "parent_agent": "sigma-governor",
            "project": "M17z2025/ai-command-center",
            "objective": "Prove the bounded worker contract.",
            "acceptance_criteria": ("No unapproved spend.", "Audit events emitted."),
            "capabilities": CapabilityPolicy(
                allow=frozenset({"read_repository", "run_tests"}),
                deny=frozenset({"production_release", "manage_secrets"}),
            ),
            "required_evidence": ("test result",),
        }
        values.update(overrides)
        return WorkerMission(**values)

    def test_capability_policy_is_fail_closed(self):
        policy = CapabilityPolicy(allow=frozenset({"read_repository"}))
        self.assertTrue(policy.permits("read_repository"))
        self.assertFalse(policy.permits("write_repository"))
        with self.assertRaises(PermissionError):
            policy.require("write_repository")

    def test_conflicting_capabilities_are_rejected(self):
        with self.assertRaises(ValueError):
            CapabilityPolicy(
                allow=frozenset({"shell"}),
                deny=frozenset({"shell"}),
            )

    def test_worker_defaults_to_zero_spend_and_bounded_timeout(self):
        mission = self.mission()
        self.assertEqual(mission.spend_ceiling, 0.0)
        self.assertGreater(mission.timeout_seconds, 0)

    def test_worker_cannot_report_verified_or_released(self):
        statuses = {status.value for status in WorkerStatus}
        self.assertNotIn("VERIFIED", statuses)
        self.assertNotIn("RELEASED", statuses)

    def test_deterministic_worker_emits_audit_and_tested_result(self):
        events = []
        result = DeterministicWorkerAdapter().execute(
            self.mission(),
            audit_sink=lambda event, payload: events.append((event, payload)),
        )
        self.assertEqual(result.status, WorkerStatus.TESTED)
        self.assertEqual([event for event, _ in events], ["worker.started", "worker.finished"])
        self.assertEqual(events[-1][1]["status"], "TESTED")

    def test_deterministic_worker_blocks_nonzero_spend(self):
        result = DeterministicWorkerAdapter().execute(
            self.mission(spend_ceiling=1.0)
        )
        self.assertEqual(result.status, WorkerStatus.BLOCKED)
        self.assertTrue(result.unresolved_failures)


if __name__ == "__main__":
    unittest.main()
