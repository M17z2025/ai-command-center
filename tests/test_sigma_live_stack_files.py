from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "deploy" / "sigma-stack"


class SigmaLiveStackFilesTests(unittest.TestCase):
    def test_base_stack_binds_sigma_to_loopback(self):
        data = yaml.safe_load((STACK / "docker-compose.yml").read_text())
        ports = data["services"]["sigma-runtime"]["ports"]
        self.assertTrue(ports)
        self.assertTrue(all(str(port).startswith("127.0.0.1:") for port in ports))

    def test_freellm_pilot_is_pinned_and_not_host_published(self):
        data = yaml.safe_load(
            (STACK / "docker-compose.freellm-pilot.yml").read_text()
        )
        service = data["services"]["freellmapi"]
        self.assertEqual(
            service["image"],
            "ghcr.io/tashfeenahmed/freellmapi:v0.12.0",
        )
        self.assertNotIn("ports", service)
        self.assertIn("3001", [str(item) for item in service.get("expose", [])])

    def test_examples_have_no_populated_secret_values(self):
        text = (STACK / ".env.example").read_text()
        for key in (
            "SIGMA_RUNTIME_TOKEN",
            "SIGMA_LLM_API_KEY",
            "FREELLMAPI_ENCRYPTION_KEY",
            "FREELLMAPI_UNIFIED_KEY",
        ):
            line = next(
                item for item in text.splitlines() if item.startswith(key + "=")
            )
            self.assertEqual(line, key + "=")


if __name__ == "__main__":
    unittest.main()
