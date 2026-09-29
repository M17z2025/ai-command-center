import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sigma_runtime.server import build_server


class FakeConfig:
    def public_summary(self):
        return {"domains": 1}


class FakeStore:
    def list_missions(self):
        return []

    def list_lessons(self):
        return []

    def get_mission(self, mission_id):
        return None


class FakeGitHub:
    allow_write = False


class FakeRunnerStore:
    def list(self, limit=50):
        return [{"id": "cycle-1", "status": "PLANNED"}]

    def get(self, cycle_id):
        return {"id": cycle_id, "status": "PLANNED"} if cycle_id == "cycle-1" else None


class FakeRunner:
    github = FakeGitHub()
    worker = None
    store = FakeRunnerStore()

    def cycle(self, trigger="api", execute=False):
        return {"cycle_id": "cycle-2", "state": "PLANNED", "trigger": trigger, "execute": execute}


class FakeOrchestrator:
    def run(self, *args, **kwargs):
        return {"id": "mission-1", "status": "COMPLETE"}


class RuntimeRunnerAPITests(unittest.TestCase):
    def setUp(self):
        self.server = build_server(
            "127.0.0.1",
            0,
            FakeOrchestrator(),
            FakeConfig(),
            FakeStore(),
            "secret",
            portfolio_runner=FakeRunner(),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, *, method="GET", payload=None, auth=True):
        headers = {}
        data = None
        if auth:
            headers["Authorization"] = "Bearer secret"
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        req = Request(self.base + path, headers=headers, data=data, method=method)
        with urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_health_reports_runner_without_auth(self):
        status, body = self.request("/health", auth=False)
        self.assertEqual(status, 200)
        self.assertTrue(body["runner"]["configured"])
        self.assertFalse(body["runner"]["write_enabled"])

    def test_runner_cycles_require_auth(self):
        with self.assertRaises(HTTPError) as ctx:
            self.request("/runner/cycles", auth=False)
        self.assertEqual(ctx.exception.code, 401)

    def test_runner_cycles_endpoint(self):
        status, body = self.request("/runner/cycles")
        self.assertEqual(status, 200)
        self.assertEqual(body["cycles"][0]["id"], "cycle-1")

    def test_runner_cycle_trigger(self):
        status, body = self.request(
            "/runner/cycle",
            method="POST",
            payload={"trigger": "operator", "execute": False},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["state"], "PLANNED")
        self.assertEqual(body["trigger"], "operator")

    def test_api_cannot_elevate_disabled_execution(self):
        with self.assertRaises(HTTPError) as ctx:
            self.request("/runner/cycle", method="POST", payload={"execute": True})
        self.assertEqual(ctx.exception.code, 403)

    def test_execution_requires_boolean(self):
        with self.assertRaises(HTTPError) as ctx:
            self.request("/runner/cycle", method="POST", payload={"execute": "false"})
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
