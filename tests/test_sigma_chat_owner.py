from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sigma_chat_owner", ROOT / "scripts" / "sigma_chat_owner.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class ChatOwnershipTests(unittest.TestCase):
    def test_invoiceit_chat_gets_invoiceit_team(self):
        result = MOD.resolve("Invoiceit Development Loop")
        self.assertEqual(result["repository"], "M17z2025/invoiceit-by-mi7z")
        self.assertIn("sigma-chat-build-steward", result["accountable_build_steward"])
        self.assertIn("finance-all-aspects-master", result["team"])
        self.assertIn("sigma-user-tester", result["team"])

    def test_revision_chat_routes_to_humanit(self):
        result = MOD.resolve("Revision Section Location", "GCSE subjects in Humanit Study")
        self.assertEqual(result["repository"], "M17z2025/ihumanit")
        self.assertIn("humanities-social-sciences-director", result["team"])

    def test_secure_dx_is_owned_but_repository_gate_is_honest(self):
        result = MOD.resolve("Secure DX Zambia Build Loop")
        self.assertEqual(result["project"], "Secure DX Zambia")
        self.assertEqual(result["state"], "PROJECT_REPOSITORY_REQUIRED")
        self.assertIsNone(result["repository"])

    def test_repository_reference_beats_chat_alias(self):
        result = MOD.resolve("General development", repository="M17z2025/umarketit")
        self.assertEqual(result["project"], "Marketit")


if __name__ == "__main__":
    unittest.main()
