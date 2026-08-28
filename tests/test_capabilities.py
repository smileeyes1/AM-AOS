from am_aos.capabilities import AgentIdentity, Capability, CapabilityGuard


def test_capability_allows_declared_action():
    guard = CapabilityGuard([Capability("read-doc", "doc:1", frozenset({"read"}))])
    agent = AgentIdentity("a1", frozenset({"read-doc"}))
    assert guard.authorize(agent, "read-doc", "doc:1", "read") is True


def test_capability_denies_missing_capability():
    guard = CapabilityGuard([Capability("read-doc", "doc:1", frozenset({"read"}))])
    agent = AgentIdentity("a1", frozenset())
    assert guard.authorize(agent, "read-doc", "doc:1", "read") is False


def test_capability_denies_wrong_resource():
    guard = CapabilityGuard([Capability("read-doc", "doc:1", frozenset({"read"}))])
    agent = AgentIdentity("a1", frozenset({"read-doc"}))
    assert guard.authorize(agent, "read-doc", "doc:2", "read") is False


def test_capability_denies_undeclared_action():
    guard = CapabilityGuard([Capability("read-doc", "doc:1", frozenset({"read"}))])
    agent = AgentIdentity("a1", frozenset({"read-doc"}))
    assert guard.authorize(agent, "read-doc", "doc:1", "write") is False
