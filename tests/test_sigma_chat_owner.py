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

    def test_approved_consolidation_routes_to_canonical_owners(self):
        friday = "M17z2025/alisha-ai-platform"
        sigma = "M17z2025/ai-command-center"
        for title in ("Friday AI", "Alysha OS", "Alisha OS"):
            self.assertEqual(MOD.resolve(title)["repository"], friday)
        for title in ("Alysha Repository Automation", "Alisha Repository Automation"):
            self.assertEqual(MOD.resolve(title)["repository"], sigma)
        old = MOD.resolve("General development", repository="M17z2025/alisha-os")
        self.assertEqual(old["repository"], friday)
        self.assertEqual(old["matched_by"], "consolidated_repository")
        self.assertEqual(old["superseded_repository"], "M17z2025/alisha-os")
        other = MOD.resolve("Friday development", repository="M17z2025/alisha-repository-automation")
        self.assertEqual(other["repository"], sigma)
        self.assertEqual(other["matched_by"], "consolidated_repository")

    def test_retired_sources_not_active_registered_projects(self):
        registry = yaml.safe_load((ROOT / "projects" / "registry.yaml").read_text(encoding="utf-8"))
        registered = {item["repository"] for item in registry["projects"]}
        redirects = registry["consolidated_repositories"]
        for entry in redirects:
            self.assertNotIn(entry["source"], registered)
            self.assertIn(entry["canonical"], registered)
            self.assertEqual(entry["status"], "archive_pending")
        team_redirects = MOD.load_config()["consolidated_repositories"]
        self.assertEqual(
            {(x["source"], x["canonical"]) for x in redirects},
            {(x["source"], x["canonical"]) for x in team_redirects},
        )

    def test_mitz_pa_aliases_route_to_sigma_and_friday_remains_separate(self):
        sigma = "M17z2025/ai-command-center"
        for title in ("Mitz PA", "Mitz personal assistant", "Jarvis", "Personal assistant", "Sigma PA"):
            with self.subTest(title=title):
                assignment = MOD.resolve(title)
                self.assertEqual(assignment["repository"], sigma)
                self.assertEqual(assignment["project"], "Sigma Development Command Center")
                self.assertEqual(assignment["state"], "ASSIGNED")
        for title in ("Friday", "Friday AI", "Friday assistant", "Alysha OS"):
            with self.subTest(title=title):
                self.assertEqual(
                    MOD.resolve(title)["repository"],
                    "M17z2025/alisha-ai-platform",
                )
        self.assertNotIn(
            "Mitz PA",
            {x["project"] for x in MOD.load_config()["intake_projects"]},
        )

    def test_mitz_pa_consolidation_consistent_across_owner_registers(self):
        registry = yaml.safe_load((ROOT / "projects" / "registry.yaml").read_text(encoding="utf-8"))
        teams = MOD.load_config()
        aliases = [x for x in teams["consolidated_products"] if x["source_product"] == "Mitz PA"]
        product = [x for x in registry["consolidated_products"] if x["source_product"] == "Mitz PA"]
        self.assertEqual(len(aliases), 1)
        self.assertEqual(len(product), 1)
        self.assertEqual(aliases[0]["canonical_repository"], "M17z2025/ai-command-center")
        self.assertEqual(product[0]["canonical_repository"], aliases[0]["canonical_repository"])
        self.assertEqual(aliases[0]["interface_repository"], "M17z2025/alisha-ai-platform")
        self.assertEqual(product[0]["status"], "merged_into_sigma")
        self.assertIsNone(product[0]["standalone_repository"])

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
            "White Rino",
            "AI Gaming",
            "UK AI HR & Employment Compliance",
            "AI PI Agent",
        }:
            self.assertIn(required, projects)


if __name__ == "__main__":
    unittest.main()
