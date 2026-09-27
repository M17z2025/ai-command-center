from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SigmaMemoryStackFilesTests(unittest.TestCase):
    def test_memory_requirements_pin_graphiti(self):
        text = (ROOT / "requirements-memory.txt").read_text(encoding="utf-8")
        self.assertIn("graphiti-core[falkordb]==0.30.2", text)

    def test_memory_compose_is_private_and_pinned(self):
        text = (
            ROOT / "deploy" / "sigma-stack" / "docker-compose.memory.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("falkordb/falkordb:v4.20.7", text)
        self.assertIn("SIGMA_MEMORY_TOKEN", text)
        self.assertIn('expose:', text)
        self.assertNotIn('ports:', text)

    def test_memory_service_rejects_candidate_ingestion(self):
        text = (
            ROOT / "scripts" / "sigma_graphiti_memory_service.py"
        ).read_text(encoding="utf-8")
        self.assertIn('{"VERIFIED", "PROMOTED"}', text)
        self.assertIn("Graphiti trusted memory accepts only", text)

    def test_memory_stack_reuses_private_ollama(self):
        text = (
            ROOT / "deploy" / "sigma-stack" / "docker-compose.memory.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("http://ollama:11434/v1", text)
        self.assertIn("OLLAMA_EMBEDDING_MODEL", text)


if __name__ == "__main__":
    unittest.main()
