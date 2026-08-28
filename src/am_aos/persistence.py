from __future__ import annotations
import json
import sqlite3
from typing import Any


class SQLiteStore:
    """Minimal durable store boundary; domain policy remains outside the DB."""
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS missions (
            mission_id TEXT PRIMARY KEY,
            goal TEXT NOT NULL,
            contract_json TEXT NOT NULL,
            contract_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            event_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            digest TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            sufficient INTEGER NOT NULL CHECK (sufficient IN (0,1))
        );
        """)
        self.db.commit()

    def save_mission(self, mission_id: str, goal: str, contract: dict[str, Any], contract_hash: str) -> None:
        self.db.execute(
            "INSERT INTO missions VALUES (?,?,?,?)",
            (mission_id, goal, json.dumps(contract, sort_keys=True, ensure_ascii=False), contract_hash),
        )
        self.db.commit()

    def mission_contract_hash(self, mission_id: str) -> str:
        row = self.db.execute("SELECT contract_hash FROM missions WHERE mission_id=?", (mission_id,)).fetchone()
        if not row:
            raise KeyError(mission_id)
        return row[0]

    def append_event(self, event_id: str, event_hash: str, payload: dict[str, Any]) -> None:
        self.db.execute("INSERT INTO events(event_id,event_hash,payload_json) VALUES (?,?,?)", (event_id, event_hash, json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)))
        self.db.commit()

    def count_events(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def close(self) -> None:
        self.db.close()
