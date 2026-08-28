from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from .task_queue import TaskQueue, Task, Status
from .gates import GateEngine, GateDecision
from .evidence import EvidenceLedger

@dataclass(frozen=True)
class RunLimits:
    max_steps: int = 25

@dataclass(frozen=True)
class RunResult:
    steps: int
    decision: str

class AutonomousMissionController:
    """Persistent control loop: execute, verify, record evidence, then gate."""
    def __init__(self, queue: TaskQueue, gates: GateEngine, evidence: EvidenceLedger,
                 limits: RunLimits | None = None):
        self.queue, self.gates, self.evidence = queue, gates, evidence
        self.limits = limits or RunLimits()

    def run(self, execute: Callable[[Task], tuple[Status, dict[str, bool], str]], version: str) -> RunResult:
        steps = 0
        while steps < self.limits.max_steps:
            task = self.queue.claim_next()
            if task is None:
                return RunResult(steps, "IDLE")
            steps += 1
            try:
                status, checks, artifact = execute(task)
                gate = self.gates.evaluate(task.gate, checks)
                result = gate.value
                self.evidence.append(f"{task.task_id}:{steps}", task.title, task.gate,
                                     "gate-evaluation", result, artifact, version)
                if gate is GateDecision.PASS:
                    self.queue.complete(task.task_id, "PASS")
                elif gate is GateDecision.BLOCKED:
                    self.queue.complete(task.task_id, "BLOCKED")
                else:
                    self.queue.fail_or_park(task.task_id)
            except Exception:
                self.queue.fail_or_park(task.task_id)
        return RunResult(steps, "BUDGET_EXHAUSTED")
