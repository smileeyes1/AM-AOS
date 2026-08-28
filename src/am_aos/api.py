"""Dependency-light HTTP API boundary for AM-AOS.

This module is intentionally provider/framework agnostic. It implements the
security boundary that must exist before wiring an external agent/tool runtime.
It is not a substitute for TLS termination, enterprise identity, or a hardened
production WSGI/ASGI deployment.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


ROLES = {
    "viewer": frozenset({"read"}),
    "operator": frozenset({"read", "execute"}),
    "assurance": frozenset({"read", "verify"}),
    "admin": frozenset({"read", "execute", "verify", "admin"}),
}


class APIStore:
    """Transactional store for API idempotency and request audit records."""
    def __init__(self, path: str = "am_aos_api.db"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS idempotency (
            idem_key TEXT PRIMARY KEY,
            request_hash TEXT NOT NULL,
            response_json TEXT NOT NULL
        )""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS api_audit (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            role TEXT NOT NULL,
            action TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        self.db.commit()

    def get_idempotent(self, key: str, request_hash: str):
        row = self.db.execute(
            "SELECT request_hash,response_json FROM idempotency WHERE idem_key=?", (key,)
        ).fetchone()
        if not row:
            return None
        if not hmac.compare_digest(row[0], request_hash):
            raise ValueError("idempotency key was reused with a different request")
        return json.loads(row[1])

    def put_idempotent(self, key: str, request_hash: str, response: dict[str, Any]):
        self.db.execute(
            "INSERT INTO idempotency VALUES (?,?,?)",
            (key, request_hash, json.dumps(response, sort_keys=True, ensure_ascii=False)),
        )
        self.db.commit()

    def audit(self, request_id, actor, role, action, request_hash):
        self.db.execute(
            "INSERT INTO api_audit(request_id,actor,role,action,request_hash) VALUES (?,?,?,?,?)",
            (request_id, actor, role, action, request_hash),
        )
        self.db.commit()


class RBAC:
    @staticmethod
    def authorize(role: str, action: str) -> bool:
        return action in ROLES.get(role, frozenset())


class Handler(BaseHTTPRequestHandler):
    store = APIStore(os.getenv("AM_AOS_DB", "am_aos_api.db"))

    def _json(self, code: int, payload: dict[str, Any]):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"status": "ok", "service": "am-aos-api"})
        if self.path == "/ready":
            return self._json(200, {"status": "ready", "checks": {"database": "configured"}})
        return self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/v1/authorize":
            return self._json(404, {"error": "not_found"})
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            return self._json(413, {"error": "payload_too_large"})
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            actor = str(payload["actor"])
            role = str(payload["role"])
            action = str(payload["action"])
            request_id = str(payload.get("request_id", ""))
            idem = self.headers.get("Idempotency-Key")
            if not idem:
                return self._json(400, {"error": "idempotency_key_required"})
            request_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            cached = self.store.get_idempotent(idem, request_hash)
            if cached is not None:
                return self._json(200, {**cached, "replayed": True})
            allowed = RBAC.authorize(role, action)
            result = {"actor": actor, "role": role, "action": action, "allowed": allowed}
            self.store.audit(request_id, actor, role, action, request_hash)
            self.store.put_idempotent(idem, request_hash, result)
            return self._json(200, result)
        except ValueError as exc:
            return self._json(409, {"error": str(exc)})
        except (KeyError, json.JSONDecodeError, TypeError) as exc:
            return self._json(400, {"error": f"invalid_request: {type(exc).__name__}"})

    def log_message(self, fmt, *args):
        return


def serve(host="127.0.0.1", port=8080):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"AM-AOS API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
