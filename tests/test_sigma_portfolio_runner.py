import json
from pathlib import Path
import tempfile
import unittest

from sigma_runtime.portfolio_runner import (
    GitHubClient,
    PortfolioRunner,
    RepositorySnapshot,
    RunnerStore,
    WorkItem,
)


class FakeOrchestrator:
    def run(self, prompt, **kwargs):
        return {"id": "mission-1", "status": "COMPLETE", "prompt": prompt}


class FakeGitHub:
    pass


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

    def test_worker_changed_still_requires_independent_gate(self):
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
            self.assertEqual(result["state"], "WORKER_CHANGED")
            self.assertIn("independent", result["next_gate"])


if __name__ == "__main__":
    unittest.main()
