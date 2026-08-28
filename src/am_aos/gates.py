from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class GateDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NO_GO = "NO-GO"
    BLOCKED = "BLOCKED"
    NOT_READY = "NOT-READY"

@dataclass(frozen=True)
class Gate:
    gate_id: str
    required_checks: tuple[str, ...]

class GateEngine:
    """Fail-closed gate evaluator. Unknown/missing checks never become PASS."""
    def __init__(self, gates: tuple[Gate, ...]):
        self.gates = {g.gate_id: g for g in gates}

    def evaluate(self, gate_id: str, checks: dict[str, bool], blockers: tuple[str, ...] = ()) -> GateDecision:
        gate = self.gates[gate_id]
        if blockers:
            return GateDecision.BLOCKED
        if any(name not in checks for name in gate.required_checks):
            return GateDecision.NOT_READY
        if not all(checks[name] for name in gate.required_checks):
            return GateDecision.NO_GO
        return GateDecision.PASS
