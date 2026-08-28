from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class SupervisorPolicy:
    max_cycles: int = 5
    max_wall_seconds: float = 300.0
    max_replans: int = 3


@dataclass(frozen=True)
class SupervisorResult(Generic[T]):
    status: str
    value: T | None
    cycles: int
    replans: int
    reason: str


class KillSwitch:
    def __init__(self) -> None:
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    @property
    def stopped(self) -> bool:
        return self._stopped


class Supervisor(Generic[T]):
    """Keeps executing until success, bounded failure, timeout, or explicit stop."""

    def __init__(self, policy: SupervisorPolicy | None = None, kill_switch: KillSwitch | None = None):
        self.policy = policy or SupervisorPolicy()
        self.kill_switch = kill_switch or KillSwitch()

    def run(
        self,
        step: Callable[[], tuple[bool, T | None]],
        replan: Callable[[int], None] | None = None,
    ) -> SupervisorResult[T]:
        started = monotonic()
        replans = 0
        for cycle in range(1, self.policy.max_cycles + 1):
            if self.kill_switch.stopped:
                return SupervisorResult("STOPPED", None, cycle - 1, replans, "kill switch")
            if monotonic() - started > self.policy.max_wall_seconds:
                return SupervisorResult("TIMEOUT", None, cycle - 1, replans, "wall-clock ceiling")
            ok, value = step()
            if ok:
                return SupervisorResult("SUCCESS", value, cycle, replans, "step accepted")
            if replan is None or replans >= self.policy.max_replans:
                continue
            replans += 1
            replan(replans)
        return SupervisorResult("EXHAUSTED", None, self.policy.max_cycles, replans, "cycle ceiling")
