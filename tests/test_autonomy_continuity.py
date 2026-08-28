from am_aos.autonomy import AutonomousController, AutonomyLimits, Phase
from am_aos.runtime import Decision


def test_failed_verification_replans_then_releases():
    state = {"n": 0}
    replans = []
    delivered = []

    def execute():
        state["n"] += 1
        return state["n"]

    def verify(value):
        return Decision.PASS if value >= 2 else Decision.FAIL

    run = AutonomousController(AutonomyLimits(max_cycles=3)).run(
        "m-replan",
        plan=lambda: None,
        execute=execute,
        verify=verify,
        break_test=lambda _: False,
        repair=lambda x: x,
        regression=lambda _: True,
        audit=lambda _: True,
        claim_scope=lambda _: True,
        release=lambda x: delivered.append(x),
        replan=lambda value, decision: replans.append((value, decision)),
    )

    assert run.phase is Phase.RELEASE
    assert run.replans == 1
    assert replans and replans[0][1] is Decision.FAIL
    assert delivered == [2]


def test_stagnation_is_detected_without_replan():
    run = AutonomousController(AutonomyLimits(max_cycles=5, max_stagnant_cycles=1)).run(
        "m-stagnant",
        plan=lambda: None,
        execute=lambda: "same",
        verify=lambda _: Decision.PASS,
        break_test=lambda _: False,
        repair=lambda x: x,
        regression=lambda _: True,
        audit=lambda _: True,
        claim_scope=lambda _: True,
        release=lambda _: None,
        progress_key=lambda x: x,
    )

    assert run.phase is Phase.STOP
    assert run.stop_reason == "STAGNATION"
    assert run.decision is Decision.BLOCKED
