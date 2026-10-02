"""Autonomous portfolio runner for Sigma-managed repositories.

The runner is evidence-driven and fail-closed. It can discover work without write
authority. Mutations and worker execution require explicit runtime configuration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
import base64
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
import uuid

import yaml

from .orchestrator import SigmaOrchestrator
from .delivery_supervisor import DeliverySupervisor


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunnerError(RuntimeError):
    pass


class GitHubClient:
    """Minimal GitHub REST client with explicit read/write authority separation."""

    def __init__(
        self,
        token: str | None = None,
        *,
        allow_write: bool = False,
        api_root: str = "https://api.github.com",
        timeout: int = 30,
    ) -> None:
        self.token = token
        self.allow_write = allow_write
        self.api_root = api_root.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        method = method.upper()
        if method != "GET" and not self.allow_write:
            raise PermissionError(f"Sigma runner write disabled; refused HTTP {method}")
        if method != "GET" and not self.token:
            raise PermissionError("Sigma runner write requires SIGMA_GITHUB_TOKEN")

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "sigma-portfolio-runner/1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        req = Request(
            f"{self.api_root}{endpoint}",
            headers=headers,
            data=data,
            method=method,
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            raise RunnerError(
                f"GitHub {method} {endpoint} failed with HTTP {exc.code}: {detail}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RunnerError(f"GitHub {method} {endpoint} failed: {exc}") from exc

    def repository(self, repository: str) -> dict[str, Any]:
        return self.request("GET", f"/repos/{repository}")

    def file_text(self, repository: str, path: str, ref: str) -> str | None:
        encoded = quote(path, safe="/")
        query = urlencode({"ref": ref})
        try:
            data = self.request(
                "GET", f"/repos/{repository}/contents/{encoded}?{query}"
            )
        except RunnerError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise
        content = data.get("content")
        if not isinstance(content, str):
            return None
        return base64.b64decode(content).decode("utf-8")

    def open_issues(self, repository: str) -> list[dict[str, Any]]:
        data = self.request(
            "GET", f"/repos/{repository}/issues?state=open&per_page=100"
        )
        return [item for item in data if "pull_request" not in item]

    def open_pulls(self, repository: str) -> list[dict[str, Any]]:
        return self.request("GET", f"/repos/{repository}/pulls?state=open&per_page=100")

    def latest_commit(self, repository: str, branch: str) -> dict[str, Any] | None:
        data = self.request(
            "GET", f"/repos/{repository}/commits?sha={quote(branch)}&per_page=1"
        )
        return data[0] if data else None

    def pull_request(self, repository: str, number: int) -> dict[str, Any]:
        return self.request("GET", f"/repos/{repository}/pulls/{int(number)}")

    def workflow_runs_for_head(
        self, repository: str, head_sha: str
    ) -> list[dict[str, Any]]:
        query = urlencode({"head_sha": head_sha, "per_page": 100})
        data = self.request(
            "GET", f"/repos/{repository}/actions/runs?{query}"
        )
        runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
        return [item for item in runs if item.get("head_sha") == head_sha]

    def workflow_run_jobs(
        self, repository: str, run_id: int
    ) -> list[dict[str, Any]]:
        data = self.request(
            "GET", f"/repos/{repository}/actions/runs/{int(run_id)}/jobs?per_page=100"
        )
        return data.get("jobs", []) if isinstance(data, dict) else []

    def pull_request_files(
        self, repository: str, number: int
    ) -> list[dict[str, Any]]:
        data = self.request(
            "GET", f"/repos/{repository}/pulls/{int(number)}/files?per_page=100"
        )
        return data if isinstance(data, list) else []

    def merge_pull_request(
        self, repository: str, number: int, expected_head_sha: str
    ) -> dict[str, Any]:
        return self.request(
            "PUT",
            f"/repos/{repository}/pulls/{int(number)}/merge",
            payload={
                "sha": expected_head_sha,
                "merge_method": "squash",
            },
        )

    def comment_issue(self, repository: str, number: int, body: str) -> None:
        self.request(
            "POST",
            f"/repos/{repository}/issues/{int(number)}/comments",
            payload={"body": body},
        )

    def close_issue(self, repository: str, number: int) -> None:
        self.request(
            "PATCH",
            f"/repos/{repository}/issues/{int(number)}",
            payload={"state": "closed", "state_reason": "completed"},
        )

    def create_issue(
        self, repository: str, title: str, body: str, labels: list[str] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        return self.request("POST", f"/repos/{repository}/issues", payload=payload)


@dataclass(frozen=True)
class WorkItem:
    repository: str
    issue_number: int
    title: str
    body: str
    priority: int
    labels: tuple[str, ...]
    executable: bool
    blockers: tuple[str, ...] = ()


@dataclass
class RepositorySnapshot:
    name: str
    repository: str
    lifecycle: str
    category: str
    accessible: bool = False
    default_branch: str = ""
    manifest_present: bool = False
    status_present: bool = False
    status_text: str = ""
    latest_commit_sha: str = ""
    open_prs: int = 0
    work_items: list[WorkItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def state(self) -> str:
        if not self.accessible:
            return "INACCESSIBLE"
        if not self.manifest_present or not self.status_present:
            return "CONTRACT_GAP"
        if self.errors:
            return "PARTIAL"
        return "DISCOVERED"


class WorkerGateway(Protocol):
    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class HTTPWorkerGateway:
    """Generic private worker service interface.

    The endpoint is deliberately generic so OpenHands or another governed worker
    can sit behind it without making the runner depend on one framework.
    """

    def __init__(self, endpoint: str, token: str | None = None, timeout: int = 900):
        if not endpoint.startswith(("http://", "https://")):
            raise RunnerError("SIGMA_WORKER_ENDPOINT must be absolute HTTP(S)")
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "sigma-portfolio-runner/1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RunnerError(f"Worker dispatch failed: {exc}") from exc


class RunnerStore:
    """Durable portfolio-cycle state in the same private SQLite volume."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runner_cycles (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  completed_at TEXT,
                  trigger TEXT NOT NULL,
                  status TEXT NOT NULL,
                  selected_repository TEXT,
                  selected_issue INTEGER,
                  mission_id TEXT,
                  payload_json TEXT NOT NULL,
                  heartbeat_at TEXT
                );
                CREATE TABLE IF NOT EXISTS runner_leases (
                  name TEXT PRIMARY KEY,
                  owner_id TEXT NOT NULL,
                  acquired_at TEXT NOT NULL,
                  heartbeat_at TEXT NOT NULL,
                  expires_at TEXT NOT NULL
                );
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(runner_cycles)").fetchall()
            }
            if "heartbeat_at" not in columns:
                conn.execute("ALTER TABLE runner_cycles ADD COLUMN heartbeat_at TEXT")

    def start(
        self,
        trigger: str,
        *,
        cycle_id: str | None = None,
        status: str = "RUNNING",
        payload: dict[str, Any] | None = None,
    ) -> str:
        cycle_id = cycle_id or str(uuid.uuid4())
        now = utcnow()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO runner_cycles
                (id, created_at, trigger, status, payload_json, heartbeat_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cycle_id,
                    now,
                    trigger,
                    status,
                    json.dumps(payload or {}),
                    now,
                ),
            )
        return cycle_id

    def heartbeat(self, cycle_id: str) -> None:
        now = utcnow()
        with self._connect() as conn:
            conn.execute(
                "UPDATE runner_cycles SET heartbeat_at=? WHERE id=? AND status='RUNNING'",
                (now, cycle_id),
            )
            conn.execute(
                """UPDATE runner_leases
                SET heartbeat_at=?
                WHERE name='portfolio' AND owner_id=?""",
                (now, cycle_id),
            )

    def acquire_lease(self, owner_id: str, ttl_seconds: int) -> bool:
        ttl_seconds = max(60, int(ttl_seconds))
        now_dt = datetime.now(timezone.utc)
        expires = (now_dt + timedelta(seconds=ttl_seconds)).isoformat()
        now = now_dt.isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT owner_id, expires_at FROM runner_leases WHERE name='portfolio'"
            ).fetchone()
            if row:
                try:
                    expires_at = datetime.fromisoformat(row["expires_at"])
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    expires_at = now_dt - timedelta(seconds=1)
                if row["owner_id"] != owner_id and expires_at > now_dt:
                    return False
            conn.execute(
                """INSERT INTO runner_leases
                (name, owner_id, acquired_at, heartbeat_at, expires_at)
                VALUES ('portfolio', ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                  owner_id=excluded.owner_id,
                  acquired_at=excluded.acquired_at,
                  heartbeat_at=excluded.heartbeat_at,
                  expires_at=excluded.expires_at""",
                (owner_id, now, now, expires),
            )
        return True

    def renew_lease(self, owner_id: str, ttl_seconds: int) -> bool:
        ttl_seconds = max(60, int(ttl_seconds))
        now_dt = datetime.now(timezone.utc)
        expires = (now_dt + timedelta(seconds=ttl_seconds)).isoformat()
        now = now_dt.isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """UPDATE runner_leases
                SET heartbeat_at=?, expires_at=?
                WHERE name='portfolio' AND owner_id=?""",
                (now, expires, owner_id),
            )
        return cursor.rowcount == 1

    def release_lease(self, owner_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM runner_leases WHERE name='portfolio' AND owner_id=?",
                (owner_id,),
            )

    def active_lease(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT name, owner_id, acquired_at, heartbeat_at, expires_at
                FROM runner_leases WHERE name='portfolio'"""
            ).fetchone()
        return dict(row) if row else None

    def mark_stale_running(self, older_than_seconds: int) -> list[str]:
        threshold = max(60, int(older_than_seconds))
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold)
        stale_ids: list[str] = []
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, created_at, heartbeat_at, payload_json
                FROM runner_cycles WHERE status='RUNNING'"""
            ).fetchall()
            for row in rows:
                raw = row["heartbeat_at"] or row["created_at"]
                try:
                    heartbeat = datetime.fromisoformat(raw)
                    if heartbeat.tzinfo is None:
                        heartbeat = heartbeat.replace(tzinfo=timezone.utc)
                except ValueError:
                    heartbeat = cutoff - timedelta(seconds=1)
                if heartbeat >= cutoff:
                    continue
                payload = json.loads(row["payload_json"] or "{}")
                payload["stale_reason"] = "heartbeat threshold exceeded"
                payload["stale_threshold_seconds"] = threshold
                now = utcnow()
                conn.execute(
                    """UPDATE runner_cycles
                    SET status='STALE', completed_at=?, payload_json=?
                    WHERE id=?""",
                    (now, json.dumps(payload), row["id"]),
                )
                conn.execute(
                    "DELETE FROM runner_leases WHERE name='portfolio' AND owner_id=?",
                    (row["id"],),
                )
                stale_ids.append(row["id"])
        return stale_ids

    def finish(
        self,
        cycle_id: str,
        status: str,
        payload: dict[str, Any],
        *,
        repository: str | None = None,
        issue_number: int | None = None,
        mission_id: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE runner_cycles SET completed_at=?, status=?,
                selected_repository=?, selected_issue=?, mission_id=?, payload_json=?
                WHERE id=?""",
                (
                    utcnow(),
                    status,
                    repository,
                    issue_number,
                    mission_id,
                    json.dumps(payload),
                    cycle_id,
                ),
            )

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM runner_cycles ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json") or "{}")
            result.append(item)
        return result

    def get(self, cycle_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM runner_cycles WHERE id=?", (cycle_id,)
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json") or "{}")
        return item

    def status_summary(self) -> dict[str, Any]:
        with self._connect() as conn:
            counts = {
                row["status"]: row["count"]
                for row in conn.execute(
                    """SELECT status, COUNT(*) AS count
                    FROM runner_cycles GROUP BY status"""
                ).fetchall()
            }
        return {
            "active_lease": self.active_lease(),
            "counts": counts,
            "recent_cycles": self.list(limit=10),
        }


_PRIORITY_RE = re.compile(r"\bP([0-3])\b", re.IGNORECASE)
_BLOCK_WORDS = (
    "blocked",
    "owner action",
    "owner-gated",
    "credential required",
    "secret required",
    "awaiting legal",
    "external approval",
)


def _priority(issue: dict[str, Any]) -> int:
    labels = [str(item.get("name", "")).lower() for item in issue.get("labels", [])]
    for index, name in enumerate(("p0", "priority:p0", "critical")):
        if name in labels:
            return 0
    for name in ("p1", "priority:p1", "high"):
        if name in labels:
            return 1
    for name in ("p2", "priority:p2", "medium"):
        if name in labels:
            return 2
    match = _PRIORITY_RE.search(issue.get("title", ""))
    return int(match.group(1)) if match else 3


def _work_item(repository: str, issue: dict[str, Any]) -> WorkItem:
    body = issue.get("body") or ""
    title = issue.get("title") or ""
    labels = tuple(
        str(item.get("name", "")) for item in issue.get("labels", []) if item.get("name")
    )
    combined = f"{title}\n{body}".lower()
    blockers = [word for word in _BLOCK_WORDS if word in combined]
    has_objective = bool(body.strip()) or bool(title.strip())
    executable = has_objective and not blockers
    return WorkItem(
        repository=repository,
        issue_number=int(issue["number"]),
        title=title,
        body=body,
        priority=_priority(issue),
        labels=labels,
        executable=executable,
        blockers=tuple(blockers),
    )


def load_registry(path: str | Path) -> list[dict[str, str]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    projects = data.get("projects", []) if isinstance(data, dict) else []
    result: list[dict[str, str]] = []
    for item in projects:
        repository = str(item.get("repository", ""))
        if repository.count("/") != 1:
            continue
        result.append(
            {
                "name": str(item.get("name", repository)),
                "repository": repository,
                "lifecycle": str(item.get("lifecycle", "")),
                "category": str(item.get("category", "")),
            }
        )
    return result


class PortfolioRunner:
    def __init__(
        self,
        github: GitHubClient,
        orchestrator: SigmaOrchestrator,
        store: RunnerStore,
        *,
        registry_path: str | Path = "projects/registry.yaml",
        worker: WorkerGateway | None = None,
        lease_ttl_seconds: int = 1800,
        stale_after_seconds: int = 1800,
    ) -> None:
        self.github = github
        self.orchestrator = orchestrator
        self.store = store
        self.registry_path = Path(registry_path)
        self.worker = worker
        self.lease_ttl_seconds = max(60, int(lease_ttl_seconds))
        self.stale_after_seconds = max(60, int(stale_after_seconds))

    def discover(self) -> list[RepositorySnapshot]:
        snapshots = []
        for project in load_registry(self.registry_path):
            snapshots.append(self._discover_one(project))
        return snapshots

    def _discover_one(self, project: dict[str, str]) -> RepositorySnapshot:
        snap = RepositorySnapshot(**project)
        try:
            repo = self.github.repository(snap.repository)
            snap.accessible = True
            snap.default_branch = repo.get("default_branch") or "main"
            snap.manifest_present = (
                self.github.file_text(
                    snap.repository, ".sigma/project.yaml", snap.default_branch
                )
                is not None
            )
            status = self.github.file_text(
                snap.repository, "PROJECT_STATUS.md", snap.default_branch
            )
            snap.status_present = status is not None
            snap.status_text = status or ""
            snap.open_prs = len(self.github.open_pulls(snap.repository))
            latest = self.github.latest_commit(snap.repository, snap.default_branch)
            if latest:
                snap.latest_commit_sha = latest.get("sha", "")
            snap.work_items = [
                _work_item(snap.repository, issue)
                for issue in self.github.open_issues(snap.repository)
            ]
        except Exception as exc:
            snap.errors.append(str(exc))
        return snap

    @staticmethod
    def select(snapshots: list[RepositorySnapshot]) -> WorkItem | None:
        candidates: list[WorkItem] = []
        for snap in snapshots:
            if snap.state != "DISCOVERED":
                continue
            candidates.extend(item for item in snap.work_items if item.executable)
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item.priority, item.repository, item.issue_number))
        return candidates[0]

    def cycle(self, *, trigger: str = "manual", execute: bool = False) -> dict[str, Any]:
        self.store.mark_stale_running(self.stale_after_seconds)
        cycle_id = str(uuid.uuid4())

        if not self.store.acquire_lease(cycle_id, self.lease_ttl_seconds):
            active = self.store.active_lease()
            payload = {
                "cycle_id": cycle_id,
                "state": "SKIPPED",
                "reason": "Another portfolio runner cycle already holds the active lease.",
                "active_lease": active,
            }
            self.store.start(
                trigger,
                cycle_id=cycle_id,
                status="SKIPPED",
                payload=payload,
            )
            self.store.finish(cycle_id, "SKIPPED", payload)
            return payload

        self.store.start(trigger, cycle_id=cycle_id)
        try:
            snapshots = self.discover()
            self.store.heartbeat(cycle_id)
            self.store.renew_lease(cycle_id, self.lease_ttl_seconds)

            selected = self.select(snapshots)
            discovery_summary = {
                "repositories": len(snapshots),
                "discovered": sum(
                    1 for item in snapshots if item.state == "DISCOVERED"
                ),
                "contract_gaps": sum(
                    1 for item in snapshots if item.state == "CONTRACT_GAP"
                ),
                "inaccessible": sum(
                    1 for item in snapshots if item.state == "INACCESSIBLE"
                ),
            }

            if selected is None:
                payload = {
                    "cycle_id": cycle_id,
                    "state": "NO_EXECUTABLE_WORK",
                    "discovery": discovery_summary,
                }
                self.store.finish(cycle_id, "IDLE", payload)
                return payload

            prompt = (
                f"Sigma autonomous portfolio runner selected GitHub issue "
                f"{selected.repository}#{selected.issue_number}: {selected.title}\n\n"
                f"{selected.body}\n\n"
                "Produce an executable development plan that obeys repository contracts, "
                "security gates, branch/PR workflow, independent verification and Sigma "
                "User Tester requirements. Do not claim implementation occurred unless "
                "worker/repository evidence proves it."
            )
            mission = self.orchestrator.run(
                prompt,
                evidence=[
                    {
                        "id": "runner-selection",
                        "source": (
                            f"github:{selected.repository}#{selected.issue_number}"
                        ),
                        "content": json.dumps(asdict(selected)),
                    }
                ],
                requested_by="sigma-portfolio-runner",
                max_cycles=2,
            )
            mission_id = mission.get("id")
            self.store.heartbeat(cycle_id)
            self.store.renew_lease(cycle_id, self.lease_ttl_seconds)

            if not execute:
                payload = {
                    "cycle_id": cycle_id,
                    "state": "PLANNED",
                    "selected": asdict(selected),
                    "mission_id": mission_id,
                    "discovery": discovery_summary,
                    "execution": "disabled",
                }
                self.store.finish(
                    cycle_id,
                    "PLANNED",
                    payload,
                    repository=selected.repository,
                    issue_number=selected.issue_number,
                    mission_id=mission_id,
                )
                return payload

            if self.worker is None:
                payload = {
                    "cycle_id": cycle_id,
                    "state": "BLOCKED",
                    "selected": asdict(selected),
                    "mission_id": mission_id,
                    "discovery": discovery_summary,
                    "blocker": "No governed worker endpoint configured.",
                }
                self.store.finish(
                    cycle_id,
                    "BLOCKED",
                    payload,
                    repository=selected.repository,
                    issue_number=selected.issue_number,
                    mission_id=mission_id,
                )
                return payload

            worker_result = self.worker.dispatch(
                {
                    "mission_id": mission_id,
                    "repository": selected.repository,
                    "issue_number": selected.issue_number,
                    "objective": selected.title,
                    "issue_body": selected.body,
                    "sigma_mission": mission,
                    "authority": {
                        "production_release": False,
                        "destructive_actions": False,
                        "paid_spend": False,
                        "direct_main_push": False,
                    },
                }
            )
            self.store.heartbeat(cycle_id)
            self.store.renew_lease(cycle_id, self.lease_ttl_seconds)

            worker_status = str(worker_result.get("status", "BLOCKED")).upper()
            repository_evidence = bool(
                worker_result.get("branch") and worker_result.get("pull_request_url")
            )
            final_status = (
                "WORKER_CHANGED"
                if worker_status in {"CHANGED", "TESTED"} and repository_evidence
                else "BLOCKED"
            )
            if worker_status in {"CHANGED", "TESTED"} and not repository_evidence:
                worker_result = dict(worker_result)
                worker_result["runner_rejection"] = (
                    "Worker claimed repository change without branch and "
                    "pull_request_url evidence."
                )

            delivery_result = None
            if final_status == "WORKER_CHANGED":
                delivery = DeliverySupervisor(
                    self.github,
                    self.worker,
                    self.orchestrator,
                    poll_seconds=float(
                        os.getenv("SIGMA_RUNNER_CI_POLL_SECONDS", "10")
                    ),
                    ci_timeout_seconds=int(
                        os.getenv("SIGMA_RUNNER_CI_TIMEOUT_SECONDS", "900")
                    ),
                    max_repairs=int(
                        os.getenv("SIGMA_RUNNER_MAX_REPAIRS", "2")
                    ),
                )
                delivery_result = delivery.finish(
                    repository=selected.repository,
                    issue_number=selected.issue_number,
                    mission_id=str(mission_id or cycle_id),
                    objective=selected.title,
                    issue_body=selected.body,
                    worker_result=worker_result,
                )
                final_status = delivery_result.state

            payload = {
                "cycle_id": cycle_id,
                "state": final_status,
                "selected": asdict(selected),
                "mission_id": mission_id,
                "discovery": discovery_summary,
                "worker": worker_result,
                "delivery": (
                    delivery_result.as_dict()
                    if delivery_result is not None
                    else None
                ),
                "next_gate": (
                    "next executable portfolio task"
                    if final_status == "DONE"
                    else (
                        delivery_result.blocker
                        if delivery_result is not None
                        else "worker blocker resolution"
                    )
                ),
            }
            self.store.finish(
                cycle_id,
                final_status,
                payload,
                repository=selected.repository,
                issue_number=selected.issue_number,
                mission_id=mission_id,
            )
            return payload
        except Exception as exc:
            payload = {
                "cycle_id": cycle_id,
                "state": "FAILED",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            self.store.finish(cycle_id, "FAILED", payload)
            raise
        finally:
            self.store.release_lease(cycle_id)


def runner_from_env(
    orchestrator: SigmaOrchestrator,
    db_path: str | Path,
    *,
    registry_path: str | Path = "projects/registry.yaml",
) -> PortfolioRunner:
    allow_write = os.getenv("SIGMA_RUNNER_ALLOW_WRITE", "0") == "1"
    github = GitHubClient(
        os.getenv("SIGMA_GITHUB_TOKEN") or None,
        allow_write=allow_write,
    )
    worker = None
    endpoint = os.getenv("SIGMA_WORKER_ENDPOINT", "").strip()
    if endpoint:
        worker = HTTPWorkerGateway(
            endpoint,
            os.getenv("SIGMA_WORKER_TOKEN") or None,
            timeout=int(os.getenv("SIGMA_WORKER_TIMEOUT_SECONDS", "900")),
        )
    return PortfolioRunner(
        github,
        orchestrator,
        RunnerStore(db_path),
        registry_path=registry_path,
        worker=worker,
        lease_ttl_seconds=int(os.getenv("SIGMA_RUNNER_LEASE_TTL_SECONDS", "1800")),
        stale_after_seconds=int(os.getenv("SIGMA_RUNNER_STALE_AFTER_SECONDS", "1800")),
    )
