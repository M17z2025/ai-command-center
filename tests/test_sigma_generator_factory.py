from copy import deepcopy
from pathlib import Path
import unittest

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


if __name__ == "__main__":
    unittest.main()
