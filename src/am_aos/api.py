from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .runtime import AMAOSEngine


class ControlPlaneHandler(BaseHTTPRequestHandler):
    engine: AMAOSEngine | None = None

    def _send(self, status: int, body: dict[str, Any]) -> None:
        raw = json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._send(200, {"status": "ok"})
            return
        if self.path == "/readyz":
            self._send(200, {"status": "ready", "engine": self.engine is not None})
            return
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/missions":
            self._send(404, {"error": "not_found"})
            return
        if self.engine is None:
            self._send(503, {"error": "engine_unavailable"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
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
    ControlPlaneHandler.engine = engine
    ThreadingHTTPServer((host, port), ControlPlaneHandler).serve_forever()
