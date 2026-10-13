"""Gated tool dispatcher for explicitly trusted local adapters.

This is an execution-boundary integration, NOT an identity provider or OS sandbox.
The caller must authenticate the principal out of band, keep tool registrations
under trusted control, and isolate any untrusted program separately. Unknown,
missing or stale policy/journal state fails closed before invoking a tool.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
import sqlite3
from typing import Callable

from .sovereign_control import MissionContract, Principal, Request, SovereignControl
from .capabilities import AgentIdentity, Capability, CapabilityGuard


class GatewayFailure(RuntimeError):
    """Fail-closed journal or registration boundary failure."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _hash(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class ToolRegistration:
    """Trusted adapter registers the actual handler and exact authority scope."""
    tool_id: str
    resource: str
    action: str
    capability: str
    operation: str
    handler: Callable[[tuple[str, ...]], str]

    def __post_init__(self):
        if not all(isinstance(x, str) and x.strip() for x in (
            self.tool_id, self.resource, self.action, self.capability, self.operation
        )) or not callable(self.handler):
            raise GatewayFailure("invalid trusted tool registration")


@dataclass(frozen=True)
class ToolCall:
    mission_id: str
    tool_id: str
    arguments: tuple[str, ...]
    idempotency_key: str


@dataclass(frozen=True)
class ToolOutcome:
    status: str  # EXECUTED, FAILED, DENIED, BLOCKED; never mission PASS
    reason: str
    result: str | None = None


class ExecutionJournal:
    """SQLite at-most-once claim and append-only event chain for local gateway.

    Bootstrap must be an explicit trusted provisioning action. Without the DB,
    open() fails rather than silently erasing replay history. The hash chain
    detects corruption only when anchored in a separate trusted location; it
    is not tamper-proof against a database administrator.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    @classmethod
    def bootstrap(cls, path: str | Path) -> "ExecutionJournal":
        journal = cls(path)
        journal.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(journal.path) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS claims (
                nonce TEXT PRIMARY KEY, request_hash TEXT NOT NULL,
                status TEXT NOT NULL, result_hash TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL, reference TEXT NOT NULL,
                prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL
            )""")
        return journal

    def _connect(self) -> sqlite3.Connection:
        if not self.path.is_file():
            raise GatewayFailure("journal missing: refuse execution")
        try:
            # URI mode rw forbids implicit creation of a missing database.
            db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=rw",
                                 uri=True, timeout=5.0)
            db.execute("PRAGMA busy_timeout=5000")
            tables = {r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"claims", "events"}.issubset(tables):
                raise GatewayFailure("journal schema missing")
            return db
        except (sqlite3.Error, OSError) as exc:
            raise GatewayFailure("journal unavailable or corrupt") from exc

    @contextmanager
    def _open(self):
        db = self._connect()
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _assert_chain(db: sqlite3.Connection) -> None:
        prev = "GENESIS"
        for kind, reference, prev_hash, event_hash in db.execute(
                "SELECT kind,reference,prev_hash,event_hash FROM events ORDER BY seq"):
            if prev_hash != prev or event_hash != _hash([prev, kind, reference]):
                raise GatewayFailure("audit chain integrity failed; refuse execution")
            prev = event_hash

    @staticmethod
    def _event(db: sqlite3.Connection, kind: str, reference: str) -> None:
        row = db.execute("SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else "GENESIS"
        digest = _hash([prev, kind, reference])
        db.execute("INSERT INTO events(kind,reference,prev_hash,event_hash) VALUES (?,?,?,?)",
                   (kind, reference, prev, digest))

    def record_denial(self, reason: str) -> None:
        try:
            with self._open() as db:
                db.execute("BEGIN IMMEDIATE")
                self._assert_chain(db)
                self._event(db, "DENIED", _hash(reason))
        except (sqlite3.Error, OSError) as exc:
            raise GatewayFailure("denial audit could not be persisted") from exc

    def claim(self, nonce: str, request_hash: str) -> bool:
        """Durably reserve nonce before side effect. A replay never executes."""
        try:
            with self._open() as db:
                db.execute("BEGIN IMMEDIATE")
                self._assert_chain(db)
                row = db.execute("SELECT request_hash FROM claims WHERE nonce=?", (nonce,)).fetchone()
                if row is not None:
                    self._event(db, "REPLAY_OR_COLLISION", _hash(nonce))
                    return False
                db.execute("INSERT INTO claims(nonce,request_hash,status) VALUES (?,?,'STARTED')",
                           (nonce, request_hash))
                self._event(db, "CLAIMED", _hash([nonce, request_hash]))
                return True
        except (sqlite3.Error, OSError) as exc:
            raise GatewayFailure("cannot claim durable execution token") from exc

    def finish(self, nonce: str, status: str, result_hash: str | None) -> None:
        try:
            with self._open() as db:
                db.execute("BEGIN IMMEDIATE")
                self._assert_chain(db)
                row = db.execute("SELECT status FROM claims WHERE nonce=?", (nonce,)).fetchone()
                if row is None or row[0] != "STARTED":
                    raise GatewayFailure("unexpected execution claim state")
                db.execute("UPDATE claims SET status=?, result_hash=? WHERE nonce=?",
                           (status, result_hash, nonce))
                self._event(db, status, _hash(nonce))
        except (sqlite3.Error, OSError) as exc:
            raise GatewayFailure("completion audit could not be persisted") from exc

    def verify_events(self) -> bool:
        try:
            with self._open() as db:
                try:
                    self._assert_chain(db)
                    return True
                except GatewayFailure:
                    return False
        except sqlite3.Error as exc:
            raise GatewayFailure("audit unavailable") from exc


class TrustedExecutionGateway:
    """Runs an approved registered handler, never an unregistered user tool.

    Principal MUST come from a trusted authenticated adapter. This API cannot
    prove identity of arbitrary Python callers, nor isolate handler subprocesses.
    """

    def __init__(self, policy: SovereignControl, journal: ExecutionJournal,
                 registrations: tuple[ToolRegistration, ...]):
        if not registrations or len({r.tool_id for r in registrations}) != len(registrations):
            raise GatewayFailure("tool registry empty or duplicate tool id")
        grants: dict[str, tuple[str, str]] = {}
        for reg in registrations:
            scope = (reg.resource, reg.action)
            if reg.capability in grants and grants[reg.capability] != scope:
                raise GatewayFailure("capability reused for conflicting resource or action")
            grants[reg.capability] = scope
        self.policy = policy
        self.journal = journal
        self.registry = MappingProxyType({r.tool_id: r for r in registrations})
        self._guards = MappingProxyType({r.tool_id: CapabilityGuard([
            Capability(r.capability, r.resource, frozenset({r.action}))])
            for r in registrations})

    def invoke(self, mission: MissionContract, principal: Principal | None,
               call: ToolCall) -> ToolOutcome:
        if (not isinstance(call, ToolCall) or not isinstance(call.mission_id, str)
            or not isinstance(call.tool_id, str) or not isinstance(call.idempotency_key, str)
            or not (1 <= len(call.idempotency_key) <= 200)
            or not isinstance(call.arguments, tuple)
            or len(call.arguments) > 20
            or any(not isinstance(arg, str) or len(arg) > 8192 for arg in call.arguments)):
            self.journal.record_denial("invalid tool call")
            return ToolOutcome("DENIED", "invalid tool call")

        reg = self.registry.get(call.tool_id)
        if reg is None or principal is None or not isinstance(principal, Principal):
            self.journal.record_denial("unknown tool or missing authenticated principal")
            return ToolOutcome("DENIED", "unknown tool or missing authenticated principal")
        if call.mission_id != mission.mission_id:
            self.journal.record_denial("mission mismatch")
            return ToolOutcome("DENIED", "mission mismatch")

        # The request scope comes from the trusted registration, NOT user text.
        decision = self.policy.authorize(mission, principal, Request(
            call.mission_id, reg.operation, reg.capability))
        if not decision.allowed:
            self.journal.record_denial(decision.reason)
            return ToolOutcome("DENIED", decision.reason)

        # Require the exact registered action/resource capability at dispatch.
        if not self._guards[reg.tool_id].authorize(
                AgentIdentity(principal.principal_id, principal.capabilities),
                reg.capability, reg.resource, reg.action):
            self.journal.record_denial("resource/action capability denied")
            return ToolOutcome("DENIED", "resource/action capability denied")
        fingerprint = _hash({
            "policy": self.policy.profile_sha256,
            "mission_id": mission.mission_id, "goal": mission.goal,
            "ceiling": sorted(mission.authority_ceiling),
            "principal": principal.principal_id, "grants": sorted(principal.capabilities),
            "tool": reg.tool_id, "resource": reg.resource,
            "action": reg.action, "capability": reg.capability,
            "operation": reg.operation, "args": call.arguments,
        })
        if not self.journal.claim(call.idempotency_key, fingerprint):
            return ToolOutcome("BLOCKED", "duplicate or conflicting execution token")

        # The only place the side-effecting tool is called by this gateway.
        try:
            result = reg.handler(call.arguments)
            if not isinstance(result, str):
                raise TypeError("tool returned non-string result")
        except Exception:
            self.journal.finish(call.idempotency_key, "FAILED", None)
            return ToolOutcome("FAILED", "registered tool failed; no automatic retry")
        self.journal.finish(call.idempotency_key, "EXECUTED", _hash(result))
        return ToolOutcome("EXECUTED", "handler returned; outcome not independently verified", result)
