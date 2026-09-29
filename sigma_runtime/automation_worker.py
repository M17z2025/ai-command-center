"""Per-project adapter around the existing runner; no new release authority."""
from __future__ import annotations

import os
from pathlib import Path
import threading

import yaml

from .automation import IntakeError, project_policy
from .portfolio_runner import PortfolioRunner, RunnerStore, load_registry, runner_from_env


class LiveRunnerStore(RunnerStore):
    """Keep the existing runner lease alive while inference/HTTP calls block."""
    def acquire_lease(self, owner_id, ttl_seconds):
        if not super().acquire_lease(owner_id, ttl_seconds):
            return False
        self.stop = threading.Event()
        def beat():
            while not self.stop.wait(min(20, ttl_seconds / 3)):
                try:
                    self.heartbeat(owner_id)
                    if not self.renew_lease(owner_id, ttl_seconds):
                        os._exit(71)
                except Exception:
                    # Lost ownership cannot safely continue side-effecting work.
                    os._exit(71)
        self.thread = threading.Thread(target=beat, daemon=True)
        self.thread.start()
        return True

    def release_lease(self, owner_id):
        if hasattr(self, "stop"):
            self.stop.set()
            self.thread.join(timeout=25)
        super().release_lease(owner_id)


class ProjectRunner(PortfolioRunner):
    def discover(self):
        project = next(p for p in load_registry(self.registry_path)
                       if p["repository"] == self.project_repository and p["lifecycle"] == "active")
        return [self._discover_one(project)]

    def select(self, snapshots):
        # Existing PR work belongs to PR #96's supervisor. Avoid competing writes.
        for snap in snapshots:
            if snap.open_prs:
                return None
            if self.project_execute:
                snap.work_items = [w for w in snap.work_items if "sigma:autonomous" in w.labels]
        return super().select(snapshots)


class GuardedGateway:
    def __init__(self, delegate, github, queue, job, root):
        self.delegate, self.github, self.queue, self.job, self.root = delegate, github, queue, job, root

    def dispatch(self, payload):
        repo = self.job["repository"]
        policies = project_policy(self.root)
        if not policies.get(repo, {}).get("execute") or os.getenv("SIGMA_RUNNER_EXECUTE") != "1":
            raise IntakeError("Project execution is disabled")
        if not self.github.allow_write or not self.github.token:
            raise IntakeError("Runner write authority is disabled")
        if payload.get("repository") != repo:
            raise IntakeError("Cross-project worker dispatch refused")
        metadata = self.github.repository(repo)
        branch = metadata.get("default_branch", "main")
        head = self.github.latest_commit(repo, branch)["sha"]
        manifest = yaml.safe_load(self.github.file_text(repo, ".sigma/project.yaml", head) or "")
        if not isinstance(manifest, dict) or manifest.get("project", {}).get("repository") != repo:
            raise IntakeError("Invalid project contract")
        automation = manifest.get("automation", {})
        if automation.get("enabled") is not True or automation.get("execution") != "branch_pr":
            raise IntakeError("Product contract does not authorise branch/PR automation")
        if automation.get("owner_gates") != "preserve":
            raise IntakeError("Product contract must preserve owner gates")
        if not self.github.file_text(repo, "AGENTS.md", head) or not self.github.file_text(repo, "PROJECT_STATUS.md", head):
            raise IntakeError("Project authority/status documents missing")
        issue = self.github.request("GET", f"/repos/{repo}/issues/{int(payload['issue_number'])}")
        labels = {v.get("name") for v in issue.get("labels", [])}
        if issue.get("state") != "open" or "sigma:autonomous" not in labels:
            raise IntakeError("Issue is not opted in")
        if issue.get("title") != payload.get("objective") or (issue.get("body") or "") != payload.get("issue_body"):
            raise IntakeError("Issue changed during planning; replan before dispatch")
        if self.github.open_pulls(repo):
            raise IntakeError("Existing PR requires supervision before new work")
        payload["authority"] = {"production_release": False, "destructive_actions": False,
                                "paid_spend": False, "direct_main_push": False,
                                "secret_management": False, "security_control_reduction": False}
        payload["automation_job_id"] = self.job["id"]
        payload["source_sha"] = head
        # Commit dispatch intent BEFORE HTTP: crashes/timeouts now require reconciliation.
        self.queue.dispatching(self.job["id"], self.job["claim"])
        return self.delegate.dispatch(payload)


def run_job(root, db_path, queue, job):
    from . import MeshConfig, MissionRouter, MissionStore, SigmaOrchestrator
    from .provider import provider_from_env
    from .memory import memory_from_env
    from .gstack import advisory_context

    root = Path(root)
    policy = project_policy(root).get(job["repository"])
    if policy is None:
        return {"state": "BLOCKED", "reason": "Project disabled"}
    execute = policy.get("execute", False) and os.getenv("SIGMA_RUNNER_EXECUTE", "0") == "1"
    config = MeshConfig(root)
    mesh = SigmaOrchestrator(config, MissionRouter(config), provider_from_env(), MissionStore(db_path), memory_from_env())
    context = advisory_context(root, enabled=policy.get("gstack") is True,
                               max_chars=4000,
                               cache_dir=Path(os.getenv("SIGMA_GSTACK_CACHE", str(root / ".sigma/gstack"))))
    if context.get("enabled"):
        original = mesh.run
        def with_reference(prompt, **kwargs):
            return original(prompt + "\n\n" + context["text"], **kwargs)
        mesh.run = with_reference
    original_runner = runner_from_env(mesh, db_path, registry_path=root / "projects/registry.yaml")
    runner = ProjectRunner(original_runner.github, mesh, LiveRunnerStore(db_path),
                           registry_path=original_runner.registry_path)
    runner.project_repository = job["repository"]
    runner.project_execute = execute
    if original_runner.worker:
        runner.worker = GuardedGateway(original_runner.worker, runner.github, queue, job, root)
    result = runner.cycle(trigger=job["trigger"], execute=execute)
    # Persist only machine identity, not private model text, in the queue summary.
    summary = {"cycle_id": result["cycle_id"], "state": result["state"],
               "gstack_revision": context.get("revision"),
               "gstack_sources": context.get("sources", []),
               "next_gate": "Independent exact-head CI, security and applicable user tests"}
    if result.get("selected"):
        summary["issue_number"] = result["selected"]["issue_number"]
    return summary
