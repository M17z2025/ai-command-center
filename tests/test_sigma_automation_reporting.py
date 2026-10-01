import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import unittest

from sigma_runtime.automation import QueueStore, intake


class Reporter:
    allow_write = True
    token = "test-only"
    def __init__(self):
        self.comments = []
        self.calls = []
        self.lose_response = False

    def request(self, method, endpoint, payload=None):
        self.calls.append(method)
        if method == "GET":
            return self.comments
        self.comments.append(payload)
        if self.lose_response:
            self.lose_response = False
            raise TimeoutError("response lost after server accepted")
        return {"id": 1}


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.queue = QueueStore(Path(self.tmp.name) / "queue.db")

    def completed(self):
        self.queue.enqueue("owner/repo", now=10)
        job = self.queue.claim(now=10)
        self.queue.finish(job["id"], job["claim"], "DONE", {"private": "NEVER_PUBLISH_THIS", "state": "PLANNED"})
        return job

    def test_lost_post_response_reconciles_without_duplicate_or_rerun(self):
        job = self.completed()
        github = Reporter()
        github.lose_response = True
        with self.assertRaises(TimeoutError):
            self.queue.publish(github, 97, now=20)
        self.queue.publish(github, 97, now=21)
        self.assertEqual(len(github.comments), 1)
        self.queue.publish(github, 97, now=321)
        self.assertEqual(github.calls, ["GET", "POST", "GET"])
        self.assertEqual(len(github.comments), 1)
        self.assertNotIn("NEVER_PUBLISH_THIS", github.comments[0]["body"])
        self.assertIn(job["id"], github.comments[0]["body"])
        self.assertIsNone(self.queue.claim(now=400))

    def test_reporting_requires_separate_write_and_token(self):
        self.completed()
        github = Reporter()
        github.allow_write = False
        self.queue.publish(github, 97)
        github.allow_write = True
        github.token = ""
        self.queue.publish(github, 97)
        self.assertEqual(github.calls, [])

    def test_changed_unsigned_delivery_id_cannot_replay_signed_body(self):
        secret = "test-only-" * 5
        body = json.dumps({"action": "opened", "repository": {"full_name": "owner/repo"}}).encode()
        headers = {"X-GitHub-Event": "issues", "X-GitHub-Delivery": "delivery-original-123456", "X-Hub-Signature-256": "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()}
        policies = {"owner/repo": {"enabled": True}}
        self.assertEqual(intake(self.queue, policies, secret, body, headers), "accepted")
        job = self.queue.claim()
        self.queue.finish(job["id"], job["claim"], "DONE", {})
        headers["X-GitHub-Delivery"] = "delivery-attacker-654321"
        self.assertEqual(intake(self.queue, policies, secret, body, headers), "duplicate")
        self.assertIsNone(self.queue.claim())
