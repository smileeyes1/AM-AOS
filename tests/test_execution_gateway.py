"""Adversarial tests for actual registered-handler invocation and durable tokens."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import pytest

from am_aos.execution_gateway import (ExecutionJournal, GatewayFailure, ToolCall,
    ToolRegistration, TrustedExecutionGateway)
from am_aos.sovereign_control import MissionContract, Principal, SovereignControl

PROFILE = Path(__file__).resolve().parents[1] / "control/sovereign-profile-v1.json"


def setup_gateway(tmp_path, handler=None):
    journal = ExecutionJournal.bootstrap(tmp_path / "state" / "journal.db")
    count = []
    def tracked(args):
        count.append(args)
        return "ran"
    reg = ToolRegistration("lesson-builder", "classroom:demo", "execute",
                           "build-lesson", "build", handler or tracked)
    gate = TrustedExecutionGateway(SovereignControl.from_file(PROFILE), journal, (reg,))
    mission = MissionContract("m1", "Produce lesson", frozenset({"build-lesson"}))
    principal = Principal("verified-upstream", frozenset({"build-lesson"}))
    call = ToolCall("m1", "lesson-builder", ("one",), "nonce-1")
    return gate, mission, principal, call, journal, count


def test_authorized_registered_handler_called_once(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    out = gate.invoke(m, p, call)
    assert out.status == "EXECUTED" and out.result == "ran"
    assert len(count) == 1 and journal.verify_events()


def test_no_authenticated_principal_no_side_effect(tmp_path):
    gate, m, _, call, _, count = setup_gateway(tmp_path)
    assert gate.invoke(m, None, call).status == "DENIED"
    assert count == []


def test_unregistered_tool_cannot_execute(tmp_path):
    gate, m, p, call, _, count = setup_gateway(tmp_path)
    altered = ToolCall(call.mission_id, "other", call.arguments, call.idempotency_key)
    assert gate.invoke(m, p, altered).status == "DENIED"
    assert not count


def test_mission_mismatch_blocks_runner(tmp_path):
    gate, m, p, call, _, count = setup_gateway(tmp_path)
    altered = ToolCall("m2", call.tool_id, call.arguments, call.idempotency_key)
    assert gate.invoke(m, p, altered).status == "DENIED" and not count


def test_principal_capability_is_required(tmp_path):
    gate, m, _, call, _, count = setup_gateway(tmp_path)
    assert gate.invoke(m, Principal("p", frozenset()), call).status == "DENIED"
    assert not count


def test_mission_authority_ceiling_is_required(tmp_path):
    gate, m, p, call, _, count = setup_gateway(tmp_path)
    restricted = MissionContract(m.mission_id, m.goal, frozenset({"read-course"}))
    assert gate.invoke(restricted, p, call).status == "DENIED"
    assert not count


def test_high_impact_tool_cannot_use_exec_path(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    critical = TrustedExecutionGateway(gate.policy, journal, (
        ToolRegistration("lesson-builder", "classroom:demo", "execute",
                         "build-lesson", "delete", lambda args: "unexpected"),))
    assert critical.invoke(m, p, call).status == "DENIED" and not count


def test_duplicate_nonce_not_replayed_across_gateway_restarts(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    assert gate.invoke(m, p, call).status == "EXECUTED"
    # Reload durable journal in a new object (simulates process restart).
    second = TrustedExecutionGateway(gate.policy, ExecutionJournal(journal.path),
                                     tuple(gate.registry.values()))
    assert second.invoke(m, p, call).status == "BLOCKED"
    assert len(count) == 1


def test_changed_args_same_nonce_denied(tmp_path):
    gate, m, p, call, _, count = setup_gateway(tmp_path)
    assert gate.invoke(m, p, call).status == "EXECUTED"
    altered = ToolCall(call.mission_id, call.tool_id, ("two",), call.idempotency_key)
    assert gate.invoke(m, p, altered).status == "BLOCKED"
    assert len(count) == 1


def test_crash_fails_without_auto_reexecution(tmp_path):
    calls = []
    def boom(args):
        calls.append(1)
        raise RuntimeError("crash")
    gate, m, p, call, _, _ = setup_gateway(tmp_path, boom)
    assert gate.invoke(m, p, call).status == "FAILED"
    assert gate.invoke(m, p, call).status == "BLOCKED"
    assert calls == [1]


def test_abandoned_started_token_parked(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    assert journal.claim(call.idempotency_key, "other-digest")
    assert gate.invoke(m, p, call).status == "BLOCKED"
    assert not count


def test_missing_journal_fails_closed(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    journal.path.unlink()
    with pytest.raises(GatewayFailure):
        gate.invoke(m, p, call)
    assert not count


def test_corrupt_journal_fails_closed(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    with sqlite3.connect(journal.path) as db:
        db.execute("DROP TABLE events")
    with pytest.raises(GatewayFailure):
        gate.invoke(m, p, call)
    assert not count


def test_invalid_request_denied(tmp_path):
    gate, m, p, call, _, count = setup_gateway(tmp_path)
    bad = ToolCall("m1", "lesson-builder", ("x" * 9000,), "nonce")
    assert gate.invoke(m, p, bad).status == "DENIED" and not count


def test_registry_duplicate_fails_closed(tmp_path):
    gate, _, _, _, journal, _ = setup_gateway(tmp_path)
    with pytest.raises(GatewayFailure):
        TrustedExecutionGateway(gate.policy, journal, tuple(gate.registry.values()) * 2)


def test_parallel_same_token_executes_once(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda _: gate.invoke(m, p, call).status, range(12)))
    assert results.count("EXECUTED") == 1
    assert results.count("BLOCKED") == 11
    assert len(count) == 1
    assert journal.verify_events()


def test_explicit_local_handler_side_effect_only_after_gate(tmp_path):
    marker = tmp_path / "proof.txt"
    def write_marker(args):
        marker.write_text("ok")
        return "recorded"
    gate, m, p, call, _, _ = setup_gateway(tmp_path, write_marker)
    assert gate.invoke(m, None, call).status == "DENIED" and not marker.exists()
    assert gate.invoke(m, p, call).status == "EXECUTED"
    assert marker.read_text() == "ok"


def test_audit_integrity_detects_tampering(tmp_path):
    gate, m, p, call, journal, _ = setup_gateway(tmp_path)
    assert gate.invoke(m, p, call).status == "EXECUTED"
    assert journal.verify_events()
    with sqlite3.connect(journal.path) as db:
        db.execute("UPDATE events SET kind='MUTATED' WHERE seq=1")
    assert not journal.verify_events()


def test_audit_tamper_prevents_future_effects(tmp_path):
    gate, m, p, call, journal, count = setup_gateway(tmp_path)
    assert gate.invoke(m, p, call).status == "EXECUTED"
    with sqlite3.connect(journal.path) as db:
        db.execute("UPDATE events SET kind='ALTERED' WHERE seq=1")
    with pytest.raises(GatewayFailure):
        gate.invoke(m, p, ToolCall(m.mission_id, call.tool_id, ("two",), "new-nonce"))
    assert len(count) == 1


def test_gate_controls_actual_worker_subprocess_invocation(tmp_path):
    """Proves dispatch reaches the existing Worker only after authorization.

    Deliberately harmless fixture code; Worker is not an OS sandbox.
    """
    from am_aos.worker import SandboxWorker, SandboxPolicy

    root = tmp_path / "worker"
    worker = SandboxWorker(root, SandboxPolicy(timeout_seconds=15.0))
    executed = []
    def handler(args):
        executed.append(True)
        command = ["python", "-c",
                   "from pathlib import Path;Path('marker.txt').write_text('test-only')"]
        result = worker.execute(command)
        if result.status != "PASS":
            raise RuntimeError("worker failed")
        return "worker executed"

    gate, mission, principal, call, _, _ = setup_gateway(tmp_path, handler)
    assert gate.invoke(mission, None, call).status == "DENIED"
    assert not (root / "marker.txt").exists()
    assert executed == []
    assert gate.invoke(mission, principal, call).status == "EXECUTED"
    assert (root / "marker.txt").read_text() == "test-only"
    assert executed == [True]


def test_conflicting_resource_scope_for_same_capability_refused(tmp_path):
    gate, _, _, _, journal, _ = setup_gateway(tmp_path)
    reg = gate.registry["lesson-builder"]
    different = ToolRegistration("another", "student-records:private", "read",
                                 reg.capability, reg.operation, lambda _: "bad")
    with pytest.raises(GatewayFailure, match="conflicting resource"):
        TrustedExecutionGateway(gate.policy, journal, (reg, different))


def test_registry_cannot_be_silently_replaced(tmp_path):
    gate, _, _, _, _, _ = setup_gateway(tmp_path)
    with pytest.raises(TypeError):
        gate.registry["hidden"] = gate.registry["lesson-builder"]
