from am_aos.delivery import DeliveryDecision, DeliveryGate


def test_delivery_holds_when_any_required_check_is_missing():
    gate = DeliveryGate()
    assert gate.decide({"artifact_exists": True}) is DeliveryDecision.HOLD


def test_delivery_holds_on_failed_security_or_release():
    gate = DeliveryGate()
    checks = {name: True for name in gate.required}
    checks["security_pass"] = False
    assert gate.decide(checks) is DeliveryDecision.HOLD


def test_delivery_only_occurs_when_every_check_passes():
    gate = DeliveryGate()
    checks = {name: True for name in gate.required}
    assert gate.decide(checks) is DeliveryDecision.DELIVER
