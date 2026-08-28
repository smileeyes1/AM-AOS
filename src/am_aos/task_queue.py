from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Literal

Status = Literal["QUEUED", "RUNNING", "VERIFYING", "PASS", "FAIL", "BLOCKED", "PARKED"]

@dataclass
class Task:
    task_id: str
    gate: str
    title: str
    status: Status = "QUEUED"
    retry_count: int = 0
    max_retries: int = 3

class TaskQueue:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: list[Task] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        self.tasks = [Task(**x) for x in json.loads(self.path.read_text())]
        # A process crash can leave leases in RUNNING. Requeue only those tasks;
        # terminal states remain terminal and retry limits remain authoritative.
        changed = False
        for task in self.tasks:
            if task.status == "RUNNING":
                task.status = "QUEUED"
                changed = True
        if changed:
            self._save()

    def _save(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps([asdict(t) for t in self.tasks], indent=2, sort_keys=True))
        tmp.replace(self.path)

    def enqueue(self, task: Task) -> None:
        if any(t.task_id == task.task_id for t in self.tasks):
            return
        self.tasks.append(task)
        self._save()

    def claim_next(self) -> Task | None:
        for task in self.tasks:
            if task.status == "QUEUED":
                task.status = "RUNNING"
                self._save()
                return task
        return None

    def complete(self, task_id: str, status: Status) -> None:
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = status
                self._save()
                return
        raise KeyError(task_id)

    def fail_or_park(self, task_id: str) -> Status:
        for task in self.tasks:
            if task.task_id == task_id:
                task.retry_count += 1
                task.status = "QUEUED" if task.retry_count < task.max_retries else "PARKED"
                self._save()
                return task.status
        raise KeyError(task_id)
