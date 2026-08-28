from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Callable

class DeliveryDecision(str, Enum):
    DELIVER = "DELIVER"
    HOLD = "HOLD"

@dataclass(frozen=True)
class DeliveryReceipt:
    decision: DeliveryDecision
    destination: str
    artifact: str

@dataclass(frozen=True)
class DeliveryGate:
    required: tuple[str, ...] = (
        "artifact_exists", "integrity_valid", "tests_pass", "security_pass",
        "evidence_sufficient", "release_approved", "destination_authorized",
    )
    def decide(self, checks: dict[str, bool]) -> DeliveryDecision:
        if any(k not in checks for k in self.required):
            return DeliveryDecision.HOLD
        return DeliveryDecision.DELIVER if all(checks[k] for k in self.required) else DeliveryDecision.HOLD

class DeliveryController:
    def __init__(self, gate: DeliveryGate | None = None):
        self.gate = gate or DeliveryGate()

    def deliver(self, checks: dict[str, bool], destination: str, artifact: str,
                sender: Callable[[str, str], None]) -> DeliveryReceipt:
        if self.gate.decide(checks) is not DeliveryDecision.DELIVER:
            return DeliveryReceipt(DeliveryDecision.HOLD, destination, artifact)
        sender(destination, artifact)
        return DeliveryReceipt(DeliveryDecision.DELIVER, destination, artifact)
