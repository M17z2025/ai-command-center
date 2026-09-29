#!/usr/bin/env python3
"""VPS entrypoint: signed intake, persistent scheduler and supervised worker."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sigma_runtime.automation import IntakeError, QueueStore, intake, project_policy


def serve(store):
    secret = os.environ.get("SIGMA_WEBHOOK_SECRET", "")
    if len(secret) < 32:
        raise IntakeError("Provision SIGMA_WEBHOOK_SECRET with at least 32 characters")
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def reply(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.reply(200 if self.path == "/healthz" else 404, {"service": "sigma-intake"})

        def do_POST(self):
            if self.path != "/github/events":
                return self.reply(404, {"error": "not found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144 or self.headers.get("Transfer-Encoding"):
                    return self.reply(413, {"error": "invalid body size"})
                body = self.rfile.read(size)
                if len(body) != size:
                    raise IntakeError("Incomplete body")
                status = intake(store, project_policy(ROOT), secret, body, self.headers)
                self.reply(202, {"status": status})
            except (ValueError, TypeError):
                self.reply(400, {"error": "event rejected"})
            except Exception:
                self.reply(503, {"error": "intake unavailable"})

        def log_message(self, *_):
            pass  # Do not log untrusted payloads, headers or secrets.

    HTTPServer((os.getenv("SIGMA_INTAKE_HOST", "0.0.0.0"), int(os.getenv("SIGMA_INTAKE_PORT", "8092"))), Handler).serve_forever()


def child(store, job_id, claim):
    from sigma_runtime.automation_worker import run_job
    with store.connect() as db:
        row = db.execute("SELECT * FROM automation_jobs WHERE id=? AND claim=? AND state='RUNNING'", (job_id, claim)).fetchone()
    if row is None:
        return 2
    try:
        result = run_job(ROOT, store.path, store, dict(row))
        state = result["state"]
        if state == "SKIPPED":
            store.fail(job_id, claim, "RunnerBusy")
        else:
            # A changed PR must enter the independent supervisor, never repeat implementation.
            hold = state in {"WORKER_CHANGED", "BLOCKED"}
            store.finish(job_id, claim, "BLOCKED" if hold else "DONE", result, hold=hold)
    except IntakeError:
        store.finish(job_id, claim, "BLOCKED", {"reason": "Authority or policy gate"}, hold=True)
    except Exception as exc:
        store.fail(job_id, claim, type(exc).__name__)
    return 0


def worker(store):
    # OS lock complements SQLite: a paused supervisor cannot be overtaken by a new
    # process while its child may still be running. Linux Docker is the target.
    import fcntl
    lock = open(str(store.path) + ".automation.lock", "a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    maximum = max(60, int(os.getenv("SIGMA_AUTOMATION_JOB_TIMEOUT", "3600")))
    from sigma_runtime.portfolio_runner import GitHubClient
    reporter = GitHubClient(os.getenv("SIGMA_AUTOMATION_REPORT_TOKEN"),
                            allow_write=os.getenv("SIGMA_AUTOMATION_REPORT_WRITE", "0") == "1",
                            timeout=5)
    report_issue = int(os.getenv("SIGMA_AUTOMATION_REPORT_ISSUE", "97"))
    store.recover()
    while not stopping:
        store.pulse("worker")
        store.recover()
        store.schedule(project_policy(ROOT))
        try:
            store.publish(reporter, report_issue)
        except Exception as exc:
            print("Sigma status publication deferred: " + type(exc).__name__, flush=True)
        job = store.claim()
        if not job:
            time.sleep(2)
            continue
        process = subprocess.Popen([sys.executable, __file__, "--db", str(store.path), "job", "--job-id", job["id"], "--claim", job["claim"]],
                                   start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started = time.monotonic()
        while process.poll() is None and not stopping and time.monotonic() - started < maximum:
            store.pulse("worker")
            if not store.heartbeat(job["id"], job["claim"]):
                break
            time.sleep(2)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        store.fail(job["id"], job["claim"], "WorkerExited")  # fenced no-op if finished
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("SIGMA_RUNTIME_DB", "/data/sigma-runtime.db"))
    parser.add_argument("mode", choices=["intake", "worker", "job", "status", "health", "resume"])
    parser.add_argument("--job-id")
    parser.add_argument("--claim")
    parser.add_argument("--repository")
    parser.add_argument("--evidence", help="Repository-backed reconciliation URL, required to resume a hold")
    args = parser.parse_args()
    store = QueueStore(args.db)
    if args.mode == "intake":
        serve(store)
    elif args.mode == "worker":
        return worker(store)
    elif args.mode == "job":
        return child(store, args.job_id, args.claim)
    elif args.mode == "status":
        print(json.dumps(store.status(), indent=2))
    elif args.mode == "health":
        return 0 if time.time() - store.status()["heartbeats"].get("worker", 0) < 60 else 1
    elif args.mode == "resume":
        if args.repository not in project_policy(ROOT) or not args.evidence or not args.evidence.startswith("https://github.com/"):
            parser.error("An enabled repository and GitHub reconciliation evidence URL are required")
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            held = db.execute("SELECT job_id FROM automation_holds WHERE repository=?", (args.repository,)).fetchone()
            if held:
                row = db.execute("SELECT result FROM automation_jobs WHERE id=?", (held[0],)).fetchone()
                result = json.loads(row[0])
                result["reconciliation"] = args.evidence
                db.execute("UPDATE automation_jobs SET result=? WHERE id=?", (json.dumps(result), held[0]))
                db.execute("DELETE FROM automation_holds WHERE repository=?", (args.repository,))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
