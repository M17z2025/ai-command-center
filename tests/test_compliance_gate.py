"""Unit tests for the Sigma compliance completeness gate (not legal assurance)."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("compliance_gate", ROOT / "scripts" / "compliance_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def approved_record():
    data = json.loads((ROOT / "templates" / "PRODUCT_COMPLIANCE.json").read_text())
    p = data["project"]
    p.update({
        "repository": "M17z2025/example", "product_name": "Example", "legal_entity": "Example Ltd",
        "accountable_owner": "ProductOwner", "markets": ["UK"],
        "children_likely": False, "personal_data": True, "special_category_data": False,
        "financial_transactions": False, "autonomous_external_actions": False,
        "education_assessment": False, "regulated_health_purpose": False
    })
    data["ai"].update({
        "has_ai": False, "roles": [], "eu_ai_act_risk": "not_applicable",
        "systems": [], "intended_use_assessment": "No AI system involved"
    })
    data["legal"].update({
        "status": "approved", "reviewer": "LegalReviewer", "review_date": "2026-11-12",
        "sector_regulator_assessment": "Ordinary website; no identified sector regulator.",
        "jurisdiction_decisions": [{"jurisdiction":"UK","obligation":"UK GDPR","applies":True,
                                    "rationale":"Processes customer personal data"}]
    })
    for control in data["controls"].values():
        control.update(state="pass", reviewer="IndependentAssessor",
                       evidence=["https://github.com/M17z2025/example/issues/1"], rationale="")
    data["review"] = {"decision": "approved", "independent_reviewer": "IndependentReviewer",
                      "date": "2026-11-12", "release_ticket": "Release-001"}
    return data


class ComplianceGateTests(unittest.TestCase):
    def test_complete_manifest_passes_structural_gate(self):
        self.assertEqual(gate.check(approved_record()), [])

    def test_template_is_not_approved(self):
        original = json.loads((ROOT / "templates" / "PRODUCT_COMPLIANCE.json").read_text())
        self.assertTrue(gate.check(original))

    def test_missing_evidence_blocks(self):
        record = approved_record()
        record["controls"]["security_and_access"]["evidence"] = []
        self.assertTrue(any("traceable evidence" in e for e in gate.check(record)))

    def test_sector_trigger_requires_pass(self):
        record = approved_record()
        record["project"]["children_likely"] = True
        record["controls"]["children_code"]["state"] = "not_applicable"
        record["controls"]["children_code"]["rationale"] = "Incorrect"
        self.assertTrue(any("children_code must pass" in e for e in gate.check(record)))

    def test_unreviewed_ai_blocks(self):
        record = approved_record()
        record["ai"].update(has_ai=True, roles=["provider"], eu_ai_act_risk="pending_assessment",
                            systems=[{"name":"Chat","purpose":"Customer help","model_or_supplier":"Example",
                                      "human_oversight":"Human escalation"}])
        self.assertTrue(any("pending/prohibited" in e for e in gate.check(record)))

    def test_product_owner_cannot_self_review(self):
        record = approved_record()
        record["review"]["independent_reviewer"] = "ProductOwner"
        self.assertTrue(any("must differ" in e for e in gate.check(record)))


if __name__ == "__main__":
    unittest.main()
