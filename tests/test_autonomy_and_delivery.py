from am_aos.delivery import DeliveryGate
from am_aos.orchestrator import AutonomyController, MissionPolicy
from am_aos.runtime import AMAOSEngine, Decision


def test_autonomy_reaches_release_with_in_scope_verification():
    e = AMAOSEngine()
    m = e.create_mission("produce result", ["result is valid"], [], {"execute"}, "pilot")
    e.register_agent("a", {"execute"}, lambda task: {"ok": True})
    t = e.add_task(m, "produce", "execute", "independent-verifier")
    c = AutonomyController(e, MissionPolicy())
    run = c.run(m, [t], "a", lambda result, criteria: result == {"ok": True})
    assert run.released is True
    assert run.decisions[-1] == Decision.PASS


def test_delivery_blocks_failed_or_unscoped_release():
    d = DeliveryGate()
    try:
        d.deliver(mission_id="m", artifact={"x": 1}, decision=Decision.FAIL, scope="pilot", claim="x")
        assert False, "failed decision must never deliver"
    except PermissionError:
        pass
    try:
        d.deliver(mission_id="m", artifact={"x": 1}, decision=Decision.PASS, scope="", claim="x")
        assert False, "empty scope must never deliver"
    except PermissionError:
        pass


def test_delivery_receipt_binds_artifact_and_scope():
    d = DeliveryGate()
    r = d.deliver(
        mission_id="m",
        artifact={"x": 1},
        decision=Decision.PASS,
        scope="pilot",
        claim="x is 1",
    )
    assert r.mission_id == "m"
    assert r.scope == "pilot"
    assert len(r.artifact_digest) == 64
