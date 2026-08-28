import sys

import pytest

from am_aos.worker import SandboxWorker


def test_allowed_python_command_runs(tmp_path):
    result = SandboxWorker(tmp_path).execute([sys.executable, "-c", "print('ok')"])
    assert result.status == "PASS"
    assert result.return_code == 0
    assert result.stdout.strip() == "ok"


def test_disallowed_executable_is_denied(tmp_path):
    with pytest.raises(PermissionError):
        SandboxWorker(tmp_path).execute(["sh", "-c", "echo escaped"])


def test_timeout_fails_closed(tmp_path):
    result = SandboxWorker(tmp_path).execute([sys.executable, "-c", "import time; time.sleep(1)"])
    assert result.status == "FAIL"
    assert result.return_code is None
