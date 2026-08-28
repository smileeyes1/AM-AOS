from __future__ import annotations
from enum import Enum


class MissionState(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    RECOVERY = "RECOVERY"
    VERIFYING = "VERIFYING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NO_GO = "NO-GO"


_ALLOWED = {
    MissionState.DRAFT: {MissionState.READY, MissionState.NO_GO},
    MissionState.READY: {MissionState.RUNNING, MissionState.NO_GO},
    MissionState.RUNNING: {MissionState.VERIFYING, MissionState.RECOVERY, MissionState.FAILED, MissionState.BLOCKED, MissionState.NO_GO},
    MissionState.RECOVERY: {MissionState.RUNNING, MissionState.NO_GO, MissionState.FAILED},
    MissionState.VERIFYING: {MissionState.PASSED, MissionState.FAILED, MissionState.BLOCKED, MissionState.NO_GO},
    MissionState.PASSED: set(),
    MissionState.FAILED: {MissionState.RECOVERY, MissionState.NO_GO},
    MissionState.BLOCKED: {MissionState.RECOVERY, MissionState.NO_GO},
    MissionState.NO_GO: set(),
}


def transition(current: MissionState, target: MissionState) -> MissionState:
    if target not in _ALLOWED[current]:
        raise ValueError(f"Illegal mission transition: {current.value} -> {target.value}")
    return target
