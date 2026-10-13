"""Boundary tests do not rely on any ChatGPT custom or project instructions."""
import json
from pathlib import Path

import pytest

from am_aos.sovereign_control import (MissionContract, PolicyFailure,
    Principal, Request, SovereignControl)

PROFILE = Path(__file__).resolve().parents[1] / "control/sovereign-profile-v1.json"


def setup():
    return (SovereignControl.from_file(PROFILE),
            MissionContract("mission-1", "Produce a verified lesson PDF", frozenset({"read-course", "build-lesson"})),
            Principal("agent-1", frozenset({"read-course", "build-lesson"})))


def test_operates_without_chatgpt_custom_instructions(monkeypatch):
    monkeypatch.delenv("CHATGPT_CUSTOM_INSTRUCTIONS", raising=False)
    controller, mission, principal = setup()
    assert controller.authorize(mission, principal, Request("mission-1", "build", "build-lesson")).allowed


def test_default_deny_unknown_action():
    c, m, p = setup()
    assert not c.authorize(m, p, Request("mission-1", "hidden_action", "build-lesson")).allowed


def test_mission_boundary_deny_even_if_principal_has_grant():
    c, m, _ = setup()
    overprivileged = Principal("agent-1", frozenset({"delete-everything"}))
    assert not c.authorize(m, overprivileged, Request("mission-1", "build", "delete-everything")).allowed


def test_principal_missing_capability_deny():
    c, m, _ = setup()
    assert not c.authorize(m, Principal("agent-1", frozenset()), Request("mission-1", "build", "build-lesson")).allowed


def test_cross_mission_request_deny():
    c, m, p = setup()
    assert not c.authorize(m, p, Request("different-mission", "build", "build-lesson")).allowed


@pytest.mark.parametrize("operation", ["publish", "pay", "delete", "grant_access", "change_goal", "deploy_production"])
def test_high_impact_operations_are_denied_without_external_approval(operation):
    c, m, p = setup()
    assert not c.authorize(m, p, Request("mission-1", operation, "build-lesson")).allowed


def test_missing_and_tampered_policy_fail_closed(tmp_path):
    with pytest.raises(PolicyFailure):
        SovereignControl.from_file(tmp_path / "missing.json")
    obj = json.loads(PROFILE.read_text())
    obj["allowed_operations"].append("pay")
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(obj))
    with pytest.raises(PolicyFailure, match="integrity mismatch"):
        SovereignControl.from_file(altered)


def test_release_gate_requires_all_successful_evidence():
    c, _, _ = setup()
    assert not c.release(None).allowed
    base = {k: "PASS" for k in ("contract", "authority", "actual_output", "verification", "regression")}
    assert c.release(base).allowed
    base["regression"] = "NOT_TESTED"
    assert not c.release(base).allowed


def test_contract_is_immutable():
    c, mission, p = setup()
    with pytest.raises(Exception):
        mission.goal = "new goal"
