"""Single-host durable intake. Events wake Sigma; they never grant authority."""
from __future__ import annotations

import hashlib
from contextlib import contextmanager
import hmac
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid

import yaml

from .portfolio_runner import load_registry

REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
EVENTS = {"issues": {"opened", "edited", "labeled", "reopened"},
          "pull_request": {"opened", "synchronize", "closed", "reopened"},
          "workflow_run": {"completed"}, "push": {None}}


class IntakeError(ValueError):
    pass


def project_policy(root: Path) -> dict:
    """Only reviewed local configuration can enable a registry project."""
    registered = {p["repository"] for p in load_registry(root / "projects/registry.yaml")
                  if p["lifecycle"] == "active"}
    config = yaml.safe_load((root / "projects/automation.yaml").read_text(encoding="utf-8"))
    result = {}
    for repo, policy in config.get("projects", {}).items():
        if repo not in registered or not REPOSITORY.fullmatch(repo):
            raise IntakeError("Automation repository is not active in the registry")
        if not isinstance(policy, dict) or type(policy.get("enabled")) is not bool:
            raise IntakeError("Invalid project policy")
        if policy["enabled"]:
            interval = policy.get("interval_seconds", 900)
            if type(interval) is not int or not 300 <= interval <= 604800:
                raise IntakeError("Schedule interval must be 300..604800 seconds")
            if type(policy.get("execute", False)) is not bool:
                raise IntakeError("execute must be boolean")
            result[repo] = {**policy, "interval_seconds": interval}
    return result


class QueueStore:
    """WAL-backed queue with atomic claims, fencing and ambiguous-write quarantine.

    One pending wake-up per repository coalesces bursts. Delivery IDs are retained
    independently, so replay never creates work after a job finishes. Run on local
    disk, not NFS. Schema changes are additive to the existing runtime database.
    """
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS automation_jobs (
                    id TEXT PRIMARY KEY, repository TEXT NOT NULL, trigger TEXT NOT NULL,
                    state TEXT NOT NULL, created REAL NOT NULL, due REAL NOT NULL,
                    attempt INTEGER NOT NULL DEFAULT 0, claim TEXT, heartbeat REAL,
                    dispatch_started INTEGER NOT NULL DEFAULT 0, result TEXT NOT NULL DEFAULT '{}');
                CREATE UNIQUE INDEX IF NOT EXISTS automation_pending_repo
                    ON automation_jobs(repository) WHERE state IN ('QUEUED','RUNNING','RETRY');
                CREATE TABLE IF NOT EXISTS automation_deliveries (
                    id TEXT PRIMARY KEY, digest TEXT NOT NULL, received REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS automation_schedule (
                    repository TEXT PRIMARY KEY, next_due REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS automation_health (
                    name TEXT PRIMARY KEY, heartbeat REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS automation_holds (
                    repository TEXT PRIMARY KEY, job_id TEXT NOT NULL, reason TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS automation_reports (
                    job_id TEXT PRIMARY KEY, sent INTEGER NOT NULL DEFAULT 0,
                    next_attempt REAL NOT NULL DEFAULT 0);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _enqueue(db, repository, trigger, now):
        if db.execute("SELECT 1 FROM automation_holds WHERE repository=?", (repository,)).fetchone():
            return None
        row = db.execute("SELECT id FROM automation_jobs WHERE repository=? AND state IN ('QUEUED','RUNNING','RETRY')", (repository,)).fetchone()
        if row:
            return row[0]
        job_id = str(uuid.uuid4())
        db.execute("INSERT INTO automation_jobs(id,repository,trigger,state,created,due) VALUES(?,?,?,'QUEUED',?,?)",
                   (job_id, repository, trigger, now, now))
        return job_id

    def enqueue(self, repository, trigger="manual", now=None):
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            return self._enqueue(db, repository, trigger, now)

    def delivery(self, delivery, digest, repository, trigger, now=None):
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT digest FROM automation_deliveries WHERE id=?", (delivery,)).fetchone()
            if previous:
                if previous[0] != digest:
                    raise IntakeError("Delivery ID reused with a different body")
                return "duplicate"
            if db.execute("SELECT 1 FROM automation_deliveries WHERE digest=?", (digest,)).fetchone():
                return "duplicate"
            # Bounded storage: operator must archive/reconcile before increasing limit.
            if db.execute("SELECT count(*) FROM automation_deliveries").fetchone()[0] >= 100000:
                raise IntakeError("Delivery retention capacity reached")
            db.execute("INSERT INTO automation_deliveries VALUES(?,?,?)", (delivery, digest, now))
            self._enqueue(db, repository, trigger, now)
            return "accepted"

    def schedule(self, policies, now=None):
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for repo, policy in policies.items():
                row = db.execute("SELECT next_due FROM automation_schedule WHERE repository=?", (repo,)).fetchone()
                if row is None or row[0] <= now:
                    self._enqueue(db, repo, "scheduled", now)
                    db.execute("INSERT INTO automation_schedule VALUES(?,?) ON CONFLICT(repository) DO UPDATE SET next_due=excluded.next_due",
                               (repo, now + policy["interval_seconds"]))

    def claim(self, now=None):
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # Preserve the portfolio runner's global single-worker boundary.
            if db.execute("SELECT 1 FROM automation_jobs WHERE state='RUNNING'").fetchone():
                return None
            row = db.execute("SELECT * FROM automation_jobs WHERE state IN ('QUEUED','RETRY') AND due<=? ORDER BY due,created,id LIMIT 1", (now,)).fetchone()
            if not row:
                return None
            token = str(uuid.uuid4())
            db.execute("UPDATE automation_jobs SET state='RUNNING',claim=?,heartbeat=?,attempt=attempt+1 WHERE id=?", (token, now, row["id"]))
            return dict(db.execute("SELECT * FROM automation_jobs WHERE id=?", (row["id"],)).fetchone())

    def heartbeat(self, job_id, claim, now=None):
        with self.connect() as db:
            return db.execute("UPDATE automation_jobs SET heartbeat=? WHERE id=? AND claim=? AND state='RUNNING'",
                              (time.time() if now is None else now, job_id, claim)).rowcount == 1

    def dispatching(self, job_id, claim):
        with self.connect() as db:
            if db.execute("UPDATE automation_jobs SET dispatch_started=1 WHERE id=? AND claim=? AND state='RUNNING'", (job_id, claim)).rowcount != 1:
                raise IntakeError("Queue claim lost before dispatch")

    def finish(self, job_id, claim, state, result, *, hold=False):
        if state not in {"DONE", "BLOCKED", "UNKNOWN", "DEAD"}:
            raise IntakeError("Invalid terminal queue state")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT repository FROM automation_jobs WHERE id=? AND claim=? AND state='RUNNING'", (job_id, claim)).fetchone()
            if not row:
                return False
            db.execute("UPDATE automation_jobs SET state=?,result=? WHERE id=?", (state, json.dumps(result), job_id))
            if hold:
                db.execute("INSERT OR REPLACE INTO automation_holds VALUES(?,?,?)", (row[0], job_id, state))
            return True

    def fail(self, job_id, claim, error_type, now=None, *, stale_before=None):
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM automation_jobs WHERE id=? AND claim=? AND state='RUNNING'", (job_id, claim)).fetchone()
            if not row:
                return
            if stale_before is not None and row["heartbeat"] >= stale_before:
                return
            state = "UNKNOWN" if row["dispatch_started"] else ("DEAD" if row["attempt"] >= 3 else "RETRY")
            db.execute("UPDATE automation_jobs SET state=?,due=?,result=? WHERE id=?", (state, now + min(3600, 30 * 2 ** row["attempt"]), json.dumps({"error_type": error_type}), job_id))
            if state in {"UNKNOWN", "DEAD"}:
                db.execute("INSERT OR REPLACE INTO automation_holds VALUES(?,?,?)", (row["repository"], job_id, state))

    def recover(self, now=None, stale_seconds=120):
        now = time.time() if now is None else now
        with self.connect() as db:
            rows = db.execute("SELECT id,claim FROM automation_jobs WHERE state='RUNNING' AND heartbeat<?", (now - stale_seconds,)).fetchall()
        for row in rows:
            self.fail(row[0], row[1], "StaleWorker", now, stale_before=now - stale_seconds)

    def pulse(self, name, now=None):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO automation_health VALUES(?,?)", (name, time.time() if now is None else now))

    def status(self):
        with self.connect() as db:
            return {"counts": {r[0]: r[1] for r in db.execute("SELECT state,count(*) FROM automation_jobs GROUP BY state")},
                    "heartbeats": {r[0]: r[1] for r in db.execute("SELECT * FROM automation_health")},
                    "holds": [dict(r) for r in db.execute("SELECT * FROM automation_holds")],
                    "recent": [dict(r) for r in db.execute("SELECT id,repository,state,attempt,result FROM automation_jobs ORDER BY created DESC LIMIT 20")]}

    def publish(self, github, issue_number, now=None):
        """Independent outbox: reporting failures never rerun implementation.

        Only fixed machine states and identifiers leave the private volume. GET
        reconciliation handles a POST whose response was lost. Bounded at-least-
        once reporting may duplicate a comment after the 10-page history horizon.
        """
        now = time.time() if now is None else now
        if not github.allow_write or not github.token:
            return
        if type(issue_number) is not int or issue_number <= 0:
            raise IntakeError("Invalid report issue")
        endpoint = f"/repos/M17z2025/ai-command-center/issues/{issue_number}/comments"
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO automation_reports(job_id) SELECT id FROM automation_jobs WHERE state IN ('DONE','BLOCKED','UNKNOWN','DEAD')")
            rows = db.execute("SELECT j.id,j.repository,j.state,j.attempt FROM automation_jobs j JOIN automation_reports r ON r.job_id=j.id WHERE r.sent=0 AND r.next_attempt<=? ORDER BY j.created LIMIT 1", (now,)).fetchall()
        for row in rows:
            with self.connect() as db:
                db.execute("UPDATE automation_reports SET next_attempt=? WHERE job_id=?", (now + 300, row["id"]))
            marker = f"<!-- sigma-automation:{row['id']} -->"
            found = False
            for page in range(1, 11):
                comments = github.request("GET", endpoint + f"?per_page=100&page={page}")
                if any(marker in (comment.get("body") or "") for comment in comments):
                    found = True
                    break
                if len(comments) < 100:
                    break
            if not found:
                body = (f"{marker}\nSigma automation job `{row['id']}`\n\n"
                        f"Repository: `{row['repository']}`\nQueue state: **{row['state']}**\n"
                        f"Attempts: {row['attempt']}\n\n"
                        "DONE means a runner cycle finished, not product acceptance. "
                        "BLOCKED/UNKNOWN/DEAD require host status inspection and repository-backed reconciliation. "
                        "Independent CI/security/user-test and owner release gates remain in force. "
                        "Private mission content and raw errors are retained only on the host.")
                github.request("POST", endpoint, payload={"body": body})
            with self.connect() as db:
                db.execute("UPDATE automation_reports SET sent=1 WHERE job_id=?", (row["id"],))


def intake(store, policies, secret, body, headers):
    if not secret or len(secret) < 32:
        raise IntakeError("Webhook secret must contain at least 32 characters")
    if len(body) > 262144:
        raise IntakeError("Payload too large")
    signature = headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise IntakeError("Invalid signature")
    delivery = headers.get("X-GitHub-Delivery", "")
    if not re.fullmatch(r"[A-Za-z0-9-]{16,100}", delivery):
        raise IntakeError("Invalid delivery ID")
    event = headers.get("X-GitHub-Event", "")
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise IntakeError("Invalid payload")
    if event == "ping":
        return "pong"
    if event not in EVENTS or payload.get("action") not in EVENTS[event]:
        return "ignored"
    repository = payload.get("repository", {})
    repo = repository.get("full_name") if isinstance(repository, dict) else None
    if repo not in policies:
        raise IntakeError("Repository is not enabled")
    # Never store issue text or trust action/command/authority fields from an event.
    return store.delivery(delivery, hashlib.sha256(body).hexdigest(), repo, "github:" + event)
