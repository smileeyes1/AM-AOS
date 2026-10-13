"""Provider-independent decision boundary: no ChatGPT instructions are trusted.

This module does NOT authenticate callers, isolate code, deliver artifacts or
establish production readiness. These must be provided by trusted adapters.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


# Reviewed hash pin: changing the profile requires changing this constant and
# passing the versioned review process. A checksum is NOT a digital signature.
TRUSTED_PROFILE_SHA256 = "bef7a930d378af02f1e7982aae557cc0a648549cc8bf19278e97f0f634628c25"
_ALLOWED_KEYS = frozenset({"schema_version", "profile_id", "purpose", "invariants", "allowed_operations", "approval_required_operations", "required_release_evidence"})
_REQUIRED_INVARIANTS = frozenset({
    "goal_is_owned_by_user", "mission_ceiling_cannot_expand_at_runtime",
    "no_execution_without_explicit_authorization", "critical_actions_require_external_approval",
    "no_release_without_evidence", "proven_baseline_must_be_preserved",
    "missing_policy_or_evidence_means_no_go",
})


class PolicyFailure(ValueError):
    """Missing, tampered, unrecognized or weakened sovereign profile."""


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    policy_sha256: str


@dataclass(frozen=True)
class MissionContract:
    mission_id: str
    goal: str
    authority_ceiling: frozenset[str]

    def __post_init__(self) -> None:
        if not self.mission_id.strip() or not self.goal.strip():
            raise ValueError("mission ID and goal are required")


@dataclass(frozen=True)
class Principal:
    principal_id: str
    capabilities: frozenset[str]


@dataclass(frozen=True)
class Request:
    mission_id: str
    operation: str
    required_capability: str


class SovereignControl:
    """Explicit, immutable mission gates independent of conversational memory.

    Only an authenticated external adapter may establish a Principal's identity
    and grants. No user-supplied text is accepted as an approval receipt.
    """

    def __init__(self, raw_profile: bytes, *, expected_sha256: str = TRUSTED_PROFILE_SHA256):
        digest = hashlib.sha256(raw_profile).hexdigest()
        if digest != expected_sha256:
            raise PolicyFailure("profile integrity mismatch")
        try:
            profile = json.loads(raw_profile)
        except (UnicodeError, ValueError) as exc:
            raise PolicyFailure("invalid profile") from exc
        if not isinstance(profile, dict) or frozenset(profile) != _ALLOWED_KEYS:
            raise PolicyFailure("unknown or missing profile keys")
        if profile["schema_version"] != "1.0":
            raise PolicyFailure("unsupported profile schema")
        for field in ("invariants", "allowed_operations", "approval_required_operations", "required_release_evidence"):
            if not isinstance(profile[field], list) or not profile[field] or not all(isinstance(s, str) and s for s in profile[field]):
                raise PolicyFailure(f"invalid field {field}")
            if len(profile[field]) != len(set(profile[field])):
                raise PolicyFailure(f"duplicate values in {field}")
        if not _REQUIRED_INVARIANTS.issubset(profile["invariants"]):
            raise PolicyFailure("missing critical invariants")
        if set(profile["allowed_operations"]) & set(profile["approval_required_operations"]):
            raise PolicyFailure("critical actions cannot be ordinary operations")
        for key in ("profile_id", "purpose"):
            if not isinstance(profile[key], str) or not profile[key].strip():
                raise PolicyFailure(f"invalid field {key}")
        self._digest = digest
        self._allowed = frozenset(profile["allowed_operations"])
        self._critical = frozenset(profile["approval_required_operations"])
        self._required_evidence = frozenset(profile["required_release_evidence"])

    @classmethod
    def from_file(cls, path: str | Path) -> "SovereignControl":
        try:
            return cls(Path(path).read_bytes())
        except OSError as exc:
            raise PolicyFailure("sovereign policy unavailable; fail closed") from exc

    @property
    def profile_sha256(self) -> str:
        return self._digest

    def authorize(self, mission: MissionContract, principal: Principal, request: Request) -> Decision:
        """Deny anything beyond intersection of mission and principal grants.

        CRITICAL operations always deny here until a separately authenticated,
        explicit approval service is implemented and independently tested.
        """
        why = ""
        if request.mission_id != mission.mission_id:
            why = "mission mismatch"
        elif not principal.principal_id.strip() or not request.required_capability.strip():
            why = "unidentified principal or missing capability"
        elif request.operation in self._critical:
            why = "high-impact operation requires trusted external approval"
        elif request.operation not in self._allowed:
            why = "operation not allowed"
        elif request.required_capability not in mission.authority_ceiling:
            why = "outside immutable mission authority ceiling"
        elif request.required_capability not in principal.capabilities:
            why = "principal lacks required capability"
        else:
            return Decision(True, "within mission and principal authority", self._digest)
        return Decision(False, why, self._digest)

    def release(self, evidence: Mapping[str, str] | None) -> Decision:
        """Local completeness gate; does not prove evidence provenance or authenticity."""
        if evidence is None or not self._required_evidence.issubset(evidence):
            return Decision(False, "missing required evidence", self._digest)
        if any(evidence[key] != "PASS" for key in self._required_evidence):
            return Decision(False, "release gate evidence not PASS", self._digest)
        return Decision(True, "claimed gates present; external proof still required", self._digest)
