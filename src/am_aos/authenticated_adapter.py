"""Authenticated bearer-token adapter for AM-AOS registered-tool gateway.

Tokens MUST be issued by an independently authenticated, trusted service.
HMAC only proves possession of a shared secret; it is not an identity provider.
This module does not create identities, perform TLS, sandbox workers, or close
legacy Python callers that invoke raw handlers outside this adapter.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
import time
from typing import Callable, Mapping

from .execution_gateway import ToolCall, ToolOutcome, TrustedExecutionGateway
from .sovereign_control import MissionContract, Principal


class AuthenticationFailure(ValueError):
    """Fail-closed bearer-token verification failure."""


def _compact(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(encoded: str) -> bytes:
    if not isinstance(encoded, str) or not encoded or len(encoded) > 6000:
        raise AuthenticationFailure("malformed token component")
    try:
        raw = encoded.encode("ascii")
        decoded = base64.b64decode(raw + b"=" * ((-len(raw)) % 4),
                                   altchars=b"-_", validate=True)
        if _b64_encode(decoded) != encoded:
            raise AuthenticationFailure("noncanonical token encoding")
        return decoded
    except (ValueError, UnicodeError) as exc:
        raise AuthenticationFailure("invalid token encoding") from exc


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AuthenticationFailure("duplicate claim")
        result[key] = value
    return result


_ALLOWED_CLAIMS = frozenset({
    "v", "iss", "aud", "sub", "caps", "mission", "goal_sha256",
    "tool", "call_sha256", "policy_sha256", "iat", "nbf", "exp",
})


def call_fingerprint(call: ToolCall) -> str:
    """Binds one token to the complete requested action and replay token."""
    return sha256(_compact({
        "mission_id": call.mission_id,
        "tool_id": call.tool_id,
        "arguments": call.arguments,
        "idempotency_key": call.idempotency_key,
    })).hexdigest()


@dataclass(frozen=True)
class VerifiedIdentity:
    subject: str
    capabilities: frozenset[str]


class SignedIdentityVerifier:
    """Checks a strict time-limited MAC envelope using a provisioned secret.

    The verifier has no signer method. A separate trusted identity issuer must
    authenticate the actor, restrict permissions and sign the envelope.
    Shared secrets must come from private deployment configuration, not Git.
    """

    def __init__(self, secret: bytes, *, issuer: str, audience: str,
                 now: Callable[[], float] | None = None,
                 max_ttl_seconds: int = 300, allowed_skew_seconds: int = 10):
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise AuthenticationFailure("missing or too-short trusted secret")
        if not issuer.strip() or not audience.strip():
            raise AuthenticationFailure("issuer and audience are required")
        if not 1 <= max_ttl_seconds <= 3600 or not 0 <= allowed_skew_seconds <= 60:
            raise AuthenticationFailure("invalid verifier limits")
        self._secret = secret
        self._issuer = issuer
        self._audience = audience
        self._now = now or time.time
        self._max_ttl = max_ttl_seconds
        self._skew = allowed_skew_seconds

    def verify(self, bearer: str, mission: MissionContract, call: ToolCall,
               policy_sha256: str) -> VerifiedIdentity:
        if not isinstance(bearer, str) or len(bearer) > 8192:
            raise AuthenticationFailure("missing or oversized token")
        parts = bearer.split(".")
        if len(parts) != 3 or parts[0] != "amaos1":
            raise AuthenticationFailure("unsupported token envelope")
        payload_raw = _b64_decode(parts[1])
        supplied_mac = _b64_decode(parts[2])
        if len(supplied_mac) != 32:
            raise AuthenticationFailure("invalid token MAC")
        expected_mac = hmac.new(self._secret, b"amaos1." + parts[1].encode("ascii"), sha256).digest()
        if not hmac.compare_digest(supplied_mac, expected_mac):
            raise AuthenticationFailure("token authentication failed")
        try:
            claims = json.loads(payload_raw, object_pairs_hook=_reject_duplicate_pairs)
        except (ValueError, UnicodeError, TypeError) as exc:
            raise AuthenticationFailure("invalid token claims") from exc
        if not isinstance(claims, dict) or frozenset(claims) != _ALLOWED_CLAIMS:
            raise AuthenticationFailure("unknown or missing claims")
        if _compact(claims) != payload_raw:
            raise AuthenticationFailure("noncanonical token claims")
        if type(claims["v"]) is not int or claims["v"] != 1:
            raise AuthenticationFailure("unsupported claims version")
        for key in ("iss", "aud", "sub", "mission", "goal_sha256", "tool", "call_sha256", "policy_sha256"):
            if not isinstance(claims[key], str) or not claims[key].strip() or len(claims[key]) > 256:
                raise AuthenticationFailure("invalid text claim")
        if claims["iss"] != self._issuer or claims["aud"] != self._audience:
            raise AuthenticationFailure("token issuer or audience mismatch")
        for name in ("iat", "nbf", "exp"):
            if type(claims[name]) is not int:
                raise AuthenticationFailure("invalid token time claim")
        now = int(self._now())
        if (claims["exp"] <= now or claims["nbf"] > now + self._skew
                or claims["iat"] > now + self._skew
                or claims["exp"] <= claims["nbf"]
                or claims["exp"] <= claims["iat"]
                or claims["exp"] - claims["iat"] > self._max_ttl
                or claims["nbf"] < claims["iat"] - self._skew):
            raise AuthenticationFailure("token expired, premature or overlong")
        caps = claims["caps"]
        if (not isinstance(caps, list) or not (1 <= len(caps) <= 32)
                or not all(isinstance(x, str) and 0 < len(x) <= 128 for x in caps)
                or len(caps) != len(set(caps))):
            raise AuthenticationFailure("invalid capability claims")
        if (claims["mission"] != mission.mission_id
                or claims["goal_sha256"] != sha256(mission.goal.encode("utf-8")).hexdigest()
                or claims["tool"] != call.tool_id
                or claims["call_sha256"] != call_fingerprint(call)
                or claims["policy_sha256"] != policy_sha256):
            raise AuthenticationFailure("token scope mismatch")
        return VerifiedIdentity(claims["sub"], frozenset(caps))


class AuthenticatedExecutionAdapter:
    """Public trust entrypoint; never accepts self-asserted Principal objects."""

    def __init__(self, verifier: SignedIdentityVerifier, gateway: TrustedExecutionGateway):
        self.verifier = verifier
        self.gateway = gateway

    def invoke(self, mission: MissionContract, bearer: str, call: ToolCall) -> ToolOutcome:
        try:
            identity = self.verifier.verify(
                bearer, mission, call, self.gateway.policy.profile_sha256)
        except (AuthenticationFailure, TypeError, AttributeError, ValueError):
            self.gateway.journal.record_denial("untrusted or out-of-scope token")
            return ToolOutcome("DENIED", "unauthenticated or out-of-scope request")
        return self.gateway.invoke(mission, Principal(identity.subject, identity.capabilities), call)
