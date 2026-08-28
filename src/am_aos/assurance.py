from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .evidence import EvidenceLedger


class GateState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NO_GO = "NO-GO"
    UNPROVEN = "UNPROVEN"


@dataclass(frozen=True)
class GateResult:
    state: GateState
    reason: str
    evidence_ids: tuple[str, ...] = ()


class VerificationGate:
    def evaluate(self, evidence: EvidenceLedger, evidence_ids: Iterable[str], expected: object) -> GateResult:
        ids = tuple(evidence_ids)
        if not evidence.sufficient(list(ids)):
            return GateResult(GateState.NO_GO, "evidence is missing or insufficient", ids)
        values = [evidence.get(i).value for i in ids]
        if expected in values:
            return GateResult(GateState.PASS, "acceptance condition established by sufficient evidence", ids)
        return GateResult(GateState.FAIL, "sufficient evidence exists but does not establish the expected outcome", ids)


class ClaimBoundary:
    """Prevents callers from converting a local test result into a global proof claim."""

    ALLOWED = {"IMPLEMENTED", "TESTED", "VERIFIED", "HARDENED", "PRODUCTION_READY", "PILOT_VERIFIED"}

    @classmethod
    def validate(cls, claim: str, scope: str) -> None:
        if claim == "GLOBALLY_PROVEN":
            raise ValueError("global proof is not an automatic runtime state")
        if claim not in cls.ALLOWED:
            raise ValueError(f"unknown assurance claim: {claim}")
        if not scope.strip():
            raise ValueError("assurance claims require an explicit scope")
