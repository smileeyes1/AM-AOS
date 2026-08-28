from am_aos.evidence import EvidenceLedger
from am_aos.gates import Gate, GateDecision, GateEngine
from am_aos.delivery import DeliveryController, DeliveryDecision
from am_aos.state import MissionState, StateStore


def test_gate_is_fail_closed():
    e = GateEngine((Gate("G1", ("tests", "security")),))
    assert e.evaluate("G1", {"tests": True}) is GateDecision.NOT_READY
    assert e.evaluate("G1", {"tests": True, "security": False}) is GateDecision.NO_GO
    assert e.evaluate("G1", {"tests": True, "security": True}) is GateDecision.PASS


def test_evidence_tamper_is_detected(tmp_path):
    p = tmp_path / "evidence.jsonl"
    l = EvidenceLedger(p)
    l.append("e1", "claim", "G1", "test", "PASS", "a.txt", "v1")
    assert l.verify()
    raw = p.read_text().replace('"result": "PASS"', '"result": "FAIL"')
    p.write_text(raw)
    assert not l.verify()


def test_delivery_holds_until_all_checks():
    c = DeliveryController()
    sent = []
    checks = {k: True for k in c.gate.required}
    checks["security_pass"] = False
    r = c.deliver(checks, "user://authorized", "artifact.tgz", lambda d, a: sent.append((d, a)))
    assert r.decision is DeliveryDecision.HOLD and sent == []
    checks["security_pass"] = True
    r = c.deliver(checks, "user://authorized", "artifact.tgz", lambda d, a: sent.append((d, a)))
    assert r.decision is DeliveryDecision.DELIVER and len(sent) == 1


def test_state_round_trip(tmp_path):
    s = StateStore(tmp_path / "state.json")
    state = MissionState("m1", "goal", ("immutable",), "ceiling", "G1", next_action="t1")
    s.save(state)
    assert s.load() == state
