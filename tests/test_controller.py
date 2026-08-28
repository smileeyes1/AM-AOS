from am_aos.controller import AutonomousController, ControllerLimits
from am_aos.task_queue import Task, TaskQueue


def test_controller_executes_until_queue_empty(tmp_path):
    q = TaskQueue(tmp_path / "q.json")
    q.enqueue(Task("a", "G3", "a"))
    q.enqueue(Task("b", "G3", "b"))
    seen = []
    controller = AutonomousController(q)
    steps = controller.run(lambda task: seen.append(task.task_id) or "PASS")
    assert steps == 2
    assert seen == ["a", "b"]
    assert all(t.status == "PASS" for t in q.tasks)


def test_controller_bounds_execution(tmp_path):
    q = TaskQueue(tmp_path / "q.json")
    for i in range(10):
        q.enqueue(Task(str(i), "G3", str(i)))
    controller = AutonomousController(q, ControllerLimits(max_steps=3))
    assert controller.run(lambda task: "PASS") == 3


def test_controller_parks_after_worker_failure(tmp_path):
    q = TaskQueue(tmp_path / "q.json")
    q.enqueue(Task("a", "G3", "a", max_retries=1))
    controller = AutonomousController(q)
    assert controller.run(lambda task: (_ for _ in ()).throw(RuntimeError("boom"))) == 1
    assert q.tasks[0].status == "PARKED"
