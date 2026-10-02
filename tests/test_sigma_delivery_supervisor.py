import unittest

from sigma_runtime.delivery_supervisor import DeliverySupervisor


class FakeGitHub:
    allow_write = True

    def __init__(self, runs_sequence):
        self.runs_sequence = list(runs_sequence)
        self.run_calls = 0
        self.merged = []
        self.comments = []
        self.closed = []

    def pull_request(self, repository, number):
        return {"number": number, "head": {"sha": "head123"}}

    def workflow_runs_for_head(self, repository, head_sha):
        index = min(self.run_calls, len(self.runs_sequence) - 1)
        self.run_calls += 1
        return list(self.runs_sequence[index])

    def workflow_run_jobs(self, repository, run_id):
        if run_id == 2:
            return [{
                "id": 22,
                "name": "tests",
                "conclusion": "failure",
                "steps": [
                    {"name": "unit tests", "conclusion": "failure"}
                ],
            }]
        return []

    def pull_request_files(self, repository, number):
        return [{
            "filename": "sigma_runtime/example.py",
            "status": "modified",
            "additions": 2,
            "deletions": 1,
            "patch": "@@ -1 +1 @@\n-old\n+new",
        }]

    def merge_pull_request(self, repository, number, expected_head_sha):
        self.merged.append((repository, number, expected_head_sha))
        return {"merged": True, "sha": "merge123", "message": "merged"}

    def comment_issue(self, repository, number, body):
        self.comments.append((repository, number, body))

    def close_issue(self, repository, number):
        self.closed.append((repository, number))


class FakeWorker:
    def __init__(self):
        self.payloads = []

    def dispatch(self, payload):
        self.payloads.append(payload)
        return {
            "status": "TESTED",
            "branch": "sigma/issue-7",
            "pull_request_url": "https://github.com/owner/repo/pull/8",
        }


class FakeOrchestrator:
    def __init__(self, statuses=None):
        self.statuses = list(statuses or ["COMPLETE", "COMPLETE"])
        self.calls = []

    def run(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        status = self.statuses.pop(0)
        return {
            "id": f"review-{len(self.calls)}",
            "status": status,
        }


class DeliverySupervisorTests(unittest.TestCase):
    def test_green_pr_is_reviewed_secured_merged_and_closed(self):
        success = [{
            "id": 1,
            "name": "tests",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "head123",
        }]
        github = FakeGitHub([success])
        delivery = DeliverySupervisor(
            github,
            FakeWorker(),
            FakeOrchestrator(),
            poll_seconds=0,
            ci_timeout_seconds=1,
        )
        result = delivery.finish(
            repository="owner/repo",
            issue_number=7,
            mission_id="mission-1",
            objective="Fix feature",
            issue_body="Acceptance criteria",
            worker_result={
                "status": "TESTED",
                "branch": "sigma/issue-7",
                "pull_request_url": "https://github.com/owner/repo/pull/8",
            },
        )
        self.assertEqual(result.state, "DONE")
        self.assertEqual(result.merge_sha, "merge123")
        self.assertEqual(github.closed, [("owner/repo", 7)])
        self.assertEqual(len(github.comments), 1)

    def test_failed_ci_dispatches_bounded_same_pr_repair(self):
        failed = [{
            "id": 2,
            "name": "tests",
            "status": "completed",
            "conclusion": "failure",
            "head_sha": "head123",
        }]
        success = [{
            "id": 3,
            "name": "tests",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "head123",
        }]
        worker = FakeWorker()
        delivery = DeliverySupervisor(
            FakeGitHub([failed, success]),
            worker,
            FakeOrchestrator(),
            poll_seconds=0,
            ci_timeout_seconds=1,
            max_repairs=2,
        )
        result = delivery.finish(
            repository="owner/repo",
            issue_number=7,
            mission_id="mission-1",
            objective="Fix feature",
            issue_body="Acceptance criteria",
            worker_result={
                "status": "TESTED",
                "branch": "sigma/issue-7",
                "pull_request_url": "https://github.com/owner/repo/pull/8",
            },
        )
        self.assertEqual(result.state, "DONE")
        self.assertEqual(result.repair_attempts, 1)
        self.assertEqual(worker.payloads[0]["existing_branch"], "sigma/issue-7")
        self.assertEqual(
            worker.payloads[0]["pull_request_url"],
            "https://github.com/owner/repo/pull/8",
        )

    def test_unverified_independent_review_blocks_merge(self):
        success = [{
            "id": 1,
            "name": "tests",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "head123",
        }]
        github = FakeGitHub([success])
        delivery = DeliverySupervisor(
            github,
            FakeWorker(),
            FakeOrchestrator(["COMPLETE_WITH_UNVERIFIED_ITEMS"]),
            poll_seconds=0,
            ci_timeout_seconds=1,
        )
        result = delivery.finish(
            repository="owner/repo",
            issue_number=7,
            mission_id="mission-1",
            objective="Fix feature",
            issue_body="Acceptance criteria",
            worker_result={
                "status": "TESTED",
                "branch": "sigma/issue-7",
                "pull_request_url": "https://github.com/owner/repo/pull/8",
            },
        )
        self.assertEqual(result.state, "REVIEW_BLOCKED")
        self.assertEqual(github.merged, [])


if __name__ == "__main__":
    unittest.main()
