"""Governed Sigma knowledge-memory interfaces and adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MemoryEpisode:
    id: str
    title: str
    content: str
    source: str
    source_type: str
    project: str | None = None
    reference_time: str = field(default_factory=utcnow)
    classification: str = "internal"
    provenance: dict[str, str] = field(default_factory=dict)
    status: str = "RAW"

    @classmethod
    def create(
        cls,
        *,
        title: str,
        content: str,
        source: str,
        source_type: str,
        project: str | None = None,
        classification: str = "internal",
        provenance: dict[str, str] | None = None,
        status: str = "RAW",
    ) -> "MemoryEpisode":
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            source=source,
            source_type=source_type,
            project=project,
            classification=classification,
            provenance=provenance or {},
            status=status,
        )


@dataclass(frozen=True)
class MemoryQuery:
    text: str
    project: str | None = None
    limit: int = 8
    include_candidate: bool = False


@dataclass(frozen=True)
class MemoryResult:
    text: str
    score: float | None = None
    source: str = ""
    project: str | None = None
    valid_at: str | None = None
    invalid_at: str | None = None
    provenance: dict[str, str] = field(default_factory=dict)
    status: str = "PROMOTED"


class KnowledgeMemory(Protocol):
    adapter_id: str

    def health(self) -> dict[str, Any]:
        ...

    def add_episode(self, episode: MemoryEpisode) -> dict[str, Any]:
        ...

    def search(self, query: MemoryQuery) -> list[MemoryResult]:
        ...


class NullKnowledgeMemory:
    """Fail-safe no-memory adapter."""

    adapter_id = "null-memory"

    def health(self) -> dict[str, Any]:
        return {"status": "disabled", "adapter": self.adapter_id}

    def add_episode(self, episode: MemoryEpisode) -> dict[str, Any]:
        return {"status": "ignored", "episode_id": episode.id}

    def search(self, query: MemoryQuery) -> list[MemoryResult]:
        return []


class DeterministicKnowledgeMemory:
    """In-process deterministic adapter for CI and contract tests."""

    adapter_id = "deterministic-memory"

    def __init__(self) -> None:
        self.episodes: list[MemoryEpisode] = []

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "adapter": self.adapter_id,
            "episodes": len(self.episodes),
        }

    def add_episode(self, episode: MemoryEpisode) -> dict[str, Any]:
        self.episodes.append(episode)
        return {"status": "stored", "episode_id": episode.id}

    def search(self, query: MemoryQuery) -> list[MemoryResult]:
        words = {item.lower() for item in query.text.split() if item.strip()}
        scored: list[tuple[int, MemoryEpisode]] = []
        for episode in self.episodes:
            if query.project and episode.project not in {None, query.project}:
                continue
            if not query.include_candidate and episode.status not in {"VERIFIED", "PROMOTED"}:
                continue
            haystack = f"{episode.title} {episode.content}".lower()
            score = sum(1 for word in words if word in haystack)
            if score:
                scored.append((score, episode))
        scored.sort(key=lambda item: (-item[0], item[1].reference_time))
        return [
            MemoryResult(
                text=episode.content,
                score=float(score),
                source=episode.source,
                project=episode.project,
                valid_at=episode.reference_time,
                provenance=episode.provenance,
                status=episode.status,
            )
            for score, episode in scored[: max(1, min(query.limit, 50))]
        ]


class HTTPKnowledgeMemory:
    """Private HTTP adapter for the Sigma Graphiti memory service."""

    adapter_id = "graphiti-http-memory"

    def __init__(
        self,
        endpoint: str,
        token: str | None = None,
        *,
        timeout: int = 120,
    ) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("SIGMA_MEMORY_ENDPOINT must be absolute HTTP(S)")
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "sigma-memory-client/1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(
            self.endpoint + path,
            headers=headers,
            data=data,
            method=method,
        )
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:600]
            raise RuntimeError(
                f"Sigma memory service HTTP {exc.code}: {detail}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Sigma memory service failed: {exc}") from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def add_episode(self, episode: MemoryEpisode) -> dict[str, Any]:
        return self._request("POST", "/episodes", asdict(episode))

    def search(self, query: MemoryQuery) -> list[MemoryResult]:
        payload = self._request("POST", "/search", asdict(query))
        results = payload.get("results", [])
        return [MemoryResult(**item) for item in results]


def memory_from_env() -> KnowledgeMemory:
    mode = os.getenv("SIGMA_MEMORY_PROVIDER", "none").strip().lower()
    if mode in {"", "none", "disabled"}:
        return NullKnowledgeMemory()
    if mode == "test":
        if os.getenv("SIGMA_ALLOW_TEST_PROVIDER") != "1":
            raise RuntimeError("Test memory provider is disabled")
        return DeterministicKnowledgeMemory()
    if mode != "graphiti":
        raise RuntimeError(f"Unsupported SIGMA_MEMORY_PROVIDER: {mode}")
    endpoint = os.getenv("SIGMA_MEMORY_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError("SIGMA_MEMORY_ENDPOINT is required for Graphiti memory")
    return HTTPKnowledgeMemory(
        endpoint,
        os.getenv("SIGMA_MEMORY_TOKEN") or None,
        timeout=int(os.getenv("SIGMA_MEMORY_TIMEOUT_SECONDS", "120")),
    )
