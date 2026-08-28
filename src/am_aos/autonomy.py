from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Callable, Generic, TypeVar

from .runtime import Decision

T = TypeVar("T")

class Phase(str, Enum):
    UNDERSTAND="UNDERSTAND"; EXTRACT="EXTRACT"; INTEGRITY="INTEGRITY"; FREEZE="FREEZE"
    EVIDENCE_PLAN="EVIDENCE_PLAN"; RISK="RISK"; PLAN="PLAN"; EXECUTE="EXECUTE"
    VERIFY="VERIFY"; BREAK="BREAK"; REPAIR="REPAIR"; REVERIFY="REVERIFY"; REGRESSION="REGRESSION"
    EVIDENCE_AUDIT="EVIDENCE_AUDIT"; CLAIM_SCOPE="CLAIM-SCOPE"; DECIDE="DECIDE"; RELEASE="RELEASE"
    STOP="STOP"

@dataclass(frozen=True)
class AutonomyLimits:
    max_cycles: int = 20
    max_repairs: int = 5
    max_attempts_per_task: int = 3
    wall_clock_seconds: float = 300.0

@dataclass
class MissionRun(Generic[T]):
    mission_id: str
    phase: Phase = Phase.UNDERSTAND
    decision: Decision | None = None
    cycles: int = 0
    repairs: int = 0
    history: list[Phase] = field(default_factory=list)
    output: T | None = None
    stop_reason: str | None = None

class AutonomousController(Generic[T]):
    """Bounded autonomous loop. It can continue, replan, repair and stop, but cannot widen authority."""
    def __init__(self, limits: AutonomyLimits | None = None, clock: Callable[[], float] = monotonic):
        self.limits = limits or AutonomyLimits()
        self._clock = clock

    def run(
        self,
        mission_id: str,
        *,
        plan: Callable[[], None],
        execute: Callable[[], T],
        verify: Callable[[T], Decision],
        break_test: Callable[[T], bool],
        repair: Callable[[T], T],
        regression: Callable[[T], bool],
        audit: Callable[[T], bool],
        claim_scope: Callable[[T], bool],
        release: Callable[[T], None],
    ) -> MissionRun[T]:
        started = self._clock(); run = MissionRun[T](mission_id=mission_id)
        def enter(p: Phase) -> None:
            run.phase = p; run.history.append(p)
        enter(Phase.UNDERSTAND); enter(Phase.EXTRACT); enter(Phase.INTEGRITY); enter(Phase.FREEZE)
        enter(Phase.EVIDENCE_PLAN); enter(Phase.RISK); enter(Phase.PLAN); plan()
        while run.cycles < self.limits.max_cycles:
            if self._clock() - started > self.limits.wall_clock_seconds:
                run.decision = Decision.BLOCKED; run.stop_reason = "WALL_CLOCK_LIMIT"; enter(Phase.STOP); return run
            run.cycles += 1; enter(Phase.EXECUTE); run.output = execute()
            enter(Phase.VERIFY); run.decision = verify(run.output)
            enter(Phase.BREAK)
            fault = break_test(run.output)
            if fault:
                if run.repairs >= self.limits.max_repairs:
                    run.decision = Decision.NO_GO; run.stop_reason = "REPAIR_LIMIT"; enter(Phase.STOP); return run
                run.repairs += 1; enter(Phase.REPAIR); run.output = repair(run.output)
                enter(Phase.REVERIFY); run.decision = verify(run.output)
                enter(Phase.REGRESSION)
                if not regression(run.output):
                    run.decision = Decision.NO_GO; run.stop_reason = "REGRESSION_FAILURE"; enter(Phase.STOP); return run
                continue
            enter(Phase.REGRESSION)
            if not regression(run.output):
                run.decision = Decision.NO_GO; run.stop_reason = "REGRESSION_FAILURE"; enter(Phase.STOP); return run
            enter(Phase.EVIDENCE_AUDIT)
            if not audit(run.output):
                run.decision = Decision.NOT_PROVEN; run.stop_reason = "EVIDENCE_AUDIT_FAILURE"; enter(Phase.STOP); return run
            enter(Phase.CLAIM_SCOPE)
            if not claim_scope(run.output):
                run.decision = Decision.NOT_PROVEN; run.stop_reason = "CLAIM_SCOPE_FAILURE"; enter(Phase.STOP); return run
            enter(Phase.DECIDE)
            if run.decision not in (Decision.PASS, Decision.CONDITIONAL_PASS):
                run.decision = Decision.BLOCKED if run.decision in (Decision.INCONCLUSIVE, Decision.BLOCKED) else run.decision
                run.stop_reason = "DECISION_NOT_RELEASEABLE"; enter(Phase.STOP); return run
            enter(Phase.RELEASE); release(run.output); return run
        run.decision = Decision.BLOCKED; run.stop_reason = "CYCLE_LIMIT"; enter(Phase.STOP); return run
