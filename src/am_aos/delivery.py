from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class DeliveryDecision(str, Enum):
    DELIVER = "DELIVER"
    HOLD = "HOLD"

@dataclass(frozen=True)
class DeliveryGate:
    """Fail-closed final delivery policy; generation never implies delivery."""
    required: tuple[str, ...] = (
        "artifact_exists", "integrity_valid", "tests_pass", "security_pass",
        "evidence_sufficient", "release_approved", "destination_authorized",
    )

    def decide(self, checks: dict[str, bool]) -> DeliveryDecision:
        if any(name not in checks for name in self.required):
            return DeliveryDecision.HOLD
        return DeliveryDecision.DELIVER if all(checks[name] for name in self.required) else DeliveryDecision.HOLD
