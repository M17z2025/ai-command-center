from pathlib import Path
import importlib.util
import unittest
import yaml

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

    def test_every_registered_repository_has_chat_ownership(self):
        registry = yaml.safe_load((ROOT / "projects" / "registry.yaml").read_text(encoding="utf-8"))
        ownership = MOD.load_config()
        expected = {
            (item["name"], item["repository"])
            for item in registry.get("projects", [])
        }
        actual = {
            (item["project"], item["repository"])
            for item in ownership.get("projects", [])
        }
        self.assertEqual(expected, actual)

    def test_every_team_member_is_registered(self):
        ownership = MOD.load_config()
        leaders = yaml.safe_load(
            (ROOT / "headquarters" / "mesh" / "leaders.yaml").read_text(encoding="utf-8")
        )
        registry = yaml.safe_load(
            (ROOT / "headquarters" / "agents" / "registry.yaml").read_text(encoding="utf-8")
        )
        known = {
            item["id"] for item in registry.get("agents", [])
            if isinstance(item, dict) and item.get("id")
        }
        for section in ("leaders", "assurance_roles"):
            known.update(
                item["id"] for item in leaders.get(section, [])
                if isinstance(item, dict) and item.get("id")
            )

        self.assertIn(ownership["defaults"]["accountable_build_steward"], known)
        for agent_id in ownership["defaults"].get("core_team", []):
            self.assertIn(agent_id, known)
        for section in ("projects", "intake_projects"):
            for item in ownership.get(section, []):
                for agent_id in item.get("domain_team", []):
                    self.assertIn(agent_id, known, f"{item['project']}: {agent_id}")

    def test_normalized_aliases_cannot_point_to_different_projects(self):
        ownership = MOD.load_config()
        seen = {}
        for section in ("projects", "intake_projects"):
            for item in ownership.get(section, []):
                for alias in [item.get("project", ""), *item.get("aliases", [])]:
                    key = " ".join(str(alias).casefold().split())
                    if not key:
                        continue
                    if key in seen and seen[key] != item["project"]:
                        self.fail(
                            f"alias {alias!r} maps to both {seen[key]!r} and {item['project']!r}"
                        )
                    seen[key] = item["project"]

    def test_known_chat_only_projects_are_explicitly_owned(self):
        ownership = MOD.load_config()
        projects = {item["project"] for item in ownership.get("intake_projects", [])}
        for required in {
            "AutoHedge – FXHedge",
            "UK AI Tax Adviser / Tax Intelligence OS",
            "UK Payroll AI",
            "PL Lookup / Veterinary Medicines",
            "Dormant Medicines Research",
            "Secure DX Zambia",
            "Alpha-Zulu Directory",
            "Mitz PA",
            "White Rino",
            "AI Gaming",
            "UK AI HR & Employment Compliance",
            "AI PI Agent",
        }:
            self.assertIn(required, projects)


if __name__ == "__main__":
    unittest.main()
