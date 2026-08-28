from am_aos.task_queue import Task, TaskQueue


def test_running_task_is_requeued_after_process_restart(tmp_path):
    state = tmp_path / "queue.json"
    first = TaskQueue(state)
    first.enqueue(Task("recover-1", "G3", "crash recovery"))
    claimed = first.claim_next()
    assert claimed is not None
    assert claimed.status == "RUNNING"

    second = TaskQueue(state)
    recovered = second.claim_next()
    assert recovered is not None
    assert recovered.task_id == "recover-1"
    assert recovered.status == "RUNNING"
    assert recovered.retry_count == 0


def test_retry_budget_parks_instead_of_looping(tmp_path):
    state = tmp_path / "queue.json"
    queue = TaskQueue(state)
    queue.enqueue(Task("park-1", "G3", "bounded failure", max_retries=2))
    queue.claim_next()
    assert queue.fail_or_park("park-1") == "QUEUED"
    queue.claim_next()
    assert queue.fail_or_park("park-1") == "PARKED"
