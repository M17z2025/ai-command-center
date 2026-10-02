from copy import deepcopy
from pathlib import Path
import unittest
import tempfile

import yaml

from sigma_runtime.generator_factory import GeneratorFactory, GeneratorFactoryError


ROOT = Path(__file__).resolve().parents[1]


class SigmaGeneratorFactoryTests(unittest.TestCase):
    def setUp(self):
        self.factory = GeneratorFactory(ROOT)

    def test_registry_passes_validation(self):
        decisions = self.factory.validate_registry()
        failures = [
            (decision.generator_id, decision.reasons)
            for decision in decisions
            if decision.reasons
        ]
        self.assertEqual(failures, [])

    def test_seeded_choice_is_reproducible(self):
        inputs = {"items": ["alpha", "bravo", "charlie", "delta"], "count": 2}
        first = self.factory.execute("sigma-random-picker", inputs, seed=42)
        second = self.factory.execute("sigma-random-picker", inputs, seed=42)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)

    def test_weighted_choice_rejects_non_positive_weight(self):
        with self.assertRaisesRegex(GeneratorFactoryError, "weight must be positive"):
            self.factory.execute(
                "sigma-weighted-picker",
                {
                    "items": [
                        {"value": "safe", "weight": 1},
                        {"value": "invalid", "weight": 0},
                    ]
                },
                seed=1,
            )

    def test_scenario_matrix_builds_cartesian_product(self):
        result = self.factory.execute(
            "sigma-scenario-matrix",
            {
                "personas": ["visitor", "admin"],
                "devices": ["mobile", "desktop"],
                "states": ["success", "error"],
            },
        )
        self.assertEqual(len(result), 8)
        self.assertIn(
            {"personas": "visitor", "devices": "mobile", "states": "success"},
            result,
        )

    def test_scenario_matrix_enforces_output_limit(self):
        values = list(range(11))
        with self.assertRaisesRegex(GeneratorFactoryError, "max_output_items"):
            self.factory.execute(
                "sigma-scenario-matrix",
                {
                    "personas": values,
                    "devices": values,
                    "states": values,
                },
            )

    def test_synthetic_records_are_bounded_and_deterministic(self):
        inputs = {"labels": ["A", "B", "C"], "prefix": "QA", "count": 3}
        first = self.factory.execute("sigma-synthetic-records", inputs, seed=9)
        second = self.factory.execute("sigma-synthetic-records", inputs, seed=9)
        self.assertEqual(first, second)
        self.assertEqual(
            [record["record_id"] for record in first],
            [1, 2, 3],
        )
        self.assertEqual(first[0]["note"], "Synthetic QA record 1")

    def test_template_rejects_missing_field(self):
        with self.assertRaisesRegex(GeneratorFactoryError, "missing required inputs"):
            self.factory.execute("sigma-text-template", {})

    def test_approved_definition_with_forbidden_capability_fails_closed(self):
        definition = deepcopy(self.factory.get_definition("sigma-random-picker"))
        definition["id"] = "unsafe-generator"
        definition["capabilities"] = ["network"]
        decision = self.factory.validate_definition(definition)
        self.assertEqual(decision.state, "DRAFT")
        self.assertTrue(
            any("forbidden capabilities" in reason for reason in decision.reasons)
        )

    def test_unknown_operation_fails_closed(self):
        definition = deepcopy(self.factory.get_definition("sigma-random-picker"))
        definition["id"] = "unknown-operation"
        definition["operation"] = {"type": "python", "config": {"code": "pass"}}
        decision = self.factory.validate_definition(definition)
        self.assertEqual(decision.state, "DRAFT")
        self.assertTrue(
            any("unknown operation" in reason for reason in decision.reasons)
        )

    def test_draft_builder_never_grants_execution_authority(self):
        draft = self.factory.draft_definition(
            generator_id="legal-clause-scenario",
            name="Legal Clause Scenario",
            department="legal",
            description="Draft a bounded legal review scenario generator.",
            operation_type="choice",
        )
        self.assertEqual(draft["state"], "DRAFT")
        self.assertEqual(draft["capabilities"], [])


    def test_choice_with_replacement_must_be_boolean(self):
        definition = deepcopy(self.factory.get_definition("sigma-random-picker"))
        definition["id"] = "invalid-choice-config"
        definition["operation"]["config"]["with_replacement"] = "false"
        decision = self.factory.validate_definition(definition)
        self.assertTrue(
            any("with_replacement must be a boolean" in reason for reason in decision.reasons)
        )

    def test_template_preserves_braces_inside_input_values(self):
        result = self.factory.execute(
            "sigma-text-template",
            {"text": "Example {{literal}} text"},
        )
        self.assertEqual(result, "Example {{literal}} text")

    def test_standalone_spec_size_is_checked_before_parse(self):
        limit = int(self.factory.policy["limits"]["max_definition_bytes"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversize.yaml"
            path.write_text("x" * (limit + 1), encoding="utf-8")
            decision = self.factory.validate_spec_file(path)
        self.assertEqual(decision.generator_id, "<oversize>")
        self.assertTrue(
            any("max_definition_bytes" in reason for reason in decision.reasons)
        )


    def test_owner_supplied_github_source_registry(self):
        path = ROOT / "headquarters" / "generator-factory" / "user-github-sources.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], 1)

        sources = data["sources"]
        urls = [item["url"] for item in sources]

        self.assertEqual(len(urls), 40)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(url.startswith("https://github.com/") for url in urls))
        self.assertTrue(
            all(item["state"] in {"REVIEW", "EVIDENCE"} for item in sources)
        )

        required = {
            "https://github.com/JustVugg/colibri",
            "https://github.com/OpenHands/OpenHands",
            "https://github.com/HKUDS/DeepTutor",
            "https://github.com/pipecat-ai/pipecat",
            "https://github.com/M17z2025/ai-command-center",
            "https://github.com/M17z2025/mi7z-web",
        }
        self.assertTrue(required.issubset(set(urls)))


    def test_owner_github_review_covers_all_external_sources(self):
        source_path = (
            ROOT / "headquarters" / "generator-factory" / "user-github-sources.yaml"
        )
        review_path = (
            ROOT / "headquarters" / "generator-factory" / "user-github-review.yaml"
        )
        source_data = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        review_data = yaml.safe_load(review_path.read_text(encoding="utf-8"))

        external_urls = {
            item["url"]
            for item in source_data["sources"]
            if not item["url"].startswith("https://github.com/M17z2025/")
        }
        reviewed_urls = {item["source_url"] for item in review_data["reviews"]}

        self.assertEqual(len(external_urls), 29)
        self.assertEqual(reviewed_urls, external_urls)

        decisions = {}
        for item in review_data["reviews"]:
            decisions[item["decision"]] = decisions.get(item["decision"], 0) + 1

        self.assertEqual(
            decisions,
            {
                "ACCEPT_FOR_DEEP_REVIEW": 13,
                "FORK_OR_SERVICE_BOUNDARY": 6,
                "REFERENCE_ONLY": 3,
                "RESTRICTED_LICENSE": 3,
                "LICENCE_UNVERIFIED": 1,
                "DISCOVERY_ONLY": 3,
            },
        )


if __name__ == "__main__":
    unittest.main()
