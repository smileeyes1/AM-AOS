from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable

from .runtime import AMAOSEngine, Decision, EvidenceState


class MissionPhase(str, Enum):
    UNDERSTAND = "UNDERSTAND"
    EXTRACT = "EXTRACT"
    INTEGRITY = "INTEGRITY"
    FREEZE = "FREEZE"
    EVIDENCE_PLAN = "EVIDENCE_PLAN"
    RISK = "RISK"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    BREAK = "BREAK"
    REPAIR = "REPAIR"
    REVERIFY = "REVERIFY"
    REGRESSION = "REGRESSION"
    EVIDENCE_AUDIT = "EVIDENCE_AUDIT"
    CLAIM_SCOPE = "CLAIM_SCOPE"
    DECIDE = "DECIDE"
    RELEASE = "RELEASE"


@dataclass(frozen=True)
class MissionPolicy:
    max_attempts: int = 3
    require_evidence: bool = True
    require_regression_after_repair: bool = True
    allow_direct_delivery: bool = True
    require_external_approval: bool = False


@dataclass
class MissionRun:
    mission_id: str
    phase: MissionPhase = MissionPhase.UNDERSTAND
    decisions: list[Decision] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    released: bool = False
    delivery_id: str | None = None


class AutonomyController:
    """Bounded autonomy: drives a mission, but never enlarges authority or claim scope."""

    def __init__(self, engine: AMAOSEngine, policy: MissionPolicy | None = None):
        self.engine = engine
        self.policy = policy or MissionPolicy()
        self.runs: dict[str, MissionRun] = {}

    def run(
        self,
        mission_id: str,
        task_ids: Iterable[str],
        agent_id: str,
        verify: Callable[[object, tuple[str, ...]], bool],
        break_test: Callable[[object], bool] | None = None,
        repair: Callable[[object], object] | None = None,
    ) -> MissionRun:
        run = MissionRun(mission_id)
        self.runs[mission_id] = run
        mission = self.engine.missions[mission_id]
        tasks = [self.engine.tasks[t] for t in task_ids]
        if not mission.goal.strip() or not mission.acceptance_criteria or not mission.scope:
            run.phase = MissionPhase.INTEGRITY
            run.decisions.append(Decision.BLOCKED)
            run.findings.append("mission contract incomplete: goal, criteria and scope are required")
            return run

        run.phase = MissionPhase.FREEZE
        run.phase = MissionPhase.EVIDENCE_PLAN
        run.phase = MissionPhase.RISK
        run.phase = MissionPhase.PLAN
        run.phase = MissionPhase.EXECUTE
        for task in tasks:
            if task.attempts >= self.policy.max_attempts:
                run.decisions.append(Decision.BLOCKED)
                run.findings.append(f"attempt ceiling reached: {task.task_id}")
                continue
            self.engine.execute(task.task_id, agent_id)

        # Freeze the pre-repair state before any adversarial mutation.
        self.engine.capture_regression_baseline()

        run.phase = MissionPhase.VERIFY
        for task in tasks:
            evidence = tuple(self.engine.evidence.items[e] for e in task.evidence_ids if e in self.engine.evidence.items)
            if self.policy.require_evidence and not evidence:
                run.decisions.append(Decision.NOT_PROVEN)
                run.findings.append(f"no evidence: {task.task_id}")
                continue
            if any(e.state not in {EvidenceState.REPRODUCIBLE, EvidenceState.VERIFIED} for e in evidence):
                run.decisions.append(Decision.NOT_PROVEN)
                run.findings.append(f"evidence state insufficient: {task.task_id}")
                continue
            if not verify(task.result, mission.acceptance_criteria):
                task.status = Decision.FAIL
                run.decisions.append(Decision.FAIL)
                run.findings.append(f"acceptance verification failed: {task.task_id}")
            else:
                task.status = Decision.PASS
                run.decisions.append(Decision.PASS)

        run.phase = MissionPhase.BREAK
        repaired = False
        for task in tasks:
            if break_test is not None and break_test(task.result):
                task.status = Decision.FAIL
                run.decisions.append(Decision.FAIL)
                run.findings.append(f"adversarial fault detected: {task.task_id}")
                if repair is not None:
                    repaired = True
                    run.phase = MissionPhase.REPAIR
                    task.result = repair(task.result)
                    run.phase = MissionPhase.REVERIFY
                    if verify(task.result, mission.acceptance_criteria):
                        task.status = Decision.PASS
                    else:
                        task.status = Decision.NO_GO
                        run.findings.append(f"repair verification failed: {task.task_id}")

        run.phase = MissionPhase.REGRESSION
        if repaired and self.policy.require_regression_after_repair:
            if not self.engine.regression_check():
                run.decisions.append(Decision.NO_GO)
                run.findings.append("regression failed after repair")

        run.phase = MissionPhase.EVIDENCE_AUDIT
        if not self.engine.audit.verify_chain():
            run.decisions.append(Decision.NO_GO)
            run.findings.append("audit chain integrity failure")

        run.phase = MissionPhase.CLAIM_SCOPE
        run.phase = MissionPhase.DECIDE
        if Decision.NO_GO in run.decisions:
            final = Decision.NO_GO
        elif Decision.FAIL in run.decisions:
            final = Decision.FAIL
        elif Decision.NOT_PROVEN in run.decisions or Decision.BLOCKED in run.decisions:
            final = Decision.NOT_PROVEN
        elif tasks:
            final = Decision.PASS
        else:
            final = Decision.BLOCKED
        run.decisions.append(final)

        run.phase = MissionPhase.RELEASE
        run.released = (
            final in {Decision.PASS, Decision.CONDITIONAL_PASS}
            and self.policy.allow_direct_delivery
            and not self.policy.require_external_approval
        )
        return run
