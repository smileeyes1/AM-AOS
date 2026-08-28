from am_aos.gates import Gate, GateDecision, GateEngine


def test_gate_is_fail_closed_on_missing_check():
    e = GateEngine((Gate("G1", ("a", "b")),))
    assert e.evaluate("G1", {"a": True}) is GateDecision.NOT_READY


def test_gate_rejects_failed_check():
    e = GateEngine((Gate("G1", ("a",)),))
    assert e.evaluate("G1", {"a": False}) is GateDecision.NO_GO


def test_gate_blocks_on_blocker():
    e = GateEngine((Gate("G1", ("a",)),))
    assert e.evaluate("G1", {"a": True}, ("external-secret",)) is GateDecision.BLOCKED


def test_gate_passes_only_when_all_checks_pass():
    e = GateEngine((Gate("G1", ("a", "b")),))
    assert e.evaluate("G1", {"a": True, "b": True}) is GateDecision.PASS
