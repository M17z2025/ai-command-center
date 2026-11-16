"""Hermes adapter policy and protocol tests; no live provider or paid calls."""
import io
import json
import unittest
from unittest.mock import patch

from sigma_runtime.workers.base import CapabilityPolicy, WorkerMission, WorkerStatus
from sigma_runtime.workers.hermes import HermesWorkerAdapter, HermesWorkerConfig, _NoRedirects


def mission(**overrides):
    values = dict(
        mission_id="hermes-proof-1", parent_agent="sigma", project="sandbox/sample",
        objective="Review bounded sample", acceptance_criteria=("Produce candidate report",),
        capabilities=CapabilityPolicy(allow=frozenset({"sandbox_execution"})),
        filesystem_scope=("/tmp/hermes-proof",),
    )
    values.update(overrides)
    return WorkerMission(**values)


class MockReply:
    def __init__(self, payload):
        self.data = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self):
        return self.data


class HermesWorkerTests(unittest.TestCase):
    def setUp(self):
        self.config = HermesWorkerConfig(
            endpoint="https://hermes.internal.example/v1",
            api_key="test-in-memory-token", enabled=True, sandbox_verified=True,
            poll_seconds=0.01,
        )

    def test_default_is_blocked_without_network(self):
        with patch("sigma_runtime.workers.hermes.build_opener") as network:
            outcome = HermesWorkerAdapter().execute(mission())
        self.assertEqual(outcome.status, WorkerStatus.BLOCKED)
        network.assert_not_called()

    def test_verified_sandbox_and_scope_required(self):
        adapter = HermesWorkerAdapter(HermesWorkerConfig(
            endpoint="https://hermes.internal.example", api_key="long-test-token",
            enabled=True, sandbox_verified=False,
        ))
        result = adapter.execute(mission())
        self.assertEqual(result.status, WorkerStatus.BLOCKED)
        self.assertIn("isolation", result.unresolved_failures[0])
        adapter = HermesWorkerAdapter(self.config)
        self.assertEqual(adapter.execute(mission(filesystem_scope=())).status, WorkerStatus.BLOCKED)
        self.assertEqual(adapter.execute(mission(credential_scope=("github",))).status, WorkerStatus.BLOCKED)
        self.assertEqual(adapter.execute(mission(capabilities=CapabilityPolicy(
            allow=frozenset({"sandbox_execution", "production_release"})
        ))).status, WorkerStatus.BLOCKED)

    def test_unsafe_endpoints_rejected(self):
        for endpoint in ("http://external.example:8642", "https://user:pwd@example.com",
                         "https://example.com/v1?key=bad", "file:///etc/passwd"):
            with self.assertRaises(ValueError):
                HermesWorkerConfig(endpoint=endpoint, api_key="12345678", enabled=True)

    def test_success_returns_candidate_only_and_idempotent_run(self):
        requests = []
        def fake_urlopen(request, timeout):
            requests.append(request)
            if request.full_url.endswith("/v1/runs") and request.get_method() == "POST":
                return MockReply({"run_id": "run-123", "status": "started"})
            return MockReply({"run_id": "run-123", "status": "completed",
                              "output": "Suggested patch. Tests not executed."})
        events = []
        with patch("sigma_runtime.workers.hermes.build_opener") as builder:
            builder.return_value.open.side_effect = fake_urlopen
            result = HermesWorkerAdapter(self.config).execute(
                mission(), audit_sink=lambda name, payload: events.append(name))
        self.assertEqual(result.status, WorkerStatus.PLANNED)
        self.assertEqual(result.evidence, ("hermes_run_id:run-123",))
        self.assertNotIn("TESTED", result.status.value)
        self.assertEqual(requests[0].get_header("Idempotency-key"), "sigma-hermes-proof-1")
        self.assertEqual(events, ["worker.started", "worker.finished"])

    def test_bearer_is_not_forwarded_to_redirect(self):
        self.assertIsNone(_NoRedirects().redirect_request(
            None, None, 302, "redirect", {}, "https://untrusted.example"
        ))

    def test_remote_failure_never_counts_as_success(self):
        replies = iter([
            {"run_id": "run-1", "status": "started"},
            {"run_id": "run-1", "status": "failed", "output": "failed"},
        ])
        with patch("sigma_runtime.workers.hermes.build_opener") as builder:
            builder.return_value.open.side_effect = lambda *_args, **_kw: MockReply(next(replies))
            result = HermesWorkerAdapter(self.config).execute(mission())
        self.assertEqual(result.status, WorkerStatus.BLOCKED)
        self.assertFalse(result.evidence)


if __name__ == "__main__":
    unittest.main()
