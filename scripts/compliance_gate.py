#!/usr/bin/env python3
"""Fail-closed structural/evidence gate for Sigma product compliance manifests.

Validates required records and reviewer attestations, NOT legal truth or
underlying evidence. Independent manual assurance remains mandatory.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

CONTROL_IDS = (
    "asset_and_vendor_inventory",
    "privacy_data_mapping",
    "lawful_basis_and_notices",
    "data_subject_rights_and_retention",
    "security_and_access",
    "incident_and_recovery",
    "ai_governance_and_testing",
    "ai_transparency_and_synthetic_media",
    "supplier_assurance",
    "accessibility_and_consumer_rights",
    "children_code",
    "special_category_data",
    "financial_regulatory_scoping",
    "agent_action_governance",
    "education_high_risk_scoping",
    "medical_device_scoping",
)
FLAGS = (
    "children_likely", "personal_data", "special_category_data",
    "financial_transactions", "autonomous_external_actions",
    "education_assessment", "regulated_health_purpose",
)
TRIGGERED = {
    "children_likely": "children_code",
    "special_category_data": "special_category_data",
    "financial_transactions": "financial_regulatory_scoping",
    "autonomous_external_actions": "agent_action_governance",
    "education_assessment": "education_high_risk_scoping",
    "regulated_health_purpose": "medical_device_scoping",
}
RISK = {"not_applicable", "minimal", "transparency", "high", "pending_assessment", "prohibited"}
ROLES = {"provider", "deployer", "importer", "distributor", "product_manufacturer"}
EMPTY = {"", "TBD", "UNKNOWN", "REVIEW_REQUIRED", "REPLACE_WITH_PRODUCT", "REPLACE_WITH_REPOSITORY"}


def meaningful(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() not in EMPTY and not value.startswith("REPLACE_WITH_")


def date_valid(value: object) -> bool:
    if not meaningful(value):
        return False
    try:
        dt.date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def check(record: object) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, description: str) -> None:
        if not condition:
            errors.append(description)

    if not isinstance(record, dict):
        return ["Manifest must be a JSON object."]
    require(record.get("schema_version") == 1, "schema_version must equal 1.")
    project = record.get("project")
    if not isinstance(project, dict):
        return errors + ["Missing project object."]
    for key in ("repository", "product_name", "legal_entity", "accountable_owner"):
        require(meaningful(project.get(key)), f"project.{key} is required.")
    markets = project.get("markets")
    require(isinstance(markets, list) and bool(markets) and all(meaningful(m) for m in markets),
            "project.markets must list the in-scope countries/markets.")
    for flag in FLAGS:
        require(type(project.get(flag)) is bool, f"project.{flag} requires a true/false decision.")

    ai = record.get("ai")
    if not isinstance(ai, dict):
        return errors + ["Missing ai object."]
    has_ai = ai.get("has_ai")
    require(type(has_ai) is bool, "ai.has_ai requires a true/false decision.")
    risk = ai.get("eu_ai_act_risk")
    require(risk in RISK, "ai.eu_ai_act_risk is invalid.")
    require(risk not in {"pending_assessment", "prohibited"},
            "AI Act risk is pending/prohibited; release must remain blocked.")
    roles = ai.get("roles")
    require(isinstance(roles, list) and all(role in ROLES for role in roles),
            "ai.roles must be a list of valid EU AI Act roles.")
    systems = ai.get("systems")
    require(isinstance(systems, list), "ai.systems must be a list.")
    require(meaningful(ai.get("intended_use_assessment")), "ai.intended_use_assessment is required.")
    if has_ai is True:
        require(bool(roles), "AI products must identify provider/deployer/etc role.")
        require(bool(systems), "AI products must inventory their AI systems.")
        require(risk != "not_applicable", "AI products require a reasoned EU AI Act classification.")
        if isinstance(systems, list):
            for index, system in enumerate(systems):
                require(isinstance(system, dict) and
                        all(meaningful(system.get(k)) for k in ("name", "purpose", "model_or_supplier", "human_oversight")),
                        f"ai.systems[{index}] requires name, purpose, model_or_supplier and human_oversight.")
    elif has_ai is False:
        require(risk == "not_applicable", "Non-AI products should record risk not_applicable.")
        require(roles == [] and systems == [], "Non-AI products should not list AI roles/systems.")

    legal = record.get("legal")
    if not isinstance(legal, dict):
        return errors + ["Missing legal object."]
    require(legal.get("status") == "approved", "legal.status must be approved after independent review.")
    require(meaningful(legal.get("reviewer")), "legal.reviewer is required.")
    require(date_valid(legal.get("review_date")), "legal.review_date must be ISO YYYY-MM-DD.")
    require(meaningful(legal.get("sector_regulator_assessment")), "legal.sector_regulator_assessment is required.")
    decisions = legal.get("jurisdiction_decisions")
    require(isinstance(decisions, list) and bool(decisions), "legal.jurisdiction_decisions must document applicable laws and exclusions.")
    if isinstance(decisions, list):
        for i, decision in enumerate(decisions):
            require(isinstance(decision, dict) and
                    meaningful(decision.get("jurisdiction")) and meaningful(decision.get("obligation")) and
                    type(decision.get("applies")) is bool and meaningful(decision.get("rationale")),
                    f"legal.jurisdiction_decisions[{i}] needs jurisdiction, obligation, applies and rationale.")

    controls = record.get("controls")
    if not isinstance(controls, dict):
        return errors + ["Missing controls object."]
    for identifier in CONTROL_IDS:
        item = controls.get(identifier)
        if not isinstance(item, dict):
            errors.append(f"controls.{identifier} is missing.")
            continue
        state = item.get("state")
        require(state in {"pass", "not_applicable"},
                f"controls.{identifier} is {state!r}, expected independently reviewed pass/not_applicable.")
        require(meaningful(item.get("reviewer")), f"controls.{identifier} requires reviewer.")
        if state == "pass":
            ev = item.get("evidence")
            require(isinstance(ev, list) and bool(ev) and all(meaningful(e) for e in ev),
                    f"controls.{identifier} needs traceable evidence references.")
        if state == "not_applicable":
            require(meaningful(item.get("rationale")),
                    f"controls.{identifier} requires a non-applicability rationale.")
    for flag, identifier in TRIGGERED.items():
        if project.get(flag) is True and isinstance(controls.get(identifier), dict):
            require(controls[identifier].get("state") == "pass",
                    f"controls.{identifier} must pass because project.{flag} is true.")
    if has_ai is True:
        for identifier in ("ai_governance_and_testing",):
            if isinstance(controls.get(identifier), dict):
                require(controls[identifier].get("state") == "pass",
                        f"controls.{identifier} must pass for an AI product.")

    review = record.get("review")
    if not isinstance(review, dict):
        return errors + ["Missing review object."]
    require(review.get("decision") == "approved", "review.decision must be approved.")
    require(meaningful(review.get("independent_reviewer")), "review.independent_reviewer required.")
    require(date_valid(review.get("date")), "review.date must be ISO YYYY-MM-DD.")
    require(meaningful(review.get("release_ticket")), "review.release_ticket must identify a real release review.")
    if meaningful(project.get("accountable_owner")) and meaningful(review.get("independent_reviewer")):
        require(project["accountable_owner"].strip().casefold() != review["independent_reviewer"].strip().casefold(),
                "Independent reviewer must differ from the product owner.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=pathlib.Path, help="Path to compliance/PRODUCT_COMPLIANCE.json")
    args = parser.parse_args()
    try:
        record = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: could not read valid manifest: {exc}", file=sys.stderr)
        return 2
    errors = check(record)
    if errors:
        print(f"BLOCKED: {len(errors)} unresolved compliance record issue(s):", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    print("PASS: manifest structure/evidence references/review attestations recorded.")
    print("NOT A LEGAL CERTIFICATION: verify real evidence and independent approval before release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
