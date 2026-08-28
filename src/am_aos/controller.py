from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .task_queue import TaskQueue, Task, Status


@dataclass(frozen=True)
class ControllerLimits:
    max_steps: int = 25


class AutonomousController:
    """Deterministic orchestration shell; policy remains outside worker code."""

    def __init__(self, queue: TaskQueue, limits: ControllerLimits | None = None):
        self.queue = queue
        self.limits = limits or ControllerLimits()

    def run(self, execute: Callable[[Task], Status]) -> int:
        steps = 0
        while steps < self.limits.max_steps:
            task = self.queue.claim_next()
            if task is None:
                break
            steps += 1
            try:
                status = execute(task)
            except Exception:
                self.queue.fail_or_park(task.task_id)
                continue
            if status == "PASS":
                self.queue.complete(task.task_id, "PASS")
            elif status == "BLOCKED":
                self.queue.complete(task.task_id, "BLOCKED")
            else:
                self.queue.fail_or_park(task.task_id)
        return steps
