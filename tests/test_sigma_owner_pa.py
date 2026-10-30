"""Mitz PA is a bounded role of Sigma, not a competing assistant system."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from sigma_runtime.owner_pa import SigmaMitzPA, MAX_OWNER_PROMPT_CHARS


class FakeMesh:
    def __init__(self):
        self.calls = []

    def run(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return {"id": "sigma-mission-123", "status": "COMPLETE",
                "final_output": "The recommended approach is to inspect actual evidence."}


class SigmaOwnerPATests(unittest.TestCase):
    def test_uses_only_the_existing_sigma_mesh_and_durable_mission_identity(self):
        mesh = FakeMesh()
        result = SigmaMitzPA(mesh).advise("  Research the next step  ")
        self.assertEqual(len(mesh.calls), 1)
        self.assertEqual(mesh.calls[0][0], "Research the next step")
        self.assertEqual(mesh.calls[0][1]["requested_by"], "mitz-pa-owner")
        self.assertEqual(mesh.calls[0][1]["evidence"], [])
        self.assertEqual(mesh.calls[0][1]["max_cycles"], 0)
        self.assertEqual(result.mission_id, "sigma-mission-123")
        self.assertEqual(result.advisory_status, "COMPLETE")
        self.assertFalse(result.action_executed)
        self.assertEqual(result.external_action_status, "NOT_EXECUTED")
        self.assertEqual(result.source, "M17z2025/ai-command-center")
        self.assertNotIn("verified_action", result.to_dict())

    def test_rejects_empty_large_and_non_string_prompts_without_invoking_models(self):
        mesh = FakeMesh()
        for prompt in ("", "   ", None, 5, "x" * (MAX_OWNER_PROMPT_CHARS + 1)):
            with self.subTest(value=repr(prompt)[:18]):
                with self.assertRaises(ValueError):
                    SigmaMitzPA(mesh).advise(prompt)
        self.assertFalse(mesh.calls)

    def test_broken_provider_result_cannot_be_counted_as_completed_action(self):
        mesh = FakeMesh()
        mesh.run = lambda prompt, **kwargs: {"status": "ERROR"}
        with self.assertRaises(RuntimeError):
            SigmaMitzPA(mesh).advise("Anything")

    def test_output_is_bounded_and_never_claims_external_execution(self):
        mesh = FakeMesh()
        mesh.run = lambda prompt, **kwargs: {
            "id": "m1", "status": "COMPLETE", "final_output": "a" * 20000,
        }
        result = SigmaMitzPA(mesh).advise("Investigate")
        self.assertEqual(len(result.summary), 12000)
        self.assertFalse(result.action_executed)


if __name__ == "__main__":
    unittest.main()
