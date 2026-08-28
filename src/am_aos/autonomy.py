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
    REPLAN="REPLAN"; STOP="STOP"

@dataclass(frozen=True)
class AutonomyLimits:
    max_cycles: int = 20
    max_repairs: int = 5
    max_attempts_per_task: int = 3
    wall_clock_seconds: float = 300.0
    max_stagnant_cycles: int = 2

@dataclass
class MissionRun(Generic[T]):
    mission_id: str
    phase: Phase = Phase.UNDERSTAND
    decision: Decision | None = None
    cycles: int = 0
    repairs: int = 0
    replans: int = 0
    history: list[Phase] = field(default_factory=list)
    output: T | None = None
    stop_reason: str | None = None

class AutonomousController(Generic[T]):
    """Bounded self-driving mission loop: execute, verify, attack, repair, regress, replan and release without widening authority."""
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
        replan: Callable[[T, Decision], None] | None = None,
        progress_key: Callable[[T], object] | None = None,
        checkpoint: Callable[[MissionRun[T]], None] | None = None,
    ) -> MissionRun[T]:
        started = self._clock(); run = MissionRun[T](mission_id=mission_id)
        last_key: object | None = None
        stagnant = 0

        def enter(p: Phase) -> None:
            run.phase = p; run.history.append(p)
            if checkpoint is not None:
                checkpoint(run)

        enter(Phase.UNDERSTAND); enter(Phase.EXTRACT); enter(Phase.INTEGRITY); enter(Phase.FREEZE)
        enter(Phase.EVIDENCE_PLAN); enter(Phase.RISK); enter(Phase.PLAN); plan()

        while run.cycles < self.limits.max_cycles:
            if self._clock() - started > self.limits.wall_clock_seconds:
                run.decision = Decision.BLOCKED; run.stop_reason = "WALL_CLOCK_LIMIT"; enter(Phase.STOP); return run

            run.cycles += 1; enter(Phase.EXECUTE)
            run.output = execute()
            enter(Phase.VERIFY); run.decision = verify(run.output)

            if run.decision not in (Decision.PASS, Decision.CONDITIONAL_PASS):
                if replan is None:
                    run.stop_reason = "VERIFICATION_NOT_RELEASEABLE"; enter(Phase.STOP); return run
                run.replans += 1; enter(Phase.REPLAN); replan(run.output, run.decision)
                continue

            enter(Phase.BREAK)
            fault = break_test(run.output)
            if fault:
                if run.repairs >= self.limits.max_repairs:
                    run.decision = Decision.NO_GO; run.stop_reason = "REPAIR_LIMIT"; enter(Phase.STOP); return run
                run.repairs += 1; enter(Phase.REPAIR); run.output = repair(run.output)
                enter(Phase.REVERIFY); run.decision = verify(run.output)
                if run.decision not in (Decision.PASS, Decision.CONDITIONAL_PASS):
                    if replan is None:
                        run.stop_reason = "REPAIR_REVERIFY_FAILURE"; enter(Phase.STOP); return run
                    run.replans += 1; enter(Phase.REPLAN); replan(run.output, run.decision); continue
                enter(Phase.REGRESSION)
                if not regression(run.output):
                    run.decision = Decision.NO_GO; run.stop_reason = "REGRESSION_FAILURE"; enter(Phase.STOP); return run
            else:
                enter(Phase.REGRESSION)
                if not regression(run.output):
                    run.decision = Decision.NO_GO; run.stop_reason = "REGRESSION_FAILURE"; enter(Phase.STOP); return run

            enter(Phase.EVIDENCE_AUDIT)
            if not audit(run.output):
                run.decision = Decision.NOT_PROVEN; run.stop_reason = "EVIDENCE_AUDIT_FAILURE"; enter(Phase.STOP); return run
            enter(Phase.CLAIM_SCOPE)
            if not claim_scope(run.output):
                run.decision = Decision.NOT_PROVEN; run.stop_reason = "CLAIM_SCOPE_FAILURE"; enter(Phase.STOP); return run

            if progress_key is not None:
                key = progress_key(run.output)
                if key == last_key:
                    stagnant += 1
                else:
                    stagnant = 0
                last_key = key
                if stagnant >= self.limits.max_stagnant_cycles:
                    if replan is None:
                        run.decision = Decision.BLOCKED; run.stop_reason = "STAGNATION"; enter(Phase.STOP); return run
                    run.replans += 1; stagnant = 0; enter(Phase.REPLAN); replan(run.output, run.decision); continue

            enter(Phase.DECIDE)
            if run.decision not in (Decision.PASS, Decision.CONDITIONAL_PASS):
                run.decision = Decision.BLOCKED if run.decision in (Decision.INCONCLUSIVE, Decision.BLOCKED) else run.decision
                run.stop_reason = "DECISION_NOT_RELEASEABLE"; enter(Phase.STOP); return run
            enter(Phase.RELEASE); release(run.output); return run

        run.decision = Decision.BLOCKED; run.stop_reason = "CYCLE_LIMIT"; enter(Phase.STOP); return run
