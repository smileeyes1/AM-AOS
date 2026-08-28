from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from time import time
from uuid import uuid4

from .runtime import Decision, canonical


@dataclass(frozen=True)
class DeliveryReceipt:
    delivery_id: str
    mission_id: str
    artifact_digest: str
    decision: str
    scope: str
    delivered_at: float


class DeliveryGate:
    """Only releases an artifact after an explicit in-scope PASS/CONDITIONAL PASS."""

    def __init__(self) -> None:
        self.receipts: dict[str, DeliveryReceipt] = {}

    def deliver(
        self,
        *,
        mission_id: str,
        artifact: object,
        decision: Decision,
        scope: str,
        claim: str,
        externally_approved: bool = False,
    ) -> DeliveryReceipt:
        if not scope.strip():
            raise PermissionError("delivery requires a non-empty claim scope")
        if not claim.strip():
            raise PermissionError("delivery requires an explicit claim")
        if decision not in {Decision.PASS, Decision.CONDITIONAL_PASS}:
            raise PermissionError(f"release denied for decision={decision.value}")
        # External approval is required only when the mission contract says so;
        # this primitive never manufactures approval.
        if externally_approved is False and decision == Decision.CONDITIONAL_PASS:
            raise PermissionError("conditional release requires explicit approval")
        payload = canonical(artifact)
        receipt = DeliveryReceipt(
            delivery_id="delivery-" + uuid4().hex,
            mission_id=mission_id,
            artifact_digest=sha256(payload).hexdigest(),
            decision=decision.value,
            scope=scope,
            delivered_at=time(),
        )
        self.receipts[receipt.delivery_id] = receipt
        return receipt
