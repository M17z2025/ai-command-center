"""Private runtime persistence for Sigma missions and evaluated lessons."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import uuid


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MissionStore:
    def __init__(self, path: str | Path = "runtime-data/sigma-runtime.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS missions (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  requested_by TEXT NOT NULL,
                  prompt TEXT NOT NULL,
                  status TEXT NOT NULL,
                  plan_json TEXT,
                  final_output TEXT,
                  error TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  mission_id TEXT NOT NULL,
                  at TEXT NOT NULL,
                  stage TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  FOREIGN KEY(mission_id) REFERENCES missions(id)
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                  mission_id TEXT NOT NULL,
                  name TEXT NOT NULL,
                  content TEXT NOT NULL,
                  PRIMARY KEY(mission_id, name),
                  FOREIGN KEY(mission_id) REFERENCES missions(id)
                );
                CREATE TABLE IF NOT EXISTS lessons (
                  id TEXT PRIMARY KEY,
                  mission_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  status TEXT NOT NULL,
                  lesson TEXT NOT NULL,
                  metadata_json TEXT NOT NULL,
                  FOREIGN KEY(mission_id) REFERENCES missions(id)
                );
                """
            )

    def create_mission(
        self, mission_id: str, prompt: str, requested_by: str, plan: dict[str, Any]
    ) -> None:
        now = utcnow()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO missions
                (id, created_at, updated_at, requested_by, prompt, status, plan_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (mission_id, now, now, requested_by, prompt, "RUNNING", json.dumps(plan)),
            )

    def event(self, mission_id: str, stage: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (mission_id, at, stage, payload_json) VALUES (?, ?, ?, ?)",
                (mission_id, utcnow(), stage, json.dumps(payload)),
            )

    def artifact(self, mission_id: str, name: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO artifacts (mission_id, name, content) VALUES (?, ?, ?)
                ON CONFLICT(mission_id, name) DO UPDATE SET content=excluded.content""",
                (mission_id, name, content),
            )

    def finish(
        self,
        mission_id: str,
        status: str,
        final_output: str | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE missions
                SET updated_at=?, status=?, final_output=?, error=? WHERE id=?""",
                (utcnow(), status, final_output, error, mission_id),
            )

    def add_lesson(
        self, mission_id: str, lesson: str, metadata: dict[str, Any] | None = None
    ) -> str:
        lesson_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO lessons
                (id, mission_id, created_at, status, lesson, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    lesson_id,
                    mission_id,
                    utcnow(),
                    "CANDIDATE",
                    lesson,
                    json.dumps(metadata or {}),
                ),
            )
        return lesson_id

    def get_mission(self, mission_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM missions WHERE id=?", (mission_id,)).fetchone()
            if not row:
                return None
            mission = dict(row)
            mission["plan"] = json.loads(mission.pop("plan_json") or "{}")
            events = conn.execute(
                "SELECT at, stage, payload_json FROM events WHERE mission_id=? ORDER BY id",
                (mission_id,),
            ).fetchall()
            mission["events"] = [
                {"at": item["at"], "stage": item["stage"], "payload": json.loads(item["payload_json"])}
                for item in events
            ]
            artifacts = conn.execute(
                "SELECT name, content FROM artifacts WHERE mission_id=? ORDER BY name",
                (mission_id,),
            ).fetchall()
            mission["artifacts"] = {item["name"]: item["content"] for item in artifacts}
            return mission

    def list_missions(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, created_at, updated_at, requested_by, status
                FROM missions ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_lessons(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, mission_id, created_at, status, lesson, metadata_json
                FROM lessons ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
                result.append(item)
            return result
