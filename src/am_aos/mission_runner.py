from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from .task_queue import Task, Status, TaskQueue
from .gates import GateEngine, GateDecision
from .evidence import EvidenceLedger

@dataclass(frozen=True)
class WorkerResult:
    status: Status
    checks: dict[str, bool]
    artifact: str

class WorkerFailure(RuntimeError):
    pass

class WorkerAdapter:
    """Narrow execution boundary. It owns no policy and cannot self-authorize."""
    def __init__(self, execute: Callable[[Task], WorkerResult]):
        self._execute = execute

    def run(self, task: Task) -> WorkerResult:
        return self._execute(task)

class MissionRunner:
    """Glue layer for queue -> worker -> verification -> evidence -> state transition."""
    def __init__(self, queue: TaskQueue, worker: WorkerAdapter,
                 gates: GateEngine, evidence: EvidenceLedger):
        self.queue, self.worker, self.gates, self.evidence = queue, worker, gates, evidence

    def step(self, version: str) -> GateDecision | None:
        task = self.queue.claim_next()
        if task is None:
            return None
        try:
            result = self.worker.run(task)
            decision = self.gates.evaluate(task.gate, result.checks)
            self.evidence.append(f"{task.task_id}:gate", task.title, task.gate,
                                 "worker-result-and-gate", decision.value,
                                 result.artifact, version)
            if decision is GateDecision.PASS:
                self.queue.complete(task.task_id, "PASS")
            elif decision is GateDecision.BLOCKED:
                self.queue.complete(task.task_id, "BLOCKED")
            else:
                self.queue.fail_or_park(task.task_id)
            return decision
        except Exception as exc:
            self.queue.fail_or_park(task.task_id)
            raise WorkerFailure(str(exc)) from exc
