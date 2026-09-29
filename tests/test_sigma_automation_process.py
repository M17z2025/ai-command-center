"""Real HTTP and Linux supervisor checks; no model, credentials or live GitHub."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sigma_runtime.automation import QueueStore

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sigma_automation.py"


class ProcessTests(unittest.TestCase):
    def test_real_signed_http_intake_and_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            secret = "test-only-" + "s" * 32
            env = {**os.environ, "SIGMA_WEBHOOK_SECRET": secret, "SIGMA_INTAKE_HOST": "127.0.0.1", "SIGMA_INTAKE_PORT": str(port)}
            db = Path(tmp) / "test.db"
            process = subprocess.Popen([sys.executable, str(SCRIPT), "--db", str(db), "intake"], env=env, cwd=ROOT)
            try:
                for _ in range(100):
                    try:
                        with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                            self.assertEqual(response.status, 200)
                        break
                    except OSError:
                        if process.poll() is not None:
                            self.fail("Intake exited during startup")
                        time.sleep(.05)
                else:
                    self.fail("Intake did not start")
                body = json.dumps({"action": "opened", "repository": {"full_name": "M17z2025/ai-command-center"}}).encode()
                headers = {"X-GitHub-Event": "issues", "X-GitHub-Delivery": "test-delivery-123456789", "X-Hub-Signature-256": "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()}
                request = Request(f"http://127.0.0.1:{port}/github/events", data=body, headers=headers)
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(json.load(response)["status"], "accepted")
                with urlopen(request, timeout=2) as response:
                    self.assertEqual(json.load(response)["status"], "duplicate")
                request = Request(request.full_url, data=body, headers={**headers, "X-Hub-Signature-256": "sha256=wrong"})
                with self.assertRaises(HTTPError) as caught:
                    urlopen(request, timeout=2)
                self.assertEqual(caught.exception.code, 400)
                self.assertEqual(QueueStore(db).status()["counts"], {"QUEUED": 1})
            finally:
                process.terminate()
                process.wait(timeout=10)

    @unittest.skipUnless(sys.platform == "linux", "Linux Docker process/OS-lock boundary")
    def test_supervisor_survives_restart_and_blocks_disabled_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            queue = QueueStore(db)
            ident = queue.enqueue("unregistered/project")
            # Keep configured real project out of the test's scheduling window.
            with queue.connect() as conn:
                conn.execute("INSERT INTO automation_schedule VALUES(?,?)", ("M17z2025/ai-command-center", time.time() + 10000))
            command = [sys.executable, str(SCRIPT), "--db", str(db), "worker"]
            process = subprocess.Popen(command, cwd=ROOT)
            try:
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if queue.status()["counts"].get("BLOCKED") == 1:
                        break
                    time.sleep(.1)
                self.assertEqual(queue.status()["counts"].get("BLOCKED"), 1)
                competing = subprocess.run(command, cwd=ROOT, timeout=5, capture_output=True)
                self.assertNotEqual(competing.returncode, 0)
                self.assertEqual(queue.status()["holds"][0]["job_id"], ident)
            finally:
                process.terminate()
                process.wait(timeout=15)
            restarted = subprocess.Popen(command, cwd=ROOT)
            try:
                time.sleep(.5)
                self.assertIsNone(restarted.poll())
                self.assertEqual(queue.status()["counts"].get("BLOCKED"), 1)
            finally:
                restarted.terminate()
                restarted.wait(timeout=15)
