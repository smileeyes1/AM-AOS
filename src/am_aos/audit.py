from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode()


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event: str
    subject: str
    data: dict[str, Any]
    timestamp: str
    previous_hash: str
    event_hash: str


class TamperEvidentAuditLog:
    """Append-only hash-chain ledger for integrity detection.

    This detects modification/reordering when the chain is later verified; it is
    not a substitute for WORM storage, signatures, key management, or an HSM.
    """

    def __init__(self):
        self._events: list[AuditEvent] = []

    def append(self, event: str, subject: str, **data: Any) -> AuditEvent:
        timestamp = datetime.now(timezone.utc).isoformat()
        previous = self._events[-1].event_hash if self._events else "GENESIS"
        body = {
            "event_id": f"evt-{uuid4().hex[:16]}",
            "event": event,
            "subject": subject,
            "data": data,
            "timestamp": timestamp,
            "previous_hash": previous,
        }
        digest = sha256(_canonical(body)).hexdigest()
        record = AuditEvent(**body, event_hash=digest)
        self._events.append(record)
        return record

    def verify_chain(self) -> tuple[bool, str]:
        previous = "GENESIS"
        for event in self._events:
            body = asdict(event)
            body.pop("event_hash")
            if body["previous_hash"] != previous:
                return False, f"broken previous-hash link at {event.event_id}"
            expected = sha256(_canonical(body)).hexdigest()
            if expected != event.event_hash:
                return False, f"event hash mismatch at {event.event_id}"
            previous = event.event_hash
        return True, "audit chain verified"

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)
