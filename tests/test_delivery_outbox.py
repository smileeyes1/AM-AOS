import pytest
from am_aos.outbox import ReleaseDeliveryOutbox, DeliveryState


def test_delivery_requires_release_and_scope():
    box = ReleaseDeliveryOutbox()
    with pytest.raises(PermissionError):
        box.enqueue("d1", "m1", "t1", {"x": 1}, "PASS", False)
    with pytest.raises(PermissionError):
        box.enqueue("d2", "m1", "t1", {"x": 1}, "FAIL", True)


def test_delivery_blocks_if_artifact_changes():
    box = ReleaseDeliveryOutbox()
    d = box.enqueue("d1", "m1", "t1", {"x": 1}, "PASS", True)
    with pytest.raises(ValueError): box.send("d1", lambda _: None, {"x": 2})
    assert d.state is DeliveryState.BLOCKED


def test_delivery_is_idempotent_after_success():
    box = ReleaseDeliveryOutbox(); sent=[]
    box.enqueue("d1", "m1", "t1", {"x": 1}, "PASS", True)
    box.send("d1", sent.append, {"x": 1}); box.send("d1", sent.append, {"x": 1})
    assert len(sent) == 1
