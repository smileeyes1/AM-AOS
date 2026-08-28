from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json, time
from typing import Callable, Any

class DeliveryState(str, Enum): QUEUED="QUEUED"; SENT="SENT"; FAILED="FAILED"; BLOCKED="BLOCKED"

@dataclass
class Delivery:
    delivery_id: str
    mission_id: str
    tenant_id: str
    artifact_digest: str
    state: DeliveryState
    attempts: int = 0
    error: str | None = None
    sent_at: float | None = None

class ReleaseDeliveryOutbox:
    """Fail-closed delivery: only PASS/CONDITIONAL PASS can enqueue; send is idempotent."""
    def __init__(self): self.items: dict[str, Delivery] = {}
    @staticmethod
    def digest(artifact: Any) -> str:
        raw = json.dumps(artifact, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")).encode()
        return sha256(raw).hexdigest()
    def enqueue(self, delivery_id: str, mission_id: str, tenant_id: str, artifact: Any, decision: str, claim_scope_ok: bool) -> Delivery:
        if decision not in {"PASS", "CONDITIONAL PASS"} or not claim_scope_ok:
            raise PermissionError("DELIVERY_GATE_BLOCKED")
        digest = self.digest(artifact)
        existing = self.items.get(delivery_id)
        if existing and existing.artifact_digest != digest:
            raise ValueError("DELIVERY_ID_REUSE_WITH_DIFFERENT_ARTIFACT")
        if existing: return existing
        d = Delivery(delivery_id, mission_id, tenant_id, digest, DeliveryState.QUEUED)
        self.items[delivery_id] = d; return d
    def send(self, delivery_id: str, sender: Callable[[Any], None], artifact: Any) -> Delivery:
        d = self.items[delivery_id]
        if self.digest(artifact) != d.artifact_digest:
            d.state = DeliveryState.BLOCKED; d.error = "ARTIFACT_CHANGED"; raise ValueError("ARTIFACT_CHANGED")
        if d.state is DeliveryState.SENT: return d
        d.attempts += 1
        try:
            sender(artifact); d.state = DeliveryState.SENT; d.sent_at = time.time()
        except Exception as exc:
            d.state = DeliveryState.FAILED; d.error = type(exc).__name__
            raise
        return d
