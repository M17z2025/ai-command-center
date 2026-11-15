"""Regression contract: the live Sigma coding agent must condense tool history.

Without this, OpenHands SDK can exhaust the 8K local model window and fail
the portfolio runner's GitHub development mission.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "sigma_openhands_worker_service.py"


class WorkerCondenserContractTests(unittest.TestCase):
    def test_openhands_coding_agent_has_bounded_context_condenser(self):
        tree = ast.parse(WORKER.read_text(encoding="utf-8"))
        editor = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_open_hands_edit"
        )
        agent_calls = [
            node for node in ast.walk(editor)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Agent"
        ]
        self.assertEqual(len(agent_calls), 1)
        kwargs = {kw.arg: kw.value for kw in agent_calls[0].keywords}
        self.assertIn("condenser", kwargs)
        condenser = kwargs["condenser"]
        self.assertIsInstance(condenser, ast.Call)
        self.assertIsInstance(condenser.func, ast.Name)
        self.assertEqual(condenser.func.id, "LLMSummarizingCondenser")
        config = {kw.arg: kw.value for kw in condenser.keywords}
        self.assertIn("max_size", config)
        self.assertIsInstance(config["max_size"], ast.Constant)
        self.assertLessEqual(config["max_size"].value, 32)
        self.assertIn("keep_first", config)


if __name__ == "__main__":
    unittest.main()
