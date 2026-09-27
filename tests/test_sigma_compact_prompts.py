from pathlib import Path
import tempfile
import unittest

from sigma_runtime.config import MeshConfig
from sigma_runtime.orchestrator import SigmaOrchestrator
from sigma_runtime.provider import CompletionRequest, ModelProvider
from sigma_runtime.router import MissionRouter
from sigma_runtime.store import MissionStore


ROOT = Path(__file__).resolve().parents[1]


class CaptureProvider(ModelProvider):
    def __init__(self):
        self.requests = []

    def complete(self, request: CompletionRequest) -> str:
        self.requests.append(request)
        if request.kind in {"critic", "verifier"}:
            return "VERDICT: REPAIR\nNeeds repair."
        if request.kind == "repair":
            return "REPAIRED ANALYSIS\nBounded."
        if request.kind == "synthesis":
            return "SIGMA FINAL SYNTHESIS\nDone."
        if request.kind == "postmortem":
            return "LESSON: keep prompts bounded."
        return "EXPERT ANALYSIS\nBounded."


class SigmaCompactPromptTests(unittest.TestCase):
    def setUp(self):
        self.config = MeshConfig(ROOT)
        self.router = MissionRouter(self.config)

    def test_repair_prompt_is_bounded_and_output_capped(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = CaptureProvider()
            runtime = SigmaOrchestrator(
                self.config,
                self.router,
                provider,
                MissionStore(Path(tmp) / "sigma.db"),
                max_parallel_specialists=1,
            )
            plan = self.router.route(
                "Verify runtime evidence and legal constraints for a technical test."
            )
            outputs = {item.id: "A" * 30000 for item in plan.specialists}
            repaired = runtime._repair(
                plan,
                "M" * 10000,
                outputs,
                "C" * 20000,
                "V" * 20000,
                [{"content": "E" * 20000}],
            )
            self.assertTrue(repaired)
            requests = [r for r in provider.requests if r.kind == "repair"]
            self.assertTrue(requests)
            for request in requests:
                self.assertLess(len(request.user), 22000)
                self.assertEqual(request.metadata["max_tokens"], 384)

    def test_governance_stages_have_explicit_output_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = CaptureProvider()
            runtime = SigmaOrchestrator(
                self.config,
                self.router,
                provider,
                MissionStore(Path(tmp) / "sigma.db"),
                max_parallel_specialists=1,
            )
            result = runtime.run(
                "Verify a technical commissioning path with evidence.",
                evidence=[{"id": "e1", "source": "test", "content": "bounded"}],
                requested_by="test",
                max_cycles=1,
            )
            self.assertIn(result["status"], {"COMPLETE", "COMPLETE_WITH_UNVERIFIED_ITEMS"})
            caps = {
                request.kind: request.metadata.get("max_tokens")
                for request in provider.requests
                if request.kind in {"analysis", "critic", "verifier", "repair", "synthesis", "postmortem"}
            }
            self.assertEqual(caps["analysis"], 512)
            self.assertEqual(caps["critic"], 384)
            self.assertEqual(caps["verifier"], 384)
            self.assertEqual(caps["repair"], 384)
            self.assertEqual(caps["synthesis"], 512)
            self.assertEqual(caps["postmortem"], 256)


if __name__ == "__main__":
    unittest.main()
