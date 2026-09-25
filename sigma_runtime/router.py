"""Deterministic mission routing and bounded team formation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any
import uuid

from .config import MeshConfig


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


@dataclass
class Specialist:
    id: str
    parent: str
    mission: str
    domain_scope: list[str]
    allowed_tools: list[str]
    prohibited_actions: list[str]
    evidence_requirements: list[str]
    expiry_or_review_condition: str


@dataclass
class MissionPlan:
    mission_id: str
    domains: list[str]
    leaders: list[str]
    thinkers: list[str]
    cognitive_methods: list[str]
    specialists: list[Specialist]
    risk_gates: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


class MissionRouter:
    def __init__(self, config: MeshConfig) -> None:
        self.config = config

    def route(self, prompt: str, *, max_domains: int = 4) -> MissionPlan:
        mission_id = str(uuid.uuid4())
        prompt_tokens = tokens(prompt)
        scored: list[tuple[int, str]] = []

        for domain_id, domain in self.config.domains.items():
            domain_tokens = tokens(domain.get("name", "")) | tokens(domain_id.replace("-", " "))
            subject_tokens: set[str] = set()
            phrase_bonus = 0
            lowered = prompt.lower()
            for subject in domain.get("subjects", []):
                subject_tokens |= tokens(subject)
                if subject.lower() in lowered:
                    phrase_bonus += 4
            score = (
                3 * len(prompt_tokens & domain_tokens)
                + len(prompt_tokens & subject_tokens)
                + phrase_bonus
            )
            if score > 0:
                scored.append((score, domain_id))

        scored.sort(key=lambda item: (-item[0], item[1]))
        if not scored:
            selected = ["research-methods", "evidence-verification"]
        else:
            best = scored[0][0]
            selected = [
                domain_id
                for score, domain_id in scored
                if score >= max(1, int(best * 0.45))
            ][:max_domains]

        leader_ids: list[str] = []
        specialists: list[Specialist] = []
        factory = self.config.raw["leaders"].get("global_team_factory", {})
        prohibitions = list(factory.get("default_prohibited_actions", []))

        for domain_id in selected:
            leader = self.config.leader_for(domain_id)
            leader_id = leader["id"]
            if leader_id not in leader_ids:
                leader_ids.append(leader_id)
            specialists.append(
                Specialist(
                    id=f"temp-{mission_id[:8]}-{domain_id}"[:96],
                    parent=leader_id,
                    mission=f"Analyze the mission only within the {domain_id} scope.",
                    domain_scope=[domain_id],
                    allowed_tools=["model-inference", "mission-evidence"],
                    prohibited_actions=prohibitions,
                    evidence_requirements=["follow headquarters/mesh/evidence.yaml"],
                    expiry_or_review_condition="expires when the mission closes",
                )
            )

        thinker_scores: list[tuple[int, str]] = []
        selected_set = set(selected)
        lowered = prompt.lower()
        for thinker_id, thinker in self.config.thinkers.items():
            overlap = len(selected_set & set(thinker.get("primary_domains", [])))
            score = overlap * 3
            if thinker_id == "sun-tzu" and any(x in lowered for x in ("strategy", "negotiat", "compet", "advantage")):
                score += 3
            if thinker_id == "kurt-godel" and any(x in lowered for x in ("proof", "limit", "certainty", "formal")):
                score += 3
            if thinker_id == "albert-einstein" and any(x in lowered for x in ("reframe", "physics", "thought experiment")):
                score += 2
            if score > 0:
                thinker_scores.append((score, thinker_id))
        thinker_scores.sort(key=lambda item: (-item[0], item[1]))
        thinker_ids = [item[1] for item in thinker_scores[:4]]
        if not thinker_ids:
            thinker_ids = ["aristotle", "alan-turing"]

        method_ids: list[str] = []
        for thinker_id in thinker_ids:
            for method_id in self.config.thinkers[thinker_id].get("cognitive_methods", []):
                if method_id not in method_ids:
                    method_ids.append(method_id)

        return MissionPlan(
            mission_id=mission_id,
            domains=selected,
            leaders=leader_ids,
            thinkers=thinker_ids,
            cognitive_methods=method_ids,
            specialists=specialists,
            risk_gates=self.config.risk_gates_for(selected, prompt),
        )
