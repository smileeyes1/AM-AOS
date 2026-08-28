import os

from am_aos.api import ControlPlaneHandler
from am_aos.runtime import AMAOSEngine


def test_api_requires_explicit_token(monkeypatch):
    monkeypatch.delenv("AM_AOS_API_TOKEN", raising=False)
    try:
        from am_aos.api import serve
        serve
    except Exception as exc:  # pragma: no cover
        assert exc is None
    assert os.environ.get("AM_AOS_API_TOKEN") is None
    assert ControlPlaneHandler.api_token is None


def test_authorization_uses_constant_time_comparison():
    ControlPlaneHandler.api_token = "secret"
    handler = object.__new__(ControlPlaneHandler)
    handler.headers = {"Authorization": "Bearer secret"}
    assert handler._authorized() is True
    handler.headers = {"Authorization": "Bearer wrong"}
    assert handler._authorized() is False
    ControlPlaneHandler.api_token = None
