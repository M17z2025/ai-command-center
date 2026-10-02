import json
from pathlib import Path
import tempfile
from datetime import datetime, timedelta, timezone
import unittest

from sigma_runtime.portfolio_runner import (
    GitHubClient,
    PortfolioRunner,
    RepositorySnapshot,
    RunnerStore,
    WorkItem,
    _issue_numbers_with_open_prs,
    _work_item,
)


class FakeOrchestrator:
    def run(self, prompt, **kwargs):
        return {"id": "mission-1", "status": "COMPLETE", "prompt": prompt}


class FakeGitHub:
    allow_write = True

    def __init__(self):
        self.comments = []
        self.closed = []
        self.merges = []

    def pull_request(self, repository, number):
        return {"number": number, "head": {"sha": "abc123"}}

    def workflow_runs_for_head(self, repository, head_sha):
        return [{"id": 1, "head_sha": head_sha, "status": "completed", "conclusion": "success"}]

    def workflow_run_jobs(self, repository, run_id):
        return [{"id": 11, "name": "tests", "conclusion": "success", "steps": []}]

    def pull_request_files(self, repository, number):
        return [{"filename": "app.py", "status": "modified", "additions": 1, "deletions": 0, "patch": "+pass"}]

    def merge_pull_request(self, repository, number, expected_head_sha):
        self.merges.append((repository, number, expected_head_sha))
        return {"merged": True, "sha": "merge123", "message": "merged"}

    def comment_issue(self, repository, number, body):
        self.comments.append((repository, number, body))

    def close_issue(self, repository, number):
        self.closed.append((repository, number))


class FakeWorker:
    def dispatch(self, payload):
        return {
            "status": "CHANGED",
            "evidence": ["worker-proof"],
            "branch": "sigma/issue-7",
            "pull_request_url": "https://github.com/owner/repo/pull/8",
        }


class PortfolioRunnerTests(unittest.TestCase):
    def test_read_only_client_refuses_write_before_network(self):
        client = GitHubClient(token=None, allow_write=False)
        with self.assertRaises(PermissionError):
            client.request("POST", "/repos/a/b/issues", payload={"title": "x"})

    def test_selection_skips_blocked_and_contract_gaps(self):
        blocked = WorkItem(
            "a/blocked", 1, "Blocked", "owner action", 0, (), False, ("blocked",)
        )
        executable = WorkItem(
            "b/ready", 2, "Do work", "acceptance criteria", 1, (), True, ()
        )
        snaps = [
            RepositorySnapshot(
                "A", "a/blocked", "active", "product",
                accessible=True, default_branch="main",
                manifest_present=True, status_present=True,
                work_items=[blocked],
            ),
            RepositorySnapshot(
                "B", "b/ready", "active", "product",
                accessible=True, default_branch="main",
                manifest_present=True, status_present=True,
                work_items=[executable],
            ),
        ]
        self.assertEqual(PortfolioRunner.select(snaps), executable)


    def test_issue_lifecycle_labels_fail_closed(self):
        source_complete = _work_item(
            "owner/repo",
            {
                "number": 10,
                "title": "Already implemented",
                "body": "historical work",
                "labels": [{"name": "source-complete"}],
            },
        )
        owner_blocked = _work_item(
            "owner/repo",
            {
                "number": 11,
                "title": "Needs owner",
                "body": "waiting",
                "labels": [{"name": "blocked-owner"}],
            },
        )
        self.assertFalse(source_complete.executable)
        self.assertEqual(source_complete.state, "SOURCE_COMPLETE")
        self.assertFalse(owner_blocked.executable)
        self.assertEqual(owner_blocked.state, "BLOCKED_OWNER")

    def test_open_pr_issue_reference_is_detected(self):
        pulls = [
            {
                "title": "Sigma worker: implement feature",
                "body": "Automated change. Issue: #17",
            },
            {
                "title": "Fixes #21",
                "body": "",
            },
        ]
        self.assertEqual(_issue_numbers_with_open_prs(pulls), {17, 21})

    def test_runner_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunnerStore(Path(tmp) / "runtime.db")
            cid = store.start("test")
            store.finish(cid, "PLANNED", {"state": "PLANNED"})
            self.assertEqual(store.get(cid)["status"], "PLANNED")
            self.assertEqual(store.list()[0]["payload"]["state"], "PLANNED")

    def test_cycle_plans_without_worker_execution(self):
        selected = WorkItem(
            "owner/repo", 7, "Implement feature", "criteria", 1, (), True, ()
        )
        snap = RepositorySnapshot(
            "Repo", "owner/repo", "active", "product",
            accessible=True, default_branch="main",
            manifest_present=True, status_present=True,
            work_items=[selected],
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = PortfolioRunner(
                FakeGitHub(),
                FakeOrchestrator(),
                RunnerStore(Path(tmp) / "runtime.db"),
            )
            runner.discover = lambda: [snap]
            result = runner.cycle(trigger="test", execute=False)
            self.assertEqual(result["state"], "PLANNED")
            self.assertEqual(result["mission_id"], "mission-1")

    def test_cycle_blocks_if_execution_requested_without_worker(self):
        selected = WorkItem(
            "owner/repo", 7, "Implement feature", "criteria", 1, (), True, ()
        )
        snap = RepositorySnapshot(
            "Repo", "owner/repo", "active", "product",
            accessible=True, default_branch="main",
            manifest_present=True, status_present=True,
            work_items=[selected],
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = PortfolioRunner(
                FakeGitHub(),
                FakeOrchestrator(),
                RunnerStore(Path(tmp) / "runtime.db"),
            )
            runner.discover = lambda: [snap]
            result = runner.cycle(trigger="test", execute=True)
            self.assertEqual(result["state"], "BLOCKED")
            self.assertIn("worker", result["blocker"].lower())

    def test_worker_claim_without_repository_evidence_is_rejected(self):
        class WeakWorker:
            def dispatch(self, payload):
                return {"status": "CHANGED"}

        selected = WorkItem(
            "owner/repo", 7, "Implement feature", "criteria", 1, (), True, ()
        )
        snap = RepositorySnapshot(
            "Repo", "owner/repo", "active", "product",
            accessible=True, default_branch="main",
            manifest_present=True, status_present=True,
            work_items=[selected],
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = PortfolioRunner(
                FakeGitHub(),
                FakeOrchestrator(),
                RunnerStore(Path(tmp) / "runtime.db"),
                worker=WeakWorker(),
            )
            runner.discover = lambda: [snap]
            result = runner.cycle(trigger="test", execute=True)
            self.assertEqual(result["state"], "BLOCKED")
            self.assertIn("runner_rejection", result["worker"])

    def test_worker_pr_completes_delivery_after_independent_gates(self):
        selected = WorkItem(
            "owner/repo", 7, "Implement feature", "criteria", 1, (), True, ()
        )
        snap = RepositorySnapshot(
            "Repo", "owner/repo", "active", "product",
            accessible=True, default_branch="main",
            manifest_present=True, status_present=True,
            work_items=[selected],
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = PortfolioRunner(
                FakeGitHub(),
                FakeOrchestrator(),
                RunnerStore(Path(tmp) / "runtime.db"),
                worker=FakeWorker(),
            )
            runner.discover = lambda: [snap]
            result = runner.cycle(trigger="test", execute=True)
            self.assertEqual(result["state"], "DONE")
            self.assertEqual(result["next_gate"], "next executable portfolio task")
            self.assertEqual(result["delivery"]["head_sha"], "abc123")
            self.assertEqual(result["delivery"]["merge_sha"], "merge123")

    def test_second_cycle_is_skipped_when_lease_is_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunnerStore(Path(tmp) / "runtime.db")
            self.assertTrue(store.acquire_lease("active-cycle", 1800))
            runner = PortfolioRunner(
                FakeGitHub(),
                FakeOrchestrator(),
                store,
            )
            result = runner.cycle(trigger="test", execute=False)
            self.assertEqual(result["state"], "SKIPPED")
            self.assertEqual(
                result["active_lease"]["owner_id"],
                "active-cycle",
            )

    def test_stale_running_cycle_is_marked_stale_and_lock_released(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunnerStore(Path(tmp) / "runtime.db")
            cid = store.start("test")
            self.assertTrue(store.acquire_lease(cid, 1800))
            old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            with store._connect() as conn:
                conn.execute(
                    "UPDATE runner_cycles SET heartbeat_at=? WHERE id=?",
                    (old, cid),
                )
            stale = store.mark_stale_running(1800)
            self.assertEqual(stale, [cid])
            self.assertEqual(store.get(cid)["status"], "STALE")
            self.assertIsNone(store.active_lease())

    def test_fresh_running_cycle_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunnerStore(Path(tmp) / "runtime.db")
            cid = store.start("test")
            self.assertTrue(store.acquire_lease(cid, 1800))
            stale = store.mark_stale_running(1800)
            self.assertEqual(stale, [])
            self.assertEqual(store.get(cid)["status"], "RUNNING")
            self.assertEqual(store.active_lease()["owner_id"], cid)

    def test_lease_is_released_after_successful_cycle(self):
        selected = WorkItem(
            "owner/repo", 7, "Implement feature", "criteria", 1, (), True, ()
        )
        snap = RepositorySnapshot(
            "Repo", "owner/repo", "active", "product",
            accessible=True, default_branch="main",
            manifest_present=True, status_present=True,
            work_items=[selected],
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = RunnerStore(Path(tmp) / "runtime.db")
            runner = PortfolioRunner(
                FakeGitHub(),
                FakeOrchestrator(),
                store,
            )
            runner.discover = lambda: [snap]
            result = runner.cycle(trigger="test", execute=False)
            self.assertEqual(result["state"], "PLANNED")
            self.assertIsNone(store.active_lease())

    def test_lease_is_released_after_failed_cycle(self):
        class FailingOrchestrator:
            def run(self, prompt, **kwargs):
                raise RuntimeError("boom")

        selected = WorkItem(
            "owner/repo", 7, "Implement feature", "criteria", 1, (), True, ()
        )
        snap = RepositorySnapshot(
            "Repo", "owner/repo", "active", "product",
            accessible=True, default_branch="main",
            manifest_present=True, status_present=True,
            work_items=[selected],
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = RunnerStore(Path(tmp) / "runtime.db")
            runner = PortfolioRunner(
                FakeGitHub(),
                FailingOrchestrator(),
                store,
            )
            runner.discover = lambda: [snap]
            with self.assertRaises(RuntimeError):
                runner.cycle(trigger="test", execute=False)
            self.assertIsNone(store.active_lease())
            self.assertEqual(store.list()[0]["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
