import tempfile
import unittest

from sigma_runtime.workers import CapabilityPolicy, WorkerMission, WorkerStatus
from sigma_runtime.workers.openhands_sdk import (
    OpenHandsSDKRunner,
    OpenHandsSDKRunnerConfig,
)


class OpenHandsSDKRunnerTests(unittest.TestCase):
    def mission(self, path):
        return WorkerMission(
            mission_id="openhands-sdk-proof",
            parent_agent="algorithmic-engineering-director",
            project="M17z2025/ai-command-center",
            objective="Make one bounded change.",
            acceptance_criteria=("Tests must pass.",),
            capabilities=CapabilityPolicy(
                allow=frozenset({"sandbox_execution", "read_repository", "write_repository"}),
                deny=frozenset({"production_release", "manage_secrets"}),
            ),
            filesystem_scope=(path,),
            prohibited_actions=("production deployment", "secret management"),
        )

    def test_requires_private_or_loopback_model_endpoint(self):
        config = OpenHandsSDKRunnerConfig(
            model="local-model",
            base_url="https://api.example.com/v1",
            server_image="ghcr.io/openhands/agent-server:1.0.0-python-amd64",
        )
        with self.assertRaises(ValueError):
            config.validate()

    def test_accepts_rfc1918_endpoint(self):
        config = OpenHandsSDKRunnerConfig(
            model="local-model",
            base_url="http://10.0.0.20:8000/v1",
            server_image="ghcr.io/openhands/agent-server:1.0.0-python-amd64",
        )
        config.validate()

    def test_refuses_latest_image(self):
        config = OpenHandsSDKRunnerConfig(
            model="local-model",
            base_url="http://127.0.0.1:8000/v1",
            server_image="ghcr.io/openhands/agent-server:latest-python",
        )
        with self.assertRaises(ValueError):
            config.validate()

    def test_missing_sdk_fails_closed_without_external_execution(self):
        config = OpenHandsSDKRunnerConfig(
            model="local-model",
            base_url="http://127.0.0.1:8000/v1",
            server_image="ghcr.io/openhands/agent-server:1.0.0-python-amd64",
        )
        runner = OpenHandsSDKRunner(config)
        with tempfile.TemporaryDirectory() as workspace:
            result = runner(self.mission(workspace))
        # CI intentionally does not install OpenHands; absence must be a clean BLOCKED
        # result, never an implicit fallback to an ungoverned execution mode.
        self.assertIn(result.status, {WorkerStatus.BLOCKED, WorkerStatus.CHANGED})
        if result.status == WorkerStatus.CHANGED:
            self.assertEqual(result.metadata.get("adapter"), "openhands-sdk")


if __name__ == "__main__":
    unittest.main()
