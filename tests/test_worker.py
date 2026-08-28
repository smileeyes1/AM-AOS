from am_aos.worker import SandboxPolicy, SandboxWorker


def test_worker_executes_allowed_python(tmp_path):
    worker = SandboxWorker(tmp_path)
    result = worker.execute(("python", "-c", "print('ok')"))
    assert result.status == "PASS"
    assert result.return_code == 0
    assert result.stdout.strip() == "ok"


def test_worker_denies_unapproved_executable(tmp_path):
    worker = SandboxWorker(tmp_path)
    try:
        worker.execute(("sh", "-c", "echo unsafe"))
    except PermissionError:
        pass
    else:
        raise AssertionError("sandbox must fail closed")


def test_worker_times_out(tmp_path):
    worker = SandboxWorker(tmp_path, SandboxPolicy(timeout_seconds=1))
    result = worker.execute(("python", "-c", "import time; time.sleep(2)"))
    assert result.status == "FAIL"
    assert result.return_code is None
