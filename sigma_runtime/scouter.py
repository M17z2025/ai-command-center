"""Sigma Scouter: strict open-source / unlimited-free candidate validation and discovery.

Discovery is intentionally separate from approval. Search hits enter REVIEW until their
licence, commercial-use rights, self-hostability and unlimited-use evidence are verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os

import yaml


class ScouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class CandidateDecision:
    candidate_id: str
    state: str
    reasons: tuple[str, ...]


class ScouterPolicy:
    def __init__(self, root: Path | str | None = None) -> None:
        self.repo_root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.policy_path = self.repo_root / "headquarters" / "scouter" / "policy.yaml"
        self.catalog_path = self.repo_root / "headquarters" / "scouter" / "catalog.yaml"
        self.policy = self._load(self.policy_path)
        self.catalog = self._load(self.catalog_path)
        if self.policy.get("schema_version") != 1:
            raise ScouterError("Unsupported Sigma Scouter policy schema")
        if self.catalog.get("schema_version") != 1:
            raise ScouterError("Unsupported Sigma Scouter catalog schema")

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ScouterError(f"Missing Sigma Scouter file: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ScouterError(f"Invalid YAML object: {path}")
        return data

    @property
    def required_fields(self) -> set[str]:
        return set(self.policy.get("required_candidate_fields", []))

    @property
    def accepted_licences(self) -> set[str]:
        classes = self.policy.get("licence_classes", {})
        accepted: set[str] = set()
        for key in ("permissive", "weak_copyleft", "strong_copyleft"):
            accepted.update(str(item) for item in classes.get(key, []))
        return accepted

    def validate_candidate(self, item: dict[str, Any]) -> CandidateDecision:
        candidate_id = str(item.get("id", "<missing-id>"))
        reasons: list[str] = []

        missing = sorted(field for field in self.required_fields if field not in item)
        if missing:
            return CandidateDecision(candidate_id, "REVIEW", (f"missing fields: {', '.join(missing)}",))

        state = str(item.get("state", "REVIEW"))
        licence = str(item.get("licence", ""))
        kind = str(item.get("kind", ""))
        self_hosted = bool(item.get("self_hosted"))
        unlimited_basis = str(item.get("unlimited_basis", "")).lower()
        evidence = item.get("evidence")

        if state not in {"ACCEPT", "FORK_CANDIDATE", "REVIEW", "REJECT"}:
            reasons.append(f"invalid state {state!r}")

        if not isinstance(evidence, list) or not evidence:
            reasons.append("no evidence records")

        if state in {"ACCEPT", "FORK_CANDIDATE"} and licence not in self.accepted_licences:
            reasons.append(f"licence {licence!r} is not in an accepted OSI/open licence class")

        if kind in {"application", "self_hosted_api", "library", "engine"} and state == "ACCEPT":
            if kind in {"application", "self_hosted_api"} and not self_hosted:
                reasons.append("accepted server application/API must be self-hostable")
            if self_hosted and "self-host" not in unlimited_basis:
                reasons.append("accepted self-hosted item must explain that vendor quota is removed by self-hosting")

        if kind == "public_api" and state == "ACCEPT":
            required_phrases = ("no rate limit", "no api key", "commercial")
            for phrase in required_phrases:
                if phrase not in unlimited_basis:
                    reasons.append(f"accepted public API unlimited_basis must include {phrase!r}")

        if item.get("requires_paid_core_dependency") is True and state in {"ACCEPT", "FORK_CANDIDATE"}:
            reasons.append("requires a paid dependency for the stated core use")

        final_state = "REVIEW" if reasons and state != "REJECT" else state
        return CandidateDecision(candidate_id, final_state, tuple(reasons))

    def validate_catalog(self) -> list[CandidateDecision]:
        items = self.catalog.get("candidates", [])
        if not isinstance(items, list):
            raise ScouterError("catalog candidates must be a list")
        seen: set[str] = set()
        decisions: list[CandidateDecision] = []
        for item in items:
            if not isinstance(item, dict):
                decisions.append(CandidateDecision("<invalid>", "REVIEW", ("candidate is not an object",)))
                continue
            candidate_id = str(item.get("id", ""))
            if candidate_id in seen:
                decisions.append(CandidateDecision(candidate_id, "REVIEW", ("duplicate candidate id",)))
                continue
            seen.add(candidate_id)
            decisions.append(self.validate_candidate(item))
        return decisions

    def list_candidates(self, state: str | None = None) -> list[dict[str, Any]]:
        items = [item for item in self.catalog.get("candidates", []) if isinstance(item, dict)]
        if state:
            items = [item for item in items if item.get("state") == state]
        return items

    def portfolio_queries(self) -> list[str]:
        return list(self.catalog.get("discovery_queries", []))


class SearXNGClient:
    """Minimal client for a private/self-hosted SearXNG JSON endpoint."""

    def __init__(self, base_url: str | None = None, timeout: int = 20) -> None:
        self.base_url = (base_url or os.environ.get("SIGMA_SCOUTER_SEARCH_URL", "")).rstrip("/")
        self.timeout = timeout
        if not self.base_url:
            raise ScouterError("SIGMA_SCOUTER_SEARCH_URL is not configured")

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        params = urlencode({"q": query, "format": "json", "language": "en"})
        req = Request(
            f"{self.base_url}/search?{params}",
            headers={"User-Agent": "Sigma-Scouter/1.0"},
        )
        with urlopen(req, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise ScouterError("Unexpected SearXNG response shape")
        cleaned: list[dict[str, Any]] = []
        for result in results[: max(1, limit)]:
            if not isinstance(result, dict):
                continue
            cleaned.append(
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "engine": result.get("engine"),
                    "state": "REVIEW",
                    "reason": "Discovery hit only; licence and unlimited-use evidence not yet verified.",
                }
            )
        return cleaned
