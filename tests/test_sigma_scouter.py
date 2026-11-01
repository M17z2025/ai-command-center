from pathlib import Path
import unittest

from sigma_runtime.scouter import ScouterPolicy


ROOT = Path(__file__).resolve().parents[1]


class SigmaScouterTests(unittest.TestCase):
    def setUp(self):
        self.scouter = ScouterPolicy(ROOT)

    def test_catalog_passes_strict_policy_validation(self):
        decisions = self.scouter.validate_catalog()
        failures = [(d.candidate_id, d.reasons) for d in decisions if d.reasons]
        self.assertEqual(failures, [])

    def test_owner_approved_shortlist_is_prioritised_but_not_deployed(self):
        shortlist = self.scouter.owner_shortlist()
        self.assertEqual(len(shortlist), 11)
        self.assertEqual(shortlist[0]["id"], "cloudflare-security-audit")
        self.assertEqual(shortlist[-1]["id"], "zero-breach")
        self.assertEqual(len({item["id"] for item in shortlist}), len(shortlist))
        self.assertTrue(all(item["state"] == "REVIEW" for item in shortlist))
        self.assertTrue(all(
            item["owner_shortlist"]["implementation_status"] == "NOT_INSTALLED_NOT_VERIFIED"
            for item in shortlist
        ))
        self.assertEqual(len(self.scouter.owner_shortlist("PILOT")), 6)
        self.assertEqual(len(self.scouter.owner_shortlist("BENCHMARK_ONLY")), 1)

    def test_accepted_public_api_requires_explicit_unlimited_evidence(self):
        candidate = {
            "id": "bad-public-api",
            "name": "Bad API",
            "category": "test",
            "kind": "public_api",
            "upstream": "https://example.invalid",
            "licence": "MIT",
            "licence_class": "permissive",
            "state": "ACCEPT",
            "self_hosted": False,
            "unlimited_basis": "free",
            "what_it_does": "test",
            "portfolio_fit": ["test"],
            "integration_strategy": "test only",
            "verified_on": "2026-09-26",
            "evidence": [{"source": "test"}],
        }
        decision = self.scouter.validate_candidate(candidate)
        self.assertEqual(decision.state, "REVIEW")
        self.assertTrue(any("no rate limit" in reason for reason in decision.reasons))

    def test_unknown_licence_cannot_be_accepted(self):
        candidate = dict(self.scouter.list_candidates("ACCEPT")[0])
        candidate["id"] = "unknown-licence"
        candidate["licence"] = "NOASSERTION"
        decision = self.scouter.validate_candidate(candidate)
        self.assertEqual(decision.state, "REVIEW")


if __name__ == "__main__":
    unittest.main()
