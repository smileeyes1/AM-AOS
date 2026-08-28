from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import Sequence


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: int = 30
    allowed_executables: tuple[str, ...] = ("python",)


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    return_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float


class SandboxWorker:
    """Minimal fail-closed worker boundary for deterministic repository tasks."""

    def __init__(self, root: str | Path, policy: SandboxPolicy | None = None):
        self.root = Path(root).resolve()
        self.policy = policy or SandboxPolicy()
        self.root.mkdir(parents=True, exist_ok=True)

    def execute(self, argv: Sequence[str]) -> ExecutionResult:
        if not argv:
            raise ValueError("empty command")
        executable = Path(argv[0]).name
        if executable not in self.policy.allowed_executables:
            raise PermissionError(f"executable not allowed: {executable}")
        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(argv), cwd=self.root, capture_output=True, text=True,
                timeout=self.policy.timeout_seconds, check=False,
            )
            status = "PASS" if completed.returncode == 0 else "FAIL"
            return ExecutionResult(status, completed.returncode, completed.stdout, completed.stderr,
                                   time.monotonic() - started)
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult("FAIL", None, exc.stdout or "", exc.stderr or "",
                                   time.monotonic() - started)
