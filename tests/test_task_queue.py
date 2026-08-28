from am_aos.task_queue import Task, TaskQueue


def test_queue_persists_and_resumes(tmp_path):
    p = tmp_path / "queue.json"
    q = TaskQueue(p)
    q.enqueue(Task("t1", "G3", "integration"))
    t = q.claim_next()
    assert t is not None and t.status == "RUNNING"
    q2 = TaskQueue(p)
    assert q2.tasks[0].status == "RUNNING"


def test_duplicate_enqueue_is_idempotent(tmp_path):
    q = TaskQueue(tmp_path / "queue.json")
    task = Task("t1", "G3", "integration")
    q.enqueue(task)
    q.enqueue(task)
    assert len(q.tasks) == 1


def test_retries_eventually_park(tmp_path):
    q = TaskQueue(tmp_path / "queue.json")
    q.enqueue(Task("t1", "G3", "integration", max_retries=2))
    assert q.fail_or_park("t1") == "QUEUED"
    assert q.fail_or_park("t1") == "PARKED"
