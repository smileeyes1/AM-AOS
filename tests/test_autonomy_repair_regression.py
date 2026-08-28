from am_aos.orchestrator import AutonomyController
from am_aos.runtime import AMAOSEngine, Decision


def test_repair_is_followed_by_regression():
    e = AMAOSEngine()
    m = e.create_mission("repairable", ["ok"], [], {"execute"}, "pilot")
    e.register_agent("a", {"execute"}, lambda task: {"ok": True})
    t = e.add_task(m, "work", "execute", "verifier")
    c = AutonomyController(e)
    seen = {"break": 0}

    def break_once(result):
        seen["break"] += 1
        return seen["break"] == 1

    run = c.run(
        m,
        [t],
        "a",
        lambda result, criteria: result == {"ok": True},
        break_test=break_once,
        repair=lambda result: result,
    )
    assert run.released is True
    assert run.decisions[-1] == Decision.PASS
    assert any("REGRESSION_PASSED" == event.event for event in e.audit.events)
