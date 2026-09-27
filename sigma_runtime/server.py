"""Minimal authenticated HTTP API for Sigma runtime and portfolio runner."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from typing import Any
from urllib.parse import parse_qs, urlparse

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
    *,
    portfolio_runner: Any | None = None,
) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"} and not token:
        raise RuntimeError("SIGMA_RUNTIME_TOKEN is required for non-loopback API binding")

    class Handler(BaseHTTPRequestHandler):
        server_version = "SigmaMesh/2"

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

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON object required")
            return payload

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/health":
                runner_summary = {
                    "configured": portfolio_runner is not None,
                    "write_enabled": False,
                    "worker_configured": False,
                }
                if portfolio_runner is not None:
                    runner_summary["write_enabled"] = bool(
                        getattr(portfolio_runner.github, "allow_write", False)
                    )
                    runner_summary["worker_configured"] = (
                        getattr(portfolio_runner, "worker", None) is not None
                    )
                self._json(
                    200,
                    {
                        "status": "ok",
                        "mesh": config.public_summary(),
                        "runner": runner_summary,
                    },
                )
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
            if path == "/runner/cycles":
                if portfolio_runner is None:
                    self._json(503, {"error": "portfolio runner not configured"})
                else:
                    query = parse_qs(parsed.query)
                    limit = int((query.get("limit") or ["50"])[0])
                    self._json(200, {"cycles": portfolio_runner.store.list(limit)})
                return
            if path.startswith("/runner/cycles/"):
                if portfolio_runner is None:
                    self._json(503, {"error": "portfolio runner not configured"})
                    return
                cycle = portfolio_runner.store.get(path.split("/", 3)[3])
                if not cycle:
                    self._json(404, {"error": "runner cycle not found"})
                else:
                    self._json(200, cycle)
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
            try:
                payload = self._read_json()
                if path == "/missions":
                    result = orchestrator.run(
                        payload.get("prompt", ""),
                        evidence=payload.get("evidence") or [],
                        requested_by=payload.get("requested_by") or "owner",
                        max_cycles=payload.get("max_cycles", 2),
                    )
                    self._json(201, result)
                    return
                if path == "/runner/cycle":
                    if portfolio_runner is None:
                        self._json(503, {"error": "portfolio runner not configured"})
                        return
                    result = portfolio_runner.cycle(
                        trigger=payload.get("trigger") or "api",
                        execute=bool(payload.get("execute", False)),
                    )
                    status = 409 if result.get("state") == "BLOCKED" else 201
                    self._json(status, result)
                    return
                self._json(404, {"error": "not found"})
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:
                self._json(500, {"error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:
            if os.getenv("SIGMA_RUNTIME_HTTP_LOG") == "1":
                super().log_message(format, *args)

    return ThreadingHTTPServer((host, port), Handler)
