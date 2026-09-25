"""Operational Sigma multi-agent orchestration loop."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import Any

from .config import MeshConfig
from .provider import CompletionRequest, ModelProvider, ProviderError
from .router import MissionPlan, MissionRouter, Specialist
from .store import MissionStore


MAX_PROMPT_CHARS = 50000
MAX_ARTIFACT_CHARS = 20000


def _bounded(text: str, limit: int = MAX_ARTIFACT_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + "\n[truncated]"


def _verdict(text: str) -> str:
    upper = text.upper()
    if "VERDICT: PASS" in upper:
        return "PASS"
    return "REPAIR"


class SigmaOrchestrator:
    def __init__(
        self,
        config: MeshConfig,
        router: MissionRouter,
        provider: ModelProvider,
        store: MissionStore,
    ) -> None:
        self.config = config
        self.router = router
        self.provider = provider
        self.store = store

    def plan(self, prompt: str) -> dict[str, Any]:
        self._validate_prompt(prompt)
        return self.router.route(prompt).to_dict()

    def run(
        self,
        prompt: str,
        *,
        evidence: list[dict[str, Any]] | None = None,
        requested_by: str = "owner",
        max_cycles: int = 2,
    ) -> dict[str, Any]:
        self._validate_prompt(prompt)
        max_cycles = max(0, min(int(max_cycles), 3))
        plan = self.router.route(prompt)
        mission_id = plan.mission_id
        evidence = evidence or []
        self.store.create_mission(mission_id, prompt, requested_by, plan.to_dict())
        self.store.event(mission_id, "authority-check", {"requested_by": requested_by, "risk_gates": plan.risk_gates})
        self.store.event(mission_id, "expert-routing", {
            "domains": plan.domains,
            "leaders": plan.leaders,
            "thinkers": plan.thinkers,
            "methods": plan.cognitive_methods,
        })
        self.store.event(mission_id, "team-formation", {
            "specialists": [item.id for item in plan.specialists]
        })

        try:
            outputs = self._parallel_analysis(plan, prompt, evidence)
            for specialist_id, output in outputs.items():
                self.store.artifact(mission_id, f"expert/{specialist_id}", _bounded(output))

            critic = ""
            verifier = ""
            for cycle in range(max_cycles + 1):
                critic = self._critic(plan, prompt, outputs)
                verifier = self._verify(plan, prompt, outputs, critic, evidence)
                self.store.event(mission_id, "adversarial-critique", {
                    "cycle": cycle, "verdict": _verdict(critic), "text": _bounded(critic, 8000)
                })
                self.store.event(mission_id, "evidence-verification", {
                    "cycle": cycle, "verdict": _verdict(verifier), "text": _bounded(verifier, 8000)
                })
                if _verdict(critic) == "PASS" and _verdict(verifier) == "PASS":
                    break
                if cycle >= max_cycles:
                    break
                outputs = self._repair(plan, prompt, outputs, critic, verifier, evidence)
                self.store.event(mission_id, "repair-loop", {"cycle": cycle + 1})

            final = self._synthesize(plan, prompt, outputs, critic, verifier, evidence)
            unresolved = _verdict(critic) != "PASS" or _verdict(verifier) != "PASS"
            status = "COMPLETE_WITH_UNVERIFIED_ITEMS" if unresolved else "COMPLETE"
            self.store.artifact(mission_id, "final", _bounded(final, 50000))
            self.store.finish(mission_id, status, final_output=final)
            self.store.event(mission_id, "synthesis", {"status": status})

            postmortem = self._postmortem(plan, prompt, status, critic, verifier)
            self.store.artifact(mission_id, "postmortem", _bounded(postmortem, 10000))
            lesson = self._extract_lesson(postmortem)
            if lesson:
                lesson_id = self.store.add_lesson(
                    mission_id,
                    lesson,
                    {"status": status, "promotion": "requires independent evaluation"},
                )
                self.store.event(mission_id, "learning-candidate", {"lesson_id": lesson_id})

            return self.store.get_mission(mission_id) or {"id": mission_id, "status": status}
        except Exception as exc:
            self.store.finish(mission_id, "FAILED", error=str(exc))
            self.store.event(mission_id, "failed", {"error": str(exc)})
            raise

    def _parallel_analysis(
        self,
        plan: MissionPlan,
        prompt: str,
        evidence: list[dict[str, Any]],
    ) -> dict[str, str]:
        outputs: dict[str, str] = {}
        workers = max(1, min(len(plan.specialists), 6))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(self._analyze, plan, specialist, prompt, evidence): specialist
                for specialist in plan.specialists
            }
            for future in as_completed(futures):
                specialist = futures[future]
                outputs[specialist.id] = future.result()
        return outputs

    def _analyze(
        self,
        plan: MissionPlan,
        specialist: Specialist,
        prompt: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        domain_id = specialist.domain_scope[0]
        domain = self.config.domains[domain_id]
        leader = self.config.leaders.get(specialist.parent, {})
        thinker_text = ", ".join(plan.thinkers)
        method_text = ", ".join(plan.cognitive_methods)
        system = (
            f"You are a bounded Sigma specialist for {domain.get('name', domain_id)}. "
            f"Parent leader: {leader.get('name', specialist.parent)}. "
            "Work only within your assigned scope. State assumptions and uncertainty. "
            "Do not invent sources. Historical Thinkers are reasoning methods, never personas. "
            "Do not perform external actions; provide analysis/advice only."
        )
        user = (
            f"MISSION:\n{prompt}\n\n"
            f"COGNITIVE LENSES: {thinker_text}\nMETHODS: {method_text}\n"
            f"MISSION EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False)[:16000]}\n\n"
            "Return a concise expert analysis, dependencies, risks, assumptions and what must be verified."
        )
        return self.provider.complete(
            CompletionRequest("analysis", system, user, {"domain": domain_id, "specialist": specialist.id})
        )

    def _critic(self, plan: MissionPlan, prompt: str, outputs: dict[str, str]) -> str:
        system = (
            "You are Sigma Independent Critic. You are independent from the primary team. "
            "Attempt to falsify the analyses, find contradictions, hidden assumptions, unsafe leaps "
            "and missing failure cases. Start with exactly VERDICT: PASS or VERDICT: REPAIR."
        )
        user = f"MISSION:\n{prompt}\n\nANALYSES:\n{json.dumps(outputs, ensure_ascii=False)[:50000]}"
        return self.provider.complete(CompletionRequest("critic", system, user))

    def _verify(
        self,
        plan: MissionPlan,
        prompt: str,
        outputs: dict[str, str],
        critic: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        system = (
            "You are Sigma Evidence Verifier. Check whether material claims are actually supported "
            "by the supplied mission evidence, whether dates/jurisdictions/populations match, and "
            "whether current verification is still required. Never manufacture citations. "
            "Start with exactly VERDICT: PASS if the synthesis can safely preserve limitations, "
            "otherwise VERDICT: REPAIR."
        )
        user = (
            f"MISSION:\n{prompt}\n\nEVIDENCE:\n{json.dumps(evidence, ensure_ascii=False)[:25000]}\n\n"
            f"ANALYSES:\n{json.dumps(outputs, ensure_ascii=False)[:35000]}\n\nCRITIC:\n{critic[:10000]}"
        )
        return self.provider.complete(CompletionRequest("verifier", system, user))

    def _repair(
        self,
        plan: MissionPlan,
        prompt: str,
        outputs: dict[str, str],
        critic: str,
        verifier: str,
        evidence: list[dict[str, Any]],
    ) -> dict[str, str]:
        repaired: dict[str, str] = {}
        for specialist in plan.specialists:
            prior = outputs.get(specialist.id, "")
            system = (
                "You are repairing a Sigma expert analysis after independent criticism. "
                "Address the findings directly, preserve uncertainty and do not invent evidence."
            )
            user = (
                f"MISSION:\n{prompt}\n\nPRIOR ANALYSIS:\n{prior[:16000]}\n\n"
                f"CRITIC:\n{critic[:8000]}\n\nVERIFIER:\n{verifier[:8000]}\n\n"
                f"EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False)[:12000]}"
            )
            repaired[specialist.id] = self.provider.complete(
                CompletionRequest("repair", system, user, {"domain": specialist.domain_scope[0]})
            )
        return repaired

    def _synthesize(
        self,
        plan: MissionPlan,
        prompt: str,
        outputs: dict[str, str],
        critic: str,
        verifier: str,
        evidence: list[dict[str, Any]],
    ) -> str:
        system = (
            "You are Sigma Synthesis Director. Merge the verified expert work into one coherent answer. "
            "Preserve material disagreements and uncertainty. Separate facts, assumptions and proposals. "
            "Explicitly identify owner-gated or professional-review actions. Do not claim verification "
            "that the Evidence Verifier did not establish."
        )
        user = (
            f"MISSION:\n{prompt}\n\nRISK GATES: {plan.risk_gates}\n"
            f"EXPERT OUTPUTS:\n{json.dumps(outputs, ensure_ascii=False)[:45000]}\n\n"
            f"CRITIC:\n{critic[:10000]}\n\nVERIFIER:\n{verifier[:10000]}\n\n"
            f"EVIDENCE COUNT: {len(evidence)}"
        )
        return self.provider.complete(CompletionRequest("synthesis", system, user))

    def _postmortem(
        self,
        plan: MissionPlan,
        prompt: str,
        status: str,
        critic: str,
        verifier: str,
    ) -> str:
        system = (
            "You are Sigma Evaluation & Evolution Controller. Produce a short postmortem. "
            "Any reusable improvement must be a CANDIDATE only and cannot self-promote. "
            "Include at most one line beginning LESSON:."
        )
        user = (
            f"MISSION SUMMARY: {prompt[:6000]}\nSTATUS: {status}\n"
            f"DOMAINS: {plan.domains}\nCRITIC: {critic[:5000]}\nVERIFIER: {verifier[:5000]}"
        )
        return self.provider.complete(CompletionRequest("postmortem", system, user))

    @staticmethod
    def _extract_lesson(postmortem: str) -> str | None:
        for line in postmortem.splitlines():
            if line.strip().upper().startswith("LESSON:"):
                value = line.split(":", 1)[1].strip()
                return value or None
        return None

    @staticmethod
    def _validate_prompt(prompt: str) -> None:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Mission prompt is required")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise ValueError(f"Mission prompt exceeds {MAX_PROMPT_CHARS} characters")
