from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any, Callable
from uuid import uuid4


class Decision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NO_GO = "NO-GO"


@dataclass(frozen=True)
class MissionContract:
    mission_id: str
    goal: str
    acceptance_criteria: tuple[str, ...]
    constitutional_constraints: tuple[str, ...]
    allowed_authorities: frozenset[str]


@dataclass
class Task:
    task_id: str
    mission_id: str
    description: str
    authority: str
    verifier: str
    status: Decision | None = None
    result: Any = None
    evidence_ids: list[str] = field(default_factory=list)
    attempts: int = 0


@dataclass(frozen=True)
class Agent:
    agent_id: str
    authorities: frozenset[str]
    execute: Callable[[Task], Any]


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    task_id: str
    claim: str
    value: Any
    sufficient: bool
    source: str
    digest: str


def _digest(value: Any) -> str:
    raw = repr(value).encode("utf-8")
    return sha256(raw).hexdigest()


class AuditLedger:
    """Append-only in-memory ledger for the prototype runtime."""

    def __init__(self):
        self.events: list[dict[str, Any]] = []

    def append(self, event: str, subject: str, **data: Any) -> None:
        self.events.append({
            "event_id": f"evt-{uuid4().hex[:12]}",
            "event": event,
            "subject": subject,
            "data": data,
        })


class EvidenceLedger:
    def __init__(self):
        self.items: dict[str, Evidence] = {}

    def record(self, task_id: str, claim: str, value: Any, sufficient: bool, source: str) -> str:
        evidence_id = f"ev-{uuid4().hex[:12]}"
        self.items[evidence_id] = Evidence(
            evidence_id=evidence_id,
            task_id=task_id,
            claim=claim,
            value=value,
            sufficient=sufficient,
            source=source,
            digest=_digest(value),
        )
        return evidence_id

    def is_sufficient(self, ids: list[str]) -> bool:
        return bool(ids) and all(eid in self.items and self.items[eid].sufficient for eid in ids)


class AuthorityGuard:
    def authorize(self, mission: MissionContract, task: Task, agent: Agent) -> bool:
        return task.authority in mission.allowed_authorities and task.authority in agent.authorities


class VerificationGate:
    def verify(self, task: Task, evidence: EvidenceLedger) -> tuple[Decision, str]:
        if not evidence.is_sufficient(task.evidence_ids):
            return Decision.BLOCKED, "Evidence is missing or insufficient."
        records = [evidence.items[eid] for eid in task.evidence_ids]
        passed = any(record.value is True or record.value == "PASS" for record in records)
        return (Decision.PASS, "Verified by sufficient evidence.") if passed else (Decision.FAIL, "Evidence does not establish success.")


class AMAOSEngine:
    """Small executable control-plane core; provider/LLM agnostic."""

    def __init__(self):
        self.missions: dict[str, MissionContract] = {}
        self.tasks: dict[str, Task] = {}
        self.agents: dict[str, Agent] = {}
        self.evidence = EvidenceLedger()
        self.audit = AuditLedger()
        self.verification = VerificationGate()
        self.regression_baseline: dict[str, Decision] = {}

    def register_agent(self, agent: Agent) -> None:
        self.agents[agent.agent_id] = agent
        self.audit.append("AGENT_REGISTERED", agent.agent_id, authorities=sorted(agent.authorities))

    def create_mission(self, goal: str, criteria: list[str], constraints: list[str], authorities: list[str]) -> str:
        mission_id = f"mission-{uuid4().hex[:12]}"
        self.missions[mission_id] = MissionContract(
            mission_id, goal, tuple(criteria), tuple(constraints), frozenset(authorities)
        )
        self.audit.append("MISSION_CREATED", mission_id, goal=goal)
        return mission_id

    def add_task(self, mission_id: str, description: str, authority: str, verifier: str) -> str:
        mission = self.missions[mission_id]
        if authority not in mission.allowed_authorities:
            raise PermissionError("Task authority exceeds mission authority ceiling.")
        task_id = f"task-{uuid4().hex[:12]}"
        self.tasks[task_id] = Task(task_id, mission_id, description, authority, verifier)
        self.audit.append("TASK_CREATED", task_id, mission_id=mission_id, authority=authority)
        return task_id

    def execute(self, task_id: str, agent_id: str) -> Decision:
        task = self.tasks[task_id]
        mission = self.missions[task.mission_id]
        agent = self.agents[agent_id]
        if not self._immutable_boundary_intact(mission):
            task.status = Decision.NO_GO
            self.audit.append("BOUNDARY_VIOLATION", task_id)
            return task.status
        if not AuthorityGuard().authorize(mission, task, agent):
            task.status = Decision.NO_GO
            self.audit.append("AUTHORITY_DENIED", task_id, agent_id=agent_id)
            return task.status

        task.attempts += 1
        self.audit.append("TASK_STARTED", task_id, agent_id=agent_id, attempt=task.attempts)
        try:
            task.result = agent.execute(task)
        except Exception as exc:
            task.status = Decision.FAIL
            self.audit.append("EXECUTION_FAILED", task_id, error=type(exc).__name__)
            return task.status

        eid = self.evidence.record(task_id, "execution result", task.result, task.result is not None, f"agent:{agent_id}")
        task.evidence_ids.append(eid)
        self.audit.append("EVIDENCE_RECORDED", task_id, evidence_id=eid)
        task.status, reason = self.verification.verify(task, self.evidence)
        self.audit.append("VERIFICATION", task_id, decision=task.status.value, reason=reason)
        return task.status

    def recover(self, task_id: str, agent_id: str) -> Decision:
        task = self.tasks[task_id]
        self.audit.append("RECOVERY_STARTED", task_id, previous=task.status.value if task.status else None)
        return self.execute(task_id, agent_id)

    def capture_regression_baseline(self) -> None:
        self.regression_baseline = {tid: task.status for tid, task in self.tasks.items() if task.status is not None}
        self.audit.append("REGRESSION_BASELINE_CAPTURED", "system", count=len(self.regression_baseline))

    def regression_check(self) -> tuple[bool, str]:
        for task_id, previous in self.regression_baseline.items():
            current = self.tasks[task_id].status
            if previous == Decision.PASS and current != Decision.PASS:
                self.audit.append("REGRESSION_FAILED", task_id, previous=previous.value, current=current.value if current else None)
                return False, f"Regression detected: {task_id}"
        self.audit.append("REGRESSION_PASSED", "system")
        return True, "Regression gate passed."

    @staticmethod
    def _immutable_boundary_intact(mission: MissionContract) -> bool:
        return bool(mission.goal and mission.allowed_authorities and all(isinstance(c, str) for c in mission.constitutional_constraints))
