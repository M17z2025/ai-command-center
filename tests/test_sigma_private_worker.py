import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sigma_openhands_worker_service",
    ROOT / "scripts" / "sigma_openhands_worker_service.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class SigmaPrivateWorkerTests(unittest.TestCase):
    def test_branch_is_non_main_sigma_namespace(self):
        branch = MOD._branch_name(80, "12345678-abcd")
        self.assertTrue(branch.startswith("sigma/issue-80-"))
        self.assertNotEqual(branch, "main")

    def test_non_allowlisted_repository_is_rejected_before_clone(self):
        old = os.environ.get("SIGMA_WORKER_ALLOWED_REPOSITORIES")
        os.environ["SIGMA_WORKER_ALLOWED_REPOSITORIES"] = "M17z2025/ai-command-center"
        try:
            with self.assertRaises(MOD.WorkerError):
                MOD.run_mission(
                    {
                        "mission_id": "m1",
                        "repository": "other/private-repo",
                        "objective": "test",
                        "authority": {},
                    }
                )
        finally:
            if old is None:
                os.environ.pop("SIGMA_WORKER_ALLOWED_REPOSITORIES", None)
            else:
                os.environ["SIGMA_WORKER_ALLOWED_REPOSITORIES"] = old

    def test_forbidden_authority_is_rejected_before_clone(self):
        for key in (
            "production_release",
            "destructive_actions",
            "paid_spend",
            "direct_main_push",
        ):
            with self.subTest(key=key):
                with self.assertRaises(MOD.WorkerError):
                    MOD.run_mission(
                        {
                            "mission_id": "m1",
                            "repository": "M17z2025/ai-command-center",
                            "objective": "test",
                            "authority": {key: True},
                        }
                    )

    def test_prompt_forbids_worker_git_and_release_authority(self):
        prompt = MOD._mission_prompt(
            {
                "objective": "Fix a bounded test issue",
                "issue_body": "Acceptance criteria",
            }
        )
        self.assertIn("Do not deploy", prompt)
        self.assertIn("push branches", prompt)
        self.assertIn("open pull requests", prompt)
        self.assertIn("VERIFIED", prompt)


    def test_manifest_driven_verification_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".sigma").mkdir()
            (root / ".sigma" / "project.yaml").write_text(
                """
commands:
  install: npm ci
  lint: npm run lint
  typecheck: npm run typecheck
  test: npm test
""".strip(),
                encoding="utf-8",
            )
            self.assertEqual(
                MOD._verification_commands(root),
                ["npm ci", "npm run lint", "npm run typecheck", "npm test"],
            )

    def test_agent_environment_hides_wrapper_secrets(self):
        old = os.environ.get("SIGMA_GITHUB_TOKEN")
        os.environ["SIGMA_GITHUB_TOKEN"] = "secret-value"
        try:
            with MOD._secrets_hidden_from_agent():
                self.assertNotIn("SIGMA_GITHUB_TOKEN", os.environ)
            self.assertEqual(os.environ.get("SIGMA_GITHUB_TOKEN"), "secret-value")
        finally:
            if old is None:
                os.environ.pop("SIGMA_GITHUB_TOKEN", None)
            else:
                os.environ["SIGMA_GITHUB_TOKEN"] = old

    def test_repair_prompt_carries_failure_evidence(self):
        prompt = MOD._mission_prompt(
            {
                "objective": "Fix feature",
                "issue_body": "criteria",
                "repair_attempt": 1,
                "failure_evidence": ["tests failed"],
            }
        )
        self.assertIn("THIS IS A REPAIR PASS", prompt)
        self.assertIn("tests failed", prompt)

    def test_worker_dependencies_are_pinned(self):
        text = (ROOT / "requirements-worker.txt").read_text(encoding="utf-8")
        self.assertIn("openhands-sdk==1.49.6", text)
        self.assertIn("openhands-tools==1.49.6", text)
        self.assertIn("PyYAML==6.0.2", text)

    def test_worker_compose_is_private_and_write_disabled_by_default(self):
        text = (
            ROOT / "deploy" / "sigma-stack" / "docker-compose.ollama.yml"
        ).read_text(encoding="utf-8")
        worker = text.split("  sigma-worker:", 1)[1]
        self.assertIn("SIGMA_WORKER_ALLOW_WRITE: ${SIGMA_WORKER_ALLOW_WRITE:-0}", worker)
        self.assertIn('expose:', worker)
        self.assertNotIn('ports:', worker.split("\nvolumes:", 1)[0])
        self.assertIn("OLLAMA_MAX_LOADED_MODELS", text)
        self.assertIn("OLLAMA_NUM_PARALLEL", text)


if __name__ == "__main__":
    unittest.main()
