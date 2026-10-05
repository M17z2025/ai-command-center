import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.sigma_coding_harness import (
    HarnessPolicyError,
    build_mission_prompt,
    critical_capability_profile,
    repository_context,
    validate_changed_paths,
    validate_workspace_path,
)


class SigmaCodingHarnessTests(unittest.TestCase):
    def test_critical_profile_contains_all_five_adapted_patterns(self):
        profile = critical_capability_profile()
        self.assertIn("multi_agent_coding_harness", profile)
        self.assertIn("coding_harness_starter", profile)
        self.assertIn("local_file_editing_agent", profile)
        self.assertIn("sandboxed_code_execution_mcp", profile)
        self.assertIn("github_mcp_agent", profile)
        self.assertFalse(profile["paid_external_dependencies"])
        self.assertFalse(profile["agent_has_github_credentials"])

    def test_rejects_absolute_traversal_and_sensitive_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for candidate in (
                "/etc/passwd",
                "../outside.txt",
                "src/../../outside.txt",
                ".env",
                ".env.production",
                ".env.staging",
                "private.pem",
                ".git/config",
                "node_modules/pkg/index.js",
            ):
                with self.subTest(candidate=candidate):
                    with self.assertRaises(HarnessPolicyError):
                        validate_workspace_path(root, candidate)

    def test_allows_env_example_but_not_real_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                validate_workspace_path(root, ".env.example"),
                ".env.example",
            )
            with self.assertRaises(HarnessPolicyError):
                validate_workspace_path(root, ".env.local")

    def test_rejects_symlink_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / (root.name + "-outside")
            outside.mkdir(exist_ok=True)
            try:
                link = root / "linked"
                try:
                    link.symlink_to(outside, target_is_directory=True)
                except OSError:
                    self.skipTest("symlinks unavailable on this platform")
                with self.assertRaises(HarnessPolicyError):
                    validate_workspace_path(root, "linked/file.txt")
            finally:
                try:
                    outside.rmdir()
                except OSError:
                    pass

    def test_validate_changed_paths_is_canonical_and_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
            self.assertEqual(
                validate_changed_paths(
                    root,
                    ["src/app.py", "src/app.py", ".env.example"],
                ),
                ("src/app.py", ".env.example"),
            )

    def test_repository_context_is_bounded_and_secret_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".sigma").mkdir()
            (root / ".sigma" / "project.yaml").write_text(
                "commands:\n  test: python -m unittest\n",
                encoding="utf-8",
            )
            (root / "PROJECT_STATUS.md").write_text(
                "Status: active\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
                "Sigma fixture README\n",
                encoding="utf-8",
            )
            (root / ".env").write_text("SECRET=do-not-read\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "noise.js").write_text(
                "noise\n", encoding="utf-8"
            )

            context = repository_context(root, max_chars=2000)
            self.assertIn(".sigma/project.yaml", context)
            self.assertIn("PROJECT_STATUS.md", context)
            self.assertIn("src/app.py", context)
            self.assertIn("Sigma fixture README", context)
            self.assertNotIn("SECRET=do-not-read", context)
            self.assertNotIn("node_modules/noise.js", context)
            self.assertLessEqual(len(context), 2000)

    def test_prompt_binds_sigma_plan_and_ordered_harness_phases(self):
        prompt = build_mission_prompt(
            {
                "objective": "Fix issue 118",
                "issue_body": "Acceptance criteria",
                "sigma_mission": {"id": "mission-1", "plan": ["inspect", "edit"]},
            },
            "FILE INVENTORY:\nsrc/app.py",
        )
        for phase in ("1. PLAN:", "2. INSPECT:", "3. EDIT:", "4. SELF-REVIEW:", "5. HANDOFF:"):
            self.assertIn(phase, prompt)
        self.assertIn("mission-1", prompt)
        self.assertIn("GitHub/runtime credentials are deliberately outside", prompt)
        self.assertIn("wrapper-owned manifest verification", prompt)

    def test_repair_prompt_carries_failure_evidence(self):
        prompt = build_mission_prompt(
            {
                "objective": "Repair failing test",
                "issue_body": "criteria",
                "repair_attempt": 2,
                "failure_evidence": ["pytest failed at test_widget"],
            },
            "FILE INVENTORY:\nwidget.py",
        )
        self.assertIn("BOUNDED REPAIR PASS", prompt)
        self.assertIn("pytest failed at test_widget", prompt)


if __name__ == "__main__":
    unittest.main()
