from pathlib import Path

from am_aos.controller import AutonomousController, ControllerLimits
from am_aos.task_queue import Task, TaskQueue


def test_e2e_restart_resume_failure_retry_and_completion(tmp_path: Path):
    queue_path = tmp_path / "state" / "tasks.json"
    queue = TaskQueue(queue_path)
    queue.enqueue(Task("build", "G2", "build", max_retries=3))
    queue.enqueue(Task("verify", "G5", "verify", max_retries=3))

    attempts = {"build": 0, "verify": 0}

    def crashing_worker(task: Task):
        attempts[task.task_id] += 1
        if task.task_id == "build" and attempts[task.task_id] == 1:
            raise RuntimeError("simulated worker crash")
        return "PASS"

    # First process dies while executing the first task.
    first = AutonomousController(TaskQueue(queue_path), ControllerLimits(max_steps=1))
    assert first.run(crashing_worker) == 1

    # State survives the process boundary; the failed task is retryable.
    resumed_queue = TaskQueue(queue_path)
    build = next(t for t in resumed_queue.tasks if t.task_id == "build")
    assert build.status == "QUEUED"
    assert build.retry_count == 1

    # A replacement controller resumes and completes the mission queue.
    second = AutonomousController(resumed_queue, ControllerLimits(max_steps=5))
    assert second.run(crashing_worker) == 2

    final_queue = TaskQueue(queue_path)
    assert {t.task_id: t.status for t in final_queue.tasks} == {
        "build": "PASS",
        "verify": "PASS",
    }
    assert attempts == {"build": 2, "verify": 1}


def test_e2e_retry_budget_parks_instead_of_looping(tmp_path: Path):
    queue = TaskQueue(tmp_path / "tasks.json")
    queue.enqueue(Task("broken", "G2", "broken worker", max_retries=2))

    def always_crashes(task: Task):
        raise RuntimeError("persistent failure")

    controller = AutonomousController(queue, ControllerLimits(max_steps=10))
    assert controller.run(always_crashes) == 2

    final = TaskQueue(tmp_path / "tasks.json")
    task = final.tasks[0]
    assert task.status == "PARKED"
    assert task.retry_count == 2
