#!/usr/bin/env python3
"""Private Graphiti-backed memory service for Sigma.

This service is intentionally small: health, episode ingestion and search.
It is expected to run only on Sigma's private Docker network.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from typing import Any
from urllib.parse import urlparse

from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.nodes import EpisodeType


MAX_BODY = 250_000


class MemoryApp:
    def __init__(self) -> None:
        self.driver = FalkorDriver(
            host=os.getenv("FALKORDB_HOST", "falkordb"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            username=os.getenv("FALKORDB_USERNAME") or None,
            password=os.getenv("FALKORDB_PASSWORD") or None,
        )
        llm_endpoint = os.getenv("SIGMA_MEMORY_LLM_BASE_URL", "http://ollama:11434/v1")
        llm_model = os.getenv("SIGMA_MEMORY_LLM_MODEL", "").strip()
        embedding_model = os.getenv("SIGMA_MEMORY_EMBEDDING_MODEL", "").strip()
        if not llm_model:
            raise RuntimeError("SIGMA_MEMORY_LLM_MODEL is required")
        if not embedding_model:
            raise RuntimeError("SIGMA_MEMORY_EMBEDDING_MODEL is required")

        api_key = os.getenv("SIGMA_MEMORY_LLM_API_KEY", "ollama")
        llm = OpenAIGenericClient(
            config=LLMConfig(
                api_key=api_key,
                model=llm_model,
                small_model=llm_model,
                base_url=llm_endpoint,
                temperature=0.1,
            ),
            structured_output_mode=os.getenv(
                "SIGMA_MEMORY_STRUCTURED_OUTPUT_MODE", "json_object"
            ),
        )
        embedder = OpenAIEmbedder(
            OpenAIEmbedderConfig(
                api_key=os.getenv("SIGMA_MEMORY_EMBEDDING_API_KEY", "ollama"),
                base_url=os.getenv(
                    "SIGMA_MEMORY_EMBEDDING_BASE_URL", "http://ollama:11434/v1"
                ),
                embedding_model=embedding_model,
                embedding_dim=int(os.getenv("SIGMA_MEMORY_EMBEDDING_DIM", "1024")),
            )
        )
        self.graphiti = Graphiti(
            graph_driver=self.driver,
            llm_client=llm,
            embedder=embedder,
        )
        asyncio.run(self.graphiti.build_indices_and_constraints())

    def add_episode(self, payload: dict[str, Any]) -> dict[str, Any]:
        reference_time = datetime.fromisoformat(
            str(payload["reference_time"]).replace("Z", "+00:00")
        )
        project = payload.get("project") or "global"
        metadata = {
            "sigma_episode_id": payload["id"],
            "source": payload["source"],
            "source_type": payload["source_type"],
            "classification": payload.get("classification", "internal"),
            "status": payload.get("status", "RAW"),
            "provenance": payload.get("provenance") or {},
        }
        body = json.dumps(
            {
                "content": payload["content"],
                "metadata": metadata,
            },
            ensure_ascii=False,
        )
        asyncio.run(
            self.graphiti.add_episode(
                name=str(payload["title"]),
                episode_body=body,
                source=EpisodeType.json,
                source_description=str(payload["source"]),
                reference_time=reference_time,
                group_id=project,
            )
        )
        return {"status": "stored", "episode_id": payload["id"], "project": project}

    def search(self, payload: dict[str, Any]) -> dict[str, Any]:
        project = payload.get("project")
        limit = max(1, min(int(payload.get("limit", 8)), 50))
        results = asyncio.run(
            self.graphiti.search(
                str(payload["text"]),
                group_ids=[project] if project else None,
                num_results=limit,
            )
        )
        mapped = []
        for result in results:
            mapped.append(
                {
                    "text": result.fact,
                    "score": getattr(result, "score", None),
                    "source": "graphiti",
                    "project": project,
                    "valid_at": (
                        result.valid_at.isoformat()
                        if getattr(result, "valid_at", None)
                        else None
                    ),
                    "invalid_at": (
                        result.invalid_at.isoformat()
                        if getattr(result, "invalid_at", None)
                        else None
                    ),
                    "provenance": {
                        "edge_uuid": str(getattr(result, "uuid", "")),
                        "source_node_uuid": str(
                            getattr(result, "source_node_uuid", "")
                        ),
                    },
                    "status": "PROMOTED",
                }
            )
        return {"results": mapped}

    def close(self) -> None:
        asyncio.run(self.graphiti.close())


def build_server(app: MemoryApp) -> ThreadingHTTPServer:
    token = os.getenv("SIGMA_MEMORY_TOKEN") or None
    host = os.getenv("SIGMA_MEMORY_HOST", "0.0.0.0")
    port = int(os.getenv("SIGMA_MEMORY_PORT", "8090"))
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise RuntimeError("SIGMA_MEMORY_TOKEN is required for non-loopback binding")

    class Handler(BaseHTTPRequestHandler):
        server_version = "SigmaMemory/1"

        def _json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _auth(self) -> bool:
            return not token or self.headers.get("Authorization") == f"Bearer {token}"

        def _read(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON object required")
            return payload

        def do_GET(self) -> None:
            if urlparse(self.path).path != "/health":
                self._json(404, {"error": "not found"})
                return
            self._json(200, {"status": "ok", "backend": "graphiti-falkordb"})

        def do_POST(self) -> None:
            if not self._auth():
                self._json(401, {"error": "unauthorized"})
                return
            path = urlparse(self.path).path
            try:
                payload = self._read()
                if path == "/episodes":
                    self._json(201, app.add_episode(payload))
                elif path == "/search":
                    self._json(200, app.search(payload))
                else:
                    self._json(404, {"error": "not found"})
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:
                self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

        def log_message(self, format: str, *args: Any) -> None:
            if os.getenv("SIGMA_MEMORY_HTTP_LOG") == "1":
                super().log_message(format, *args)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> int:
    app = MemoryApp()
    server = build_server(app)
    print(f"Sigma memory service listening on {server.server_address}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
