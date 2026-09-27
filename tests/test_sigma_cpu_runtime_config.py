import os
from pathlib import Path
import tempfile
import unittest

from sigma_runtime.config import MeshConfig
from sigma_runtime.orchestrator import SigmaOrchestrator
from sigma_runtime.provider import DeterministicTestProvider
from sigma_runtime.router import MissionRouter
from sigma_runtime.store import MissionStore


ROOT = Path(__file__).resolve().parents[1]


class SigmaCPURuntimeConfigTests(unittest.TestCase):
    def test_parallel_specialists_can_be_limited_by_environment(self):
        old = os.environ.get("SIGMA_MAX_PARALLEL_SPECIALISTS")
        os.environ["SIGMA_MAX_PARALLEL_SPECIALISTS"] = "1"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                config = MeshConfig(ROOT)
                runtime = SigmaOrchestrator(
                    config,
                    MissionRouter(config),
                    DeterministicTestProvider(),
                    MissionStore(Path(tmp) / "sigma.db"),
                )
                self.assertEqual(runtime.max_parallel_specialists, 1)
        finally:
            if old is None:
                os.environ.pop("SIGMA_MAX_PARALLEL_SPECIALISTS", None)
            else:
                os.environ["SIGMA_MAX_PARALLEL_SPECIALISTS"] = old

    def test_parallel_specialists_are_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = MeshConfig(ROOT)
            runtime = SigmaOrchestrator(
                config,
                MissionRouter(config),
                DeterministicTestProvider(),
                MissionStore(Path(tmp) / "sigma.db"),
                max_parallel_specialists=99,
            )
            self.assertEqual(runtime.max_parallel_specialists, 6)

    def test_ollama_overlay_exposes_cpu_safe_runtime_controls(self):
        text = (
            ROOT / "deploy" / "sigma-stack" / "docker-compose.ollama.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("SIGMA_MAX_PARALLEL_SPECIALISTS", text)
        self.assertIn("SIGMA_LLM_TIMEOUT_SECONDS", text)

    def test_live_probe_timeout_is_configurable(self):
        text = (ROOT / "scripts" / "sigma_live_probe.py").read_text(encoding="utf-8")
        self.assertIn("SIGMA_LIVE_PROBE_TIMEOUT_SECONDS", text)
        self.assertIn('parser.add_argument(\n        "--timeout"', text)


if __name__ == "__main__":
    unittest.main()
