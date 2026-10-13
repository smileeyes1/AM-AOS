"""Test-only credential issuer models a separately trusted identity service."""
import base64
import hashlib
import hmac
import json
from pathlib import Path

import pytest

from am_aos.authenticated_adapter import (
    AuthenticatedExecutionAdapter, AuthenticationFailure, SignedIdentityVerifier,
    call_fingerprint,
)
from am_aos.execution_gateway import (
    ExecutionJournal, ToolCall, ToolRegistration, TrustedExecutionGateway,
)
from am_aos.sovereign_control import MissionContract, SovereignControl

PROFILE = Path(__file__).resolve().parents[1] / "control/sovereign-profile-v1.json"
TEST_SECRET = b"unit-test-only-not-a-real-deployment-key!!"
T = 100_000


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _issue(claims, secret=TEST_SECRET):
    payload = _b64(json.dumps(claims, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False).encode("utf-8"))
    content = "amaos1." + payload
    signature = hmac.new(secret, content.encode(), hashlib.sha256).digest()
    return content + "." + _b64(signature)


def fixture(tmp_path):
    count = []
    def handler(args):
        count.append(args)
        return "executed"
    gate = TrustedExecutionGateway(
        SovereignControl.from_file(PROFILE),
        ExecutionJournal.bootstrap(tmp_path / "journal.db"),
        (ToolRegistration("build-lesson", "sample:lesson", "execute", "build-lesson", "build", handler),),
    )
    verifier = SignedIdentityVerifier(TEST_SECRET, issuer="trusted-issuer", audience="am-aos-gateway", now=lambda: T)
    adapter = AuthenticatedExecutionAdapter(verifier, gate)
    mission = MissionContract("m1", "Prepare verified lesson", frozenset({"build-lesson"}))
    call = ToolCall("m1", "build-lesson", ("math",), "nonce-auth-1")
    return adapter, mission, call, count


def claims(adapter, mission, call):
    return {
        "v": 1, "iss": "trusted-issuer", "aud": "am-aos-gateway", "sub": "user-validated-by-issuer",
        "caps": ["build-lesson"], "mission": mission.mission_id,
        "goal_sha256": hashlib.sha256(mission.goal.encode("utf-8")).hexdigest(),
        "tool": call.tool_id, "call_sha256": call_fingerprint(call),
        "policy_sha256": adapter.gateway.policy.profile_sha256,
        "iat": T-2, "nbf": T-2, "exp": T+180,
    }


def test_authenticated_request_invokes_trusted_tool(tmp_path):
    a, m, c, count = fixture(tmp_path)
    assert a.invoke(m, _issue(claims(a, m, c)), c).status == "EXECUTED"
    assert len(count) == 1 and a.gateway.journal.verify_events()


def test_missing_token_denies_without_execution(tmp_path):
    a, m, c, count = fixture(tmp_path)
    assert a.invoke(m, "", c).status == "DENIED" and count == []


def test_fabricated_name_or_self_asserted_role_does_not_authenticate(tmp_path):
    a, m, c, count = fixture(tmp_path)
    for forged in ("admin", '{"sub":"admin","caps":["build-lesson"]}', "amaos1.x.y"):
        assert a.invoke(m, forged, c).status == "DENIED"
    assert count == []


def test_modified_signed_payload_denied(tmp_path):
    a, m, c, count = fixture(tmp_path)
    original = _issue(claims(a, m, c))
    tampered = original.replace("amaos1.", "amaos1.Z", 1)
    assert a.invoke(m, tampered, c).status == "DENIED"
    assert not count


def test_signature_with_wrong_key_denied(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c), secret=b"a"*32)
    assert a.invoke(m, token, c).status == "DENIED" and not count


@pytest.mark.parametrize("field,value", [
    ("iss", "evil"), ("aud", "elsewhere"), ("sub", ""), ("tool", "other"),
    ("mission", "m2"), ("goal_sha256", "0"*64), ("call_sha256", "0"*64),
    ("policy_sha256", "0"*64), ("caps", []), ("caps", ["build-lesson", "build-lesson"]),
    ("caps", ["publish"]), ("exp", T-1), ("nbf", T+50), ("iat", T+50),
    ("exp", T+500), ("v", True),
])
def test_malformed_or_out_of_scope_token_denied(tmp_path, field, value):
    a, m, c, count = fixture(tmp_path)
    p = claims(a, m, c)
    p[field] = value
    assert a.invoke(m, _issue(p), c).status != "EXECUTED"
    assert not count


def test_valid_bearer_bound_to_original_arguments(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c))
    wrong = ToolCall("m1", "build-lesson", ("different",), c.idempotency_key)
    assert a.invoke(m, token, wrong).status == "DENIED"
    assert count == []


def test_valid_bearer_bound_to_original_nonce(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c))
    wrong = ToolCall("m1", "build-lesson", c.arguments, "second-nonce")
    assert a.invoke(m, token, wrong).status == "DENIED"
    assert count == []


def test_valid_bearer_bound_to_original_goal(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c))
    modified = MissionContract("m1", "Changed goal", m.authority_ceiling)
    assert a.invoke(modified, token, c).status == "DENIED"
    assert count == []


def test_valid_bearer_cannot_expand_mission_authority(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c))
    restricted = MissionContract("m1", m.goal, frozenset({"other"}))
    assert a.invoke(restricted, token, c).status == "DENIED"
    assert count == []


def test_valid_token_replay_blocked_across_adapter_restart(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c))
    assert a.invoke(m, token, c).status == "EXECUTED"
    recovered = TrustedExecutionGateway(a.gateway.policy, ExecutionJournal(a.gateway.journal.path), tuple(a.gateway.registry.values()))
    second = AuthenticatedExecutionAdapter(a.verifier, recovered)
    assert second.invoke(m, token, c).status == "BLOCKED"
    assert len(count) == 1


def test_expiry_with_live_clock(tmp_path):
    a, m, c, count = fixture(tmp_path)
    token = _issue(claims(a, m, c))
    verifier = SignedIdentityVerifier(TEST_SECRET, issuer="trusted-issuer", audience="am-aos-gateway", now=lambda: T+181)
    assert AuthenticatedExecutionAdapter(verifier, a.gateway).invoke(m, token, c).status == "DENIED"
    assert count == []


def test_no_key_or_short_key_fails_closed():
    for key in (b"", b"short"):
        with pytest.raises(AuthenticationFailure):
            SignedIdentityVerifier(key, issuer="trusted-issuer", audience="am-aos-gateway")


def test_bearer_cannot_authorize_critical_delete_operation(tmp_path):
    a, m, c, count = fixture(tmp_path)
    critical_gateway = TrustedExecutionGateway(a.gateway.policy, a.gateway.journal, (
        ToolRegistration("build-lesson", "sample:lesson", "execute", "build-lesson", "delete", lambda _: "unsafe"),
    ))
    token = _issue(claims(a, m, c))
    auth = AuthenticatedExecutionAdapter(a.verifier, critical_gateway)
    assert auth.invoke(m, token, c).status == "DENIED"
    assert not count


def test_token_verifier_strict_duplicate_json_claims(tmp_path):
    a, m, c, count = fixture(tmp_path)
    p = claims(a, m, c)
    payload = json.dumps(p, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload = payload.replace('"sub":"user-validated-by-issuer",', '"sub":"evil","sub":"user-validated-by-issuer",')
    signed = "amaos1."+_b64(payload.encode())
    signed += "."+_b64(hmac.new(TEST_SECRET,signed.encode(),hashlib.sha256).digest())
    assert a.invoke(m, signed, c).status == "DENIED"
    assert not count
