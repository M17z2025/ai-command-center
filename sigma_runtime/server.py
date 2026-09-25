"""Minimal authenticated HTTP API for Sigma runtime."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from typing import Any
from urllib.parse import urlparse

from .config import MeshConfig
from .orchestrator import SigmaOrchestrator
from .store import MissionStore


MAX_BODY = 100_000


def build_server(
    host: str,
    port: int,
    orchestrator: SigmaOrchestrator,
    config: MeshConfig,
    store: MissionStore,
    token: str | None,
) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise RuntimeError("SIGMA_RUNTIME_TOKEN is required for non-loopback API binding")

    class Handler(BaseHTTPRequestHandler):
        server_version = "SigmaMesh/1"

        def _authorized(self) -> bool:
            if not token:
                return True
            return self.headers.get("Authorization") == f"Bearer {token}"

        def _json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _auth_or_401(self) -> bool:
            if self._authorized():
                return True
            self._json(401, {"error": "unauthorized"})
            return False

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/health":
                self._json(200, {"status": "ok", "mesh": config.public_summary()})
                return
            if not self._auth_or_401():
                return
            if path == "/mesh":
                self._json(200, config.public_summary())
                return
            if path == "/missions":
                self._json(200, {"missions": store.list_missions()})
                return
            if path == "/lessons":
                self._json(200, {"lessons": store.list_lessons()})
                return
            if path.startswith("/missions/"):
                mission = store.get_mission(path.split("/", 2)[2])
                if not mission:
                    self._json(404, {"error": "mission not found"})
                else:
                    self._json(200, mission)
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if not self._auth_or_401():
                return
            if path != "/missions":
                self._json(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                self._json(413, {"error": "invalid request size"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                result = orchestrator.run(
                    payload.get("prompt", ""),
                    evidence=payload.get("evidence") or [],
                    requested_by=payload.get("requested_by") or "owner",
                    max_cycles=payload.get("max_cycles", 2),
                )
                self._json(201, result)
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:
                self._json(500, {"error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:
            if os.getenv("SIGMA_RUNTIME_HTTP_LOG") == "1":
                super().log_message(format, *args)

    return ThreadingHTTPServer((host, port), Handler)
