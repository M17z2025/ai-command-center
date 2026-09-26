from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class SigmaProjectTeamTests(unittest.TestCase):
    def setUp(self):
        self.teams = yaml.safe_load(
            (ROOT / "headquarters/project-teams.yaml").read_text(encoding="utf-8")
        )
        self.registry = yaml.safe_load(
            (ROOT / "projects/registry.yaml").read_text(encoding="utf-8")
        )
        self.leaders = yaml.safe_load(
            (ROOT / "headquarters/mesh/leaders.yaml").read_text(encoding="utf-8")
        )
        self.agents = yaml.safe_load(
            (ROOT / "headquarters/agents/registry.yaml").read_text(encoding="utf-8")
        )

    def test_every_registered_project_has_exact_team_assignment(self):
        expected = {
            (item["name"], item["repository"])
            for item in self.registry.get("projects", [])
        }
        actual = {
            (item["project"], item["repository"])
            for item in self.teams.get("project_assignments", [])
        }
        self.assertEqual(expected, actual)

    def test_all_team_profiles_reference_registered_agents(self):
        known = {
            item["id"]
            for item in self.agents.get("agents", [])
            if isinstance(item, dict) and item.get("id")
        }
        for section in ("leaders", "assurance_roles"):
            known.update(
                item["id"]
                for item in self.leaders.get(section, [])
                if isinstance(item, dict) and item.get("id")
            )

        for profile_name, profile in self.teams.get("team_profiles", {}).items():
            self.assertIn(profile["lead"], known, profile_name)
            for specialist in profile.get("specialists", []):
                self.assertIn(specialist, known, f"{profile_name}: {specialist}")

        for role_name, agent_id in self.teams.get("mandatory_roles", {}).items():
            self.assertIn(agent_id, known, role_name)

    def test_all_assignments_reference_existing_profiles(self):
        profiles = set(self.teams.get("team_profiles", {}))
        for section in ("project_assignments", "chat_project_assignments"):
            for assignment in self.teams.get(section, []):
                self.assertIn(assignment["team_profile"], profiles)
                self.assertTrue(assignment.get("chat_aliases"))

    def test_chat_aliases_do_not_silently_collide(self):
        aliases = {}
        for section in ("project_assignments", "chat_project_assignments"):
            for assignment in self.teams.get(section, []):
                for alias in assignment.get("chat_aliases", []):
                    key = alias.strip().casefold()
                    if key in aliases:
                        self.fail(
                            f"chat alias {alias!r} maps to both "
                            f"{aliases[key]!r} and {assignment['project']!r}"
                        )
                    aliases[key] = assignment["project"]

    def test_scouter_is_mandatory_for_every_project_team(self):
        self.assertEqual(
            self.teams["mandatory_roles"]["open_source_recon"],
            "sigma-scouter",
        )
        self.assertTrue((ROOT / "headquarters/scouter/policy.yaml").exists())
        self.assertTrue((ROOT / "headquarters/scouter/catalog.yaml").exists())


if __name__ == "__main__":
    unittest.main()
