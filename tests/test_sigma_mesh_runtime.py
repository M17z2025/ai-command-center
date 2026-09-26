import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sigma_runtime.config import MeshConfig
from sigma_runtime.orchestrator import SigmaOrchestrator
from sigma_runtime.provider import DeterministicTestProvider, ProviderError, provider_from_env
from sigma_runtime.router import MissionRouter
from sigma_runtime.server import build_server
from sigma_runtime.store import MissionStore


ROOT = Path(__file__).resolve().parents[1]


class SigmaMeshRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.config = MeshConfig(ROOT)
        self.router = MissionRouter(self.config)

    def test_router_selects_multiple_domains_and_bounded_specialists(self):
        plan = self.router.route(
            "Design AI software with database security and cryptography."
        )
        self.assertGreaterEqual(len(plan.domains), 2)
        self.assertIn("cyber-security", plan.domains)
        self.assertTrue(plan.specialists)
        for specialist in plan.specialists:
            self.assertTrue(specialist.parent)
            self.assertIn("self-promote", specialist.prohibited_actions)
            self.assertEqual(
                specialist.expiry_or_review_condition,
                "expires when the mission closes",
            )

    def test_router_selects_named_advisory_specialists(self):
        mobile = self.router.route(
            "Build a mobile Android and iOS app with a clear development plan."
        )
        self.assertTrue(mobile.development_planning_required)
        self.assertIn("mobile-app-engineering-master", mobile.leaders)

        film = self.router.route(
            "Create a film production, directing, editing and script development plan."
        )
        self.assertTrue(film.development_planning_required)
        self.assertTrue(
            {
                "film-director-master",
                "film-production-master",
                "film-editing-master",
                "scriptwriting-master",
            }
            & set(film.leaders)
        )

        commercial = self.router.route(
            "Develop a marketing and sales plan for a new business product."
        )
        self.assertIn("marketing-brand-master", commercial.leaders)
        self.assertIn("sales-commercial-master", commercial.leaders)

    def test_router_selects_algorithmic_engineering_team(self):
        plan = self.router.route(
            "Debug and fix the backend API, database query performance and add strong regression tests."
        )
        self.assertTrue(plan.algorithmic_engineering_required)
        self.assertIn("debugging-root-cause-master", plan.leaders)
        self.assertIn("backend-api-engineering-master", plan.leaders)
        self.assertIn("performance-optimisation-master", plan.leaders)
        self.assertIn("qa-test-engineering-master", plan.leaders)

    def test_router_activates_rescue_mode_for_broken_product(self):
        plan = self.router.route(
            "The backend is broken and login is not working. Fix the regression."
        )
        self.assertTrue(plan.rescue_mode_required)
        self.assertIn("sigma-engineering-support-desk", plan.leaders)
        self.assertIn("debugging-root-cause-master", plan.leaders)

    def test_rescue_mode_stays_open_without_fixed_verified_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "sigma.db")
            provider = DeterministicTestProvider()
            runtime = SigmaOrchestrator(self.config, self.router, provider, store)
            result = runtime.run(
                "The software is broken. Debug and fix the failing API.",
                evidence=[{"id": "e1", "type": "reproduction", "status": "REPRODUCED"}],
                requested_by="test",
                max_cycles=2,
            )
            self.assertEqual(result["status"], "ACTIVE_WORKING")
            self.assertTrue(result["plan"]["rescue_mode_required"])
            self.assertIn("engineering-rescue-report", result["artifacts"])
            self.assertIn(
                "engineering-rescue-mode",
                [event["stage"] for event in result["events"]],
            )

    def test_rescue_mode_can_close_only_with_fixed_verified_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "sigma.db")
            provider = DeterministicTestProvider()
            runtime = SigmaOrchestrator(self.config, self.router, provider, store)
            result = runtime.run(
                "Fix the broken API regression.",
                evidence=[
                    {"id": "e1", "type": "reproduction", "status": "REPRODUCED"},
                    {
                        "id": "e2",
                        "type": "engineering-rescue-verification",
                        "status": "FIXED_VERIFIED",
                    },
                ],
                requested_by="test",
                max_cycles=2,
            )
            self.assertEqual(result["status"], "FIXED_VERIFIED")

    def test_router_selects_thinker_lenses(self):
        plan = self.router.route(
            "Formal proof limits for a computer algorithm and computation model."
        )
        self.assertIn("kurt-godel", plan.thinkers)
        self.assertIn("alan-turing", plan.thinkers)
        self.assertTrue(plan.cognitive_methods)

    def test_end_to_end_runtime_repairs_then_completes_and_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "sigma.db")
            provider = DeterministicTestProvider()
            runtime = SigmaOrchestrator(self.config, self.router, provider, store)
            result = runtime.run(
                "Design secure AI software with database security.",
                evidence=[{"id": "e1", "source": "test", "content": "known test evidence"}],
                requested_by="test",
                max_cycles=2,
            )
            self.assertEqual(result["status"], "COMPLETE")
            self.assertIn("SIGMA FINAL SYNTHESIS", result["final_output"])
            stages = [event["stage"] for event in result["events"]]
            self.assertIn("adversarial-critique", stages)
            self.assertIn("evidence-verification", stages)
            self.assertIn("repair-loop", stages)
            self.assertIn("learning-candidate", stages)
            self.assertTrue(store.list_lessons())
            self.assertGreaterEqual(provider.critic_calls, 2)
            self.assertTrue(result["plan"]["development_planning_required"])
            self.assertIn("development-advisory-plan", result["artifacts"])
            self.assertIn(
                "SIGMA DEVELOPMENT ADVISORY PLAN",
                result["artifacts"]["development-advisory-plan"],
            )
            self.assertIn(
                "development-advisory-plan",
                [event["stage"] for event in result["events"]],
            )
            self.assertTrue(result["plan"]["algorithmic_engineering_required"])
            self.assertIn("algorithmic-solution-report", result["artifacts"])
            self.assertIn(
                "SIGMA ALGORITHMIC SOLUTION REPORT",
                result["artifacts"]["algorithmic-solution-report"],
            )
            self.assertIn("engineering-solution-judge", result["artifacts"])
            self.assertIn(
                "algorithmic-solution-search",
                [event["stage"] for event in result["events"]],
            )
            self.assertIn(
                "engineering-independent-judge",
                [event["stage"] for event in result["events"]],
            )

    def test_store_does_not_promote_lessons_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "sigma.db")
            store.create_mission("m1", "prompt", "test", {})
            lesson_id = store.add_lesson("m1", "candidate only")
            lesson = next(item for item in store.list_lessons() if item["id"] == lesson_id)
            self.assertEqual(lesson["status"], "CANDIDATE")

    def test_live_provider_fails_closed_without_configuration(self):
        keys = ["SIGMA_RUNTIME_PROVIDER", "SIGMA_LLM_ENDPOINT", "SIGMA_LLM_MODEL", "SIGMA_ALLOW_TEST_PROVIDER"]
        old = {key: os.environ.get(key) for key in keys}
        try:
            for key in keys:
                os.environ.pop(key, None)
            with self.assertRaises(ProviderError):
                provider_from_env()
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_http_api_requires_token_and_runs_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = MissionStore(Path(tmp) / "sigma.db")
            runtime = SigmaOrchestrator(
                self.config, self.router, DeterministicTestProvider(), store
            )
            server = build_server("127.0.0.1", 0, runtime, self.config, store, "secret")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with self.assertRaises(HTTPError) as ctx:
                    urlopen(Request(base + "/missions"), timeout=5)
                self.assertEqual(ctx.exception.code, 401)

                body = json.dumps(
                    {"prompt": "AI software security architecture", "max_cycles": 2}
                ).encode("utf-8")
                req = Request(
                    base + "/missions",
                    data=body,
                    method="POST",
                    headers={
                        "Authorization": "Bearer secret",
                        "Content-Type": "application/json",
                    },
                )
                with urlopen(req, timeout=10) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["status"], "COMPLETE")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
