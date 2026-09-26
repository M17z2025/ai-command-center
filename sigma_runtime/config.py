"""Load and index Sigma mesh governance configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class MeshConfigError(RuntimeError):
    pass


class MeshConfig:
    FILES = {
        "taxonomy": "taxonomy.yaml",
        "leaders": "leaders.yaml",
        "pipeline": "pipeline.yaml",
        "evidence": "evidence.yaml",
        "evolution": "evolution.yaml",
        "methods": "cognitive-methods.yaml",
        "thinkers": "thinkers.yaml",
    }

    def __init__(self, root: Path | str | None = None) -> None:
        repo_root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.repo_root = repo_root
        self.mesh_dir = repo_root / "headquarters" / "mesh"
        self.raw: dict[str, dict[str, Any]] = {
            key: self._load(self.mesh_dir / filename)
            for key, filename in self.FILES.items()
        }

        self.domains: dict[str, dict[str, Any]] = {}
        self.pillar_by_domain: dict[str, str] = {}
        for pillar in self.raw["taxonomy"].get("pillars", []):
            pillar_id = pillar["id"]
            for domain in pillar.get("domains", []):
                self.domains[domain["id"]] = domain
                self.pillar_by_domain[domain["id"]] = pillar_id

        self.leaders: dict[str, dict[str, Any]] = {}
        self.leaders_for_domain: dict[str, list[dict[str, Any]]] = {}
        for section in ("leaders", "assurance_roles"):
            for leader in self.raw["leaders"].get(section, []):
                self.leaders[leader["id"]] = leader
                for domain_id in leader.get("domains", []):
                    self.leaders_for_domain.setdefault(domain_id, []).append(leader)

        self.methods = {
            item["id"]: item for item in self.raw["methods"].get("methods", [])
        }
        self.thinkers = {
            item["id"]: item for item in self.raw["thinkers"].get("thinkers", [])
        }

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise MeshConfigError(f"Missing mesh configuration: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise MeshConfigError(f"Invalid mesh configuration: {path}")
        return data

    def compact_domain_catalog(self) -> list[dict[str, str]]:
        return [
            {"id": domain_id, "name": domain.get("name", domain_id)}
            for domain_id, domain in self.domains.items()
        ]

    def leaders_for(
        self,
        domain_id: str,
        prompt: str = "",
        *,
        max_leaders: int = 3,
    ) -> list[dict[str, Any]]:
        candidates = self.leaders_for_domain.get(domain_id, [])
        if candidates:
            lowered = prompt.lower()
            scored: list[tuple[int, int, int, dict[str, Any]]] = []
            for index, candidate in enumerate(candidates):
                keywords = [
                    str(item).lower()
                    for item in candidate.get("routing_keywords", [])
                    if str(item).strip()
                ]
                hits = sum(1 for keyword in keywords if keyword in lowered)
                if hits:
                    priority = int(candidate.get("routing_priority", 0) or 0)
                    scored.append((hits, priority, -index, candidate))
            if scored:
                scored.sort(key=lambda item: (-item[0], -item[1], -item[2]))
                return [item[3] for item in scored[:max(1, max_leaders)]]
            return [candidates[0]]

        fallback = self.leaders.get("research-director")
        if not fallback:
            raise MeshConfigError(f"No leader for domain {domain_id}")
        return [fallback]

    def leader_for(self, domain_id: str, prompt: str = "") -> dict[str, Any]:
        return self.leaders_for(domain_id, prompt, max_leaders=1)[0]

    @staticmethod
    def is_development_mission(prompt: str) -> bool:
        lowered = prompt.lower()
        development_terms = (
            "build", "develop", "development", "code", "coding", "software",
            "app", "application", "website", "platform", "feature", "fix",
            "refactor", "deploy", "release", "product", "implementation",
            "architecture", "user journey", "roadmap", "backlog", "pull plan",
        )
        return any(term in lowered for term in development_terms)

    def risk_gates_for(self, domain_ids: list[str], prompt: str) -> list[str]:
        domain_set = set(domain_ids)
        pillar_set = {
            self.pillar_by_domain[d] for d in domain_ids if d in self.pillar_by_domain
        }
        gates: list[str] = []
        for gate_name, gate in self.raw["pipeline"].get("risk_gates", {}).items():
            triggers = set(gate.get("triggers", []))
            if triggers & domain_set or triggers & pillar_set:
                gates.append(gate_name)

        lowered = prompt.lower()
        production_terms = (
            "deploy", "production", "delete", "drop database", "secret",
            "credential", "pay ", "payment", "transfer money", "purchase",
        )
        if any(term in lowered for term in production_terms):
            gates.append("production_action")
        return list(dict.fromkeys(gates))

    def public_summary(self) -> dict[str, Any]:
        return {
            "taxonomy_id": self.raw["taxonomy"].get("taxonomy_id"),
            "pipeline_id": self.raw["pipeline"].get("pipeline_id"),
            "evolution_policy_id": self.raw["evolution"].get("evolution_policy_id"),
            "domains": len(self.domains),
            "leaders": len(self.leaders),
            "thinkers": len(self.thinkers),
            "methods": len(self.methods),
        }
