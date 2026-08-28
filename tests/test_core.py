import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from am_aos import AMAOSEngine, Agent, Decision


def make():
    engine = AMAOSEngine()
    engine.register_agent(Agent("executor", frozenset({"EXECUTE"}), lambda task: True))
    engine.register_agent(Agent("reviewer", frozenset({"REVIEW"}), lambda task: True))
    mission = engine.create_mission(
        "demonstrate governed execution",
        ["task verified"],
        ["goal and constraints immutable"],
        ["EXECUTE", "REVIEW"],
    )
    return engine, mission


def test_authorized_execution_passes():
    e, m = make()
    t = e.add_task(m, "execute", "EXECUTE", "standard")
    assert e.execute(t, "executor") == Decision.PASS


def test_unauthorized_execution_is_no_go():
    e, m = make()
    t = e.add_task(m, "execute", "EXECUTE", "standard")
    assert e.execute(t, "reviewer") == Decision.NO_GO


def test_outside_authority_ceiling_is_rejected():
    e, m = make()
    try:
        e.add_task(m, "admin", "ADMIN", "standard")
        assert False, "Expected PermissionError"
    except PermissionError:
        pass


def test_missing_evidence_blocks_verification():
    e, m = make()
    t = e.add_task(m, "execute", "EXECUTE", "standard")
    task = e.tasks[t]
    decision, _ = e.verification.verify(task, e.evidence)
    assert decision == Decision.BLOCKED


def test_execution_failure_is_detected_and_recovery_can_pass():
    calls = {"n": 0}
    def flaky(task):
        calls["n"] += 1
        return False if calls["n"] == 1 else True
    e = AMAOSEngine()
    e.register_agent(Agent("executor", frozenset({"EXECUTE"}), flaky))
    m = e.create_mission("recover", ["pass"], ["fixed"], ["EXECUTE"])
    t = e.add_task(m, "flaky", "EXECUTE", "standard")
    assert e.execute(t, "executor") == Decision.FAIL
    assert e.recover(t, "executor") == Decision.PASS


def test_regression_gate_catches_degradation():
    e, m = make()
    t = e.add_task(m, "execute", "EXECUTE", "standard")
    assert e.execute(t, "executor") == Decision.PASS
    e.capture_regression_baseline()
    e.tasks[t].status = Decision.FAIL
    ok, _ = e.regression_check()
    assert not ok
