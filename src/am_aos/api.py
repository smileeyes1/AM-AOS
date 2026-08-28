from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .runtime import AMAOSEngine


class ControlPlaneHandler(BaseHTTPRequestHandler):
    engine: AMAOSEngine | None = None
    api_token: str | None = None

    def _send(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self) -> bool:
        expected = self.api_token
        supplied = self.headers.get("Authorization", "")
        if expected is None:
            return False
        if not supplied.startswith("Bearer "):
            return False
        return hmac.compare_digest(supplied[7:], expected)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._send(200, {"status": "ok"})
            return
        if self.path == "/readyz":
            self._send(200, {"status": "ready", "engine": self.engine is not None, "auth_configured": self.api_token is not None})
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/missions":
            self._send(404, {"error": "not_found"})
            return
        if not self._authorized():
            self._send(401, {"error": "unauthorized"})
            return
        if self.engine is None:
            self._send(503, {"error": "engine_unavailable"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_048_576:
                self._send(413, {"error": "payload_too_large"})
                return
            body = json.loads(self.rfile.read(length) or b"{}")
            mission_id = self.engine.create_mission(
                body["goal"],
                body["acceptance_criteria"],
                body.get("constraints", []),
                set(body["authorities"]),
                body["scope"],
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send(400, {"error": "invalid_mission", "detail": str(exc)})
            return
        self._send(201, {"mission_id": mission_id})

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(engine: AMAOSEngine, host: str = "127.0.0.1", port: int = 8080) -> None:
    token = os.environ.get("AM_AOS_API_TOKEN")
    if not token:
        raise RuntimeError("AM_AOS_API_TOKEN must be configured before starting the API")
    ControlPlaneHandler.engine = engine
    ControlPlaneHandler.api_token = token
    ThreadingHTTPServer((host, port), ControlPlaneHandler).serve_forever()
