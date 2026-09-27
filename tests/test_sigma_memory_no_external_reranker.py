import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SigmaMemoryNoExternalRerankerTests(unittest.TestCase):
    def test_memory_service_injects_local_cross_encoder(self):
        text = (
            ROOT / "scripts" / "sigma_graphiti_memory_service.py"
        ).read_text(encoding="utf-8")
        self.assertIn("class LocalPassThroughReranker", text)
        self.assertIn("cross_encoder=LocalPassThroughReranker()", text)
        self.assertNotIn("OpenAIRerankerClient", text)

    def test_memory_service_parses(self):
        path = ROOT / "scripts" / "sigma_graphiti_memory_service.py"
        ast.parse(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
