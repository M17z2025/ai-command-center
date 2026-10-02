import unittest

from sigma_runtime.pr_supervisor import PullRequestSupervisor, parse_pull_request_url


class FakeGitHub:
    def __init__(self, runs):
        self.runs = runs

    def pull_request(self, repository, number):
        return {"number": number, "head": {"sha": "abc123"}}

    def workflow_runs_for_head(self, repository, head_sha):
        self.requested = (repository, head_sha)
        return list(self.runs)


class PullRequestSupervisorTests(unittest.TestCase):
    def test_parse_canonical_url(self):
        self.assertEqual(
            parse_pull_request_url("https://github.com/owner/repo/pull/42"),
            ("owner/repo", 42),
        )

    def test_rejects_wrong_repository(self):
        supervisor = PullRequestSupervisor(FakeGitHub([]))
        with self.assertRaises(ValueError):
            supervisor.assess("owner/repo", "https://github.com/other/repo/pull/1")

    def test_no_runs_is_pending(self):
        result = PullRequestSupervisor(FakeGitHub([])).assess(
            "owner/repo", "https://github.com/owner/repo/pull/1"
        )
        self.assertEqual(result.state, "CI_PENDING")
        self.assertEqual(result.head_sha, "abc123")

    def test_in_progress_run_is_pending(self):
        runs = [{"id": 1, "status": "in_progress", "conclusion": None}]
        result = PullRequestSupervisor(FakeGitHub(runs)).assess(
            "owner/repo", "https://github.com/owner/repo/pull/1"
        )
        self.assertEqual(result.state, "CI_PENDING")

    def test_failed_run_requires_changes(self):
        runs = [
            {"id": 1, "status": "completed", "conclusion": "success"},
            {"id": 2, "status": "completed", "conclusion": "failure"},
        ]
        result = PullRequestSupervisor(FakeGitHub(runs)).assess(
            "owner/repo", "https://github.com/owner/repo/pull/1"
        )
        self.assertEqual(result.state, "CHANGES_REQUIRED")
        self.assertEqual(len(result.failed_runs), 1)

    def test_all_success_is_ci_passed_not_verified(self):
        runs = [{"id": 1, "status": "completed", "conclusion": "success"}]
        result = PullRequestSupervisor(FakeGitHub(runs)).assess(
            "owner/repo", "https://github.com/owner/repo/pull/1"
        )
        self.assertEqual(result.state, "CI_PASSED")
        self.assertIn("independent", result.next_gate)


if __name__ == "__main__":
    unittest.main()
