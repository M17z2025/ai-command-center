#!/usr/bin/env python3
"""Validate the Sigma universal expert mesh configuration."""

from __future__ import annotations

from pathlib import Path
import json

import jsonschema
import yaml


MESH_FILES = {
    "taxonomy": "headquarters/mesh/taxonomy.yaml",
    "leaders": "headquarters/mesh/leaders.yaml",
    "pipeline": "headquarters/mesh/pipeline.yaml",
    "evidence": "headquarters/mesh/evidence.yaml",
    "evolution": "headquarters/mesh/evolution.yaml",
    "cognitive_methods": "headquarters/mesh/cognitive-methods.yaml",
    "thinkers": "headquarters/mesh/thinkers.yaml",
}

REQUIRED_DOMAIN_IDS = {
    "mathematics-logic",
    "physics",
    "chemistry",
    "earth-space-sciences",
    "life-sciences",
    "computer-science",
    "artificial-intelligence",
    "software-engineering",
    "data-databases",
    "networks-cloud",
    "cyber-security",
    "quantum-computing",
    "aerospace-engineering",
    "mechanical-engineering",
    "electrical-electronic-engineering",
    "chemical-process-engineering",
    "civil-structural-engineering",
    "nuclear-engineering",
    "vehicle-naval-engineering",
    "mining-resources-engineering",
    "materials-metallurgy",
    "manufacturing-industrial",
    "industrial-product-design",
    "textiles-fashion-wearables",
    "anatomy-physiology",
    "internal-clinical-medicine",
    "surgery-anesthesia",
    "pathology-laboratory",
    "pharmacology-medicines",
    "genetics-genomics",
    "oncology-immunology",
    "neuroscience-neurology",
    "mental-behavioural-health",
    "public-population-health",
    "veterinary-science",
    "agriculture-agronomy",
    "food-science",
    "environment-sustainability",
    "natural-resources",
    "corporate-strategy",
    "operations-supply-chain",
    "people-hr",
    "marketing-sales-growth",
    "product-project-programme",
    "macro-micro-economics",
    "econometrics-quantitative-finance",
    "accounting-tax",
    "banking-investment-capital",
    "insurance-actuarial",
    "global-trade-commerce",
    "constitutional-public-law",
    "international-law",
    "corporate-commercial-law",
    "criminal-law",
    "civil-private-law",
    "intellectual-property-law",
    "regulatory-compliance",
    "jurisprudence-legal-history",
    "public-policy-administration",
    "geopolitics-international-relations",
    "political-theory-systems",
    "intelligence-analysis",
    "history",
    "archaeology-anthropology",
    "sociology",
    "psychology",
    "geography",
    "linguistics-philology",
    "philosophy",
    "theology-religion-mythology",
    "education-learning",
    "literature-writing",
    "music-audio",
    "visual-art-graphic-design",
    "ui-ux-interaction",
    "film-animation",
    "performing-arts",
    "architecture-built-design",
    "games-interactive-media",
    "research-methods",
    "evidence-verification",
    "systems-decision-science",
    "ethics-safety",
    "foresight-innovation",
}

REQUIRED_THINKER_IDS = {
    "alan-turing",
    "ada-lovelace",
    "john-von-neumann",
    "kurt-godel",
    "albert-einstein",
    "isaac-newton",
    "marie-curie",
    "charles-darwin",
    "aristotle",
    "plato",
    "sun-tzu",
    "carl-jung",
}

REQUIRED_ASSURANCE_ROLES = {
    "sigma-mission-router",
    "sigma-independent-critic",
    "sigma-evidence-verifier",
    "sigma-security-gatekeeper",
    "sigma-synthesis-director",
    "evaluation-evolution-controller",
}

REQUIRED_SECURITY_ROLES = {
    "security-master",
    "appsec-master",
    "identity-access-security-master",
    "tenant-data-isolation-master",
    "cloud-infrastructure-security-master",
    "network-edge-security-master",
    "supply-chain-security-master",
    "secrets-cryptography-master",
    "offensive-security-master",
    "detection-response-forensics-master",
    "ai-systems-security-master",
    "api-mobile-integration-security-master",
    "privacy-data-security-master",
    "resilience-recovery-security-master",
    "sigma-security-gatekeeper",
}


def _load_yaml(root: Path, rel: str, errors: list[str]):
    path = root / rel
    if not path.exists():
        errors.append(f"Missing Sigma mesh file: {rel}")
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - fail closed for malformed YAML
        errors.append(f"{rel} cannot be parsed: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{rel} must contain a YAML object")
        return None
    if data.get("schema_version") != 1:
        errors.append(f"{rel} must declare schema_version: 1")
    return data


def validate_mesh(root: Path) -> list[str]:
    errors: list[str] = []
    loaded = {name: _load_yaml(root, rel, errors) for name, rel in MESH_FILES.items()}

    taxonomy = loaded.get("taxonomy")
    leaders_cfg = loaded.get("leaders")
    pipeline = loaded.get("pipeline")
    evolution = loaded.get("evolution")
    cognitive_methods = loaded.get("cognitive_methods")
    thinkers_cfg = loaded.get("thinkers")

    domain_ids: set[str] = set()
    if taxonomy:
        pillar_ids: set[str] = set()
        for p_idx, pillar in enumerate(taxonomy.get("pillars", [])):
            if not isinstance(pillar, dict):
                errors.append(f"taxonomy pillar[{p_idx}] must be an object")
                continue
            pillar_id = pillar.get("id")
            if not pillar_id:
                errors.append(f"taxonomy pillar[{p_idx}] missing id")
            elif pillar_id in pillar_ids:
                errors.append(f"Duplicate taxonomy pillar id: {pillar_id}")
            else:
                pillar_ids.add(pillar_id)

            for d_idx, domain in enumerate(pillar.get("domains", [])):
                if not isinstance(domain, dict):
                    errors.append(f"taxonomy {pillar_id} domain[{d_idx}] must be an object")
                    continue
                domain_id = domain.get("id")
                if not domain_id:
                    errors.append(f"taxonomy {pillar_id} domain[{d_idx}] missing id")
                    continue
                if domain_id in domain_ids:
                    errors.append(f"Duplicate taxonomy domain id: {domain_id}")
                domain_ids.add(domain_id)
                subjects = domain.get("subjects")
                if not isinstance(subjects, list) or not subjects:
                    errors.append(f"taxonomy domain {domain_id} must have non-empty subjects")

        missing_domains = sorted(REQUIRED_DOMAIN_IDS - domain_ids)
        if missing_domains:
            errors.append(
                "Taxonomy missing required owner-requested domain coverage: "
                + ", ".join(missing_domains)
            )

        coverage = taxonomy.get("coverage_policy", {})
        if coverage.get("unknown_subject_flow") is None:
            errors.append("taxonomy coverage_policy must define unknown_subject_flow")

    leader_ids: set[str] = set()
    if leaders_cfg:
        all_nodes = []
        for section in ("leaders", "assurance_roles"):
            nodes = leaders_cfg.get(section, [])
            if not isinstance(nodes, list):
                errors.append(f"leaders.yaml {section} must be a list")
                continue
            for idx, node in enumerate(nodes):
                if not isinstance(node, dict):
                    errors.append(f"leaders.yaml {section}[{idx}] must be an object")
                    continue
                node_id = node.get("id")
                if not node_id:
                    errors.append(f"leaders.yaml {section}[{idx}] missing id")
                    continue
                if node_id in leader_ids:
                    errors.append(f"Duplicate Sigma leader/assurance id: {node_id}")
                leader_ids.add(node_id)
                all_nodes.append(node)

        missing_roles = sorted(REQUIRED_ASSURANCE_ROLES - leader_ids)
        if missing_roles:
            errors.append("Missing required assurance roles: " + ", ".join(missing_roles))

        missing_security_roles = sorted(REQUIRED_SECURITY_ROLES - leader_ids)
        if missing_security_roles:
            errors.append(
                "Missing required Sigma Cybersecurity Division roles: "
                + ", ".join(missing_security_roles)
            )

        core_registry_ids: set[str] = set()
        core_registry_path = root / "headquarters/agents/registry.yaml"
        if core_registry_path.exists():
            try:
                core_registry = yaml.safe_load(core_registry_path.read_text(encoding="utf-8")) or {}
                core_registry_ids = {
                    agent.get("id")
                    for agent in core_registry.get("agents", [])
                    if isinstance(agent, dict) and agent.get("id")
                }
            except Exception as exc:
                errors.append(f"headquarters/agents/registry.yaml cannot be parsed: {exc}")

        valid_parents = leader_ids | core_registry_ids | {"sigma-governor"}
        for node in all_nodes:
            node_id = node.get("id")
            parent = node.get("parent")
            if parent not in valid_parents:
                errors.append(f"{node_id} references unknown parent {parent!r}")
            for domain_id in node.get("domains", []):
                if domain_id not in domain_ids:
                    errors.append(f"{node_id} references unknown taxonomy domain {domain_id!r}")

        covered_domains = {
            domain_id
            for node in all_nodes
            for domain_id in node.get("domains", [])
            if isinstance(domain_id, str)
        }
        uncovered_required = sorted(REQUIRED_DOMAIN_IDS - covered_domains)
        if uncovered_required:
            errors.append(
                "Required taxonomy domains without a registered leader: "
                + ", ".join(uncovered_required)
            )

        factory = leaders_cfg.get("global_team_factory", {})
        if factory.get("child_may_outrank_parent") is not False:
            errors.append("global_team_factory.child_may_outrank_parent must be false")
        if not factory.get("required_temporary_fields"):
            errors.append("global_team_factory must define required_temporary_fields")

    if pipeline:
        stage_ids = [s.get("id") for s in pipeline.get("stages", []) if isinstance(s, dict)]
        required_stages = {
            "authority-check",
            "mission-decomposition",
            "expert-routing",
            "cognitive-lens-selection",
            "team-formation",
            "parallel-analysis",
            "adversarial-critique",
            "evidence-verification",
            "security-assurance",
            "synthesis",
            "execution-gate",
            "postmortem",
        }
        missing_stages = sorted(required_stages - set(stage_ids))
        if missing_stages:
            errors.append("Mesh pipeline missing required stages: " + ", ".join(missing_stages))

    if evolution:
        forbidden = set(evolution.get("forbidden", []))
        if "silent production self-rewrite" not in forbidden:
            errors.append("Evolution policy must forbid silent production self-rewrite")
        if "silent permission expansion" not in forbidden:
            errors.append("Evolution policy must forbid silent permission expansion")
        requirements = set(evolution.get("promotion_requirements", []))
        if "candidate cannot evaluate or promote itself" not in requirements:
            errors.append("Evolution promotion must require independent evaluation")

    method_ids: set[str] = set()
    if cognitive_methods:
        for idx, method in enumerate(cognitive_methods.get("methods", [])):
            if not isinstance(method, dict) or not method.get("id"):
                errors.append(f"cognitive-methods method[{idx}] missing id")
                continue
            method_id = method["id"]
            if method_id in method_ids:
                errors.append(f"Duplicate cognitive method id: {method_id}")
            method_ids.add(method_id)

    if thinkers_cfg:
        thinker_ids: set[str] = set()
        for idx, thinker in enumerate(thinkers_cfg.get("thinkers", [])):
            if not isinstance(thinker, dict):
                errors.append(f"thinkers.yaml thinker[{idx}] must be an object")
                continue
            thinker_id = thinker.get("id")
            if not thinker_id:
                errors.append(f"thinkers.yaml thinker[{idx}] missing id")
                continue
            if thinker_id in thinker_ids:
                errors.append(f"Duplicate thinker id: {thinker_id}")
            thinker_ids.add(thinker_id)

            for domain_id in thinker.get("primary_domains", []):
                if domain_id not in domain_ids:
                    errors.append(
                        f"Thinker {thinker_id} references unknown taxonomy domain {domain_id!r}"
                    )
            for method_id in thinker.get("cognitive_methods", []):
                if method_id not in method_ids:
                    errors.append(
                        f"Thinker {thinker_id} references unknown cognitive method {method_id!r}"
                    )

        missing_thinkers = sorted(REQUIRED_THINKER_IDS - thinker_ids)
        if missing_thinkers:
            errors.append("Missing required Thinkers Council profiles: " + ", ".join(missing_thinkers))

        policy = thinkers_cfg.get("policy", {})
        if policy.get("not_personas") is not True or policy.get("not_human_recreations") is not True:
            errors.append("Thinkers Council must explicitly prohibit persona/human recreation claims")

    expert_schema_path = root / "schemas/sigma-expert.schema.json"
    expert_template_path = root / "templates/sigma-expert.yaml"
    if not expert_schema_path.exists():
        errors.append("Missing schemas/sigma-expert.schema.json")
    if not expert_template_path.exists():
        errors.append("Missing templates/sigma-expert.yaml")
    if expert_schema_path.exists() and expert_template_path.exists():
        try:
            schema = json.loads(expert_schema_path.read_text(encoding="utf-8"))
            template = yaml.safe_load(expert_template_path.read_text(encoding="utf-8"))
            jsonschema.validate(template, schema)
            for method_id in template.get("expert", {}).get("cognitive_methods", []):
                if method_id not in method_ids:
                    errors.append(
                        f"Sigma expert template references unknown cognitive method {method_id!r}"
                    )
        except Exception as exc:
            errors.append(f"Sigma expert template/schema validation failed: {exc}")

    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    failures = validate_mesh(root)
    if failures:
        print("Sigma mesh validation FAILED")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("Sigma mesh validation PASSED")
