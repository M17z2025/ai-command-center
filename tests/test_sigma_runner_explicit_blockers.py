"""Regression: narrative failure vocabulary must not defeat code-ready queue labels."""
from unittest import TestCase
from unittest.mock import patch

from sigma_runtime.portfolio_runner import _work_item


class ExplicitBlockerTests(TestCase):
    def issue(self, body, labels=("sigma:ready-for-code",), title="[P0] Repair coding worker"):
        return {
            "number": 158,
            "title": title,
            "body": body,
            "labels": [{"name": label} for label in labels],
        }

    def test_code_ready_issue_may_require_structured_blocked_result(self):
        with patch.dict("os.environ", {"SIGMA_RUNNER_REQUIRE_READY_LABEL": "1"}):
            item = _work_item(
                "M17z2025/ai-command-center",
                self.issue(
                    "Require a structured BLOCKED result when no diff exists. "
                    "Compare prior blocked runs and add a failing regression test."
                ),
            )
        self.assertTrue(item.executable)
        self.assertEqual(item.state, "EXECUTABLE")

    def test_owner_blocker_label_still_wins_over_ready_label(self):
        item = _work_item(
            "owner/repo",
            self.issue("Implement safe verification", labels=("sigma:ready-for-code", "blocked-owner")),
        )
        self.assertFalse(item.executable)
        self.assertEqual(item.state, "BLOCKED_OWNER")

    def test_explicit_status_blocks_even_with_ready_label(self):
        item = _work_item("owner/repo", self.issue("Status: BLOCKED — awaiting credentials"))
        self.assertFalse(item.executable)
        self.assertEqual(item.state, "BLOCKED_EXTERNAL")

    def test_explicit_blocker_blocks_even_with_ready_label(self):
        item = _work_item("owner/repo", self.issue("Blocker: external approval required"))
        self.assertFalse(item.executable)
        self.assertEqual(item.state, "BLOCKED_EXTERNAL")

    def test_none_blocker_is_not_a_blocker(self):
        item = _work_item("owner/repo", self.issue("Blockers: none\nAdd test for BLOCKED result"))
        self.assertTrue(item.executable)

    def test_blocked_title_marker_blocks(self):
        item = _work_item(
            "owner/repo", self.issue("Implement", title="[P0][BLOCKED] Needs approval")
        )
        self.assertFalse(item.executable)
        self.assertEqual(item.state, "BLOCKED_EXTERNAL")

    def test_non_ready_issue_stays_non_ready(self):
        with patch.dict("os.environ", {"SIGMA_RUNNER_REQUIRE_READY_LABEL": "1"}):
            item = _work_item("owner/repo", self.issue("Implement", labels=()))
        self.assertFalse(item.executable)
        self.assertEqual(item.state, "NOT_CODE_READY")
