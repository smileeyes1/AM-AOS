from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class PolicyViolation(PermissionError):
    """Raised when an action violates an immutable policy boundary."""


@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    reason: str
    policy_version: str = "1.0"


class AuthorityPolicy:
    """Deterministic allow-list policy; no runtime mutation API is exposed."""

    def __init__(self, allowed_authorities: Iterable[str]):
        self._allowed = frozenset(allowed_authorities)

    @property
    def allowed(self):
        return self._allowed

    def decide(self, required: str, granted: Iterable[str]) -> AuthorityDecision:
        granted_set = frozenset(granted)
        if required not in self._allowed:
            return AuthorityDecision(False, "required authority is outside mission ceiling")
        if required not in granted_set:
            return AuthorityDecision(False, "agent does not possess required authority")
        return AuthorityDecision(True, "authority granted")

    def assert_allowed(self, required: str, granted: Iterable[str]) -> None:
        decision = self.decide(required, granted)
        if not decision.allowed:
            raise PolicyViolation(decision.reason)

    def __setattr__(self, name, value):
        # Prevent replacing the policy after construction.
        if name == "_allowed" and hasattr(self, "_allowed"):
            raise AttributeError("authority policy is immutable")
        super().__setattr__(name, value)
