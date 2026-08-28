from am_aos.autonomy import AutonomousController, AutonomyLimits, Phase
from am_aos.capabilities import Capability, CapabilityGateway, AgentIdentity, CapabilityDenied
from am_aos.tenancy import TenantContext, TenantGuard, TenantBoundaryError
from am_aos.recovery import CheckpointStore
from am_aos.idempotency import IdempotencyStore, IdempotencyConflict
from am_aos.runtime import Decision


def test_autonomy_repairs_then_regresses_before_release():
    state = {"fault": True, "runs": 0}
    def execute(): state["runs"] += 1; return dict(state)
    def verify(x): return Decision.PASS if not x["fault"] else Decision.FAIL
    def repair(x): state["fault"] = False; return dict(state)
    delivered = []
    run = AutonomousController(AutonomyLimits(max_cycles=3, max_repairs=1)).run(
        "m1", plan=lambda: None, execute=execute, verify=verify,
        break_test=lambda x: x["fault"], repair=repair,
        regression=lambda x: not x["fault"], audit=lambda x: True,
        claim_scope=lambda x: True, release=lambda x: delivered.append(x),
    )
    assert run.phase is Phase.RELEASE
    assert run.repairs == 1 and delivered


def test_capability_and_tenant_boundaries_are_fail_closed():
    gw = CapabilityGateway({"read": Capability("read", "LOW")})
    agent = AgentIdentity("a", "tenant-a", frozenset({"read"}))
    assert gw.invoke(agent, "read", "tenant-a", lambda: 7).value == 7
    try: gw.invoke(agent, "read", "tenant-b", lambda: 7)
    except CapabilityDenied: pass
    else: raise AssertionError("cross-tenant invocation must be denied")
    try: TenantGuard.require(TenantContext("tenant-a", "p"), "tenant-b")
    except TenantBoundaryError: pass
    else: raise AssertionError("cross-tenant resource access must be denied")


def test_checkpoint_tampering_is_detected():
    store = CheckpointStore(); cp = store.save("m", {"phase": "VERIFY"})
    assert store.verify(cp)
    cp.state["phase"] = "RELEASE"
    assert not store.verify(cp)


def test_idempotency_conflict_is_fail_closed():
    store = IdempotencyStore(); store.put("delivery", "k", "a")
    try: store.put("delivery", "k", "b")
    except IdempotencyConflict: pass
    else: raise AssertionError("idempotency key reuse must be rejected")
