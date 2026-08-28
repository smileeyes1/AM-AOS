from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
from datetime import datetime, timezone


class GateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NO_GO = "NO-GO"
    BLOCKED = "BLOCKED"
    NOT_READY = "NOT-READY"


@dataclass(frozen=True)
class ProjectState:
    current_gate: str
    status: GateStatus
    last_verified_commit: str | None
    last_successful_test: str | None
    next_action: str
    active_blockers: tuple[str, ...]
    release_status: str
    updated_at: str

    @classmethod
    def initial(cls, gate: str, next_action: str) -> "ProjectState":
        return cls(gate, GateStatus.NOT_READY, None, None, next_action, (), "NOT-RELEASED", _now())

    def to_dict(self) -> dict:
        return {
            "current_gate": self.current_gate,
            "status": self.status.value,
            "last_verified_commit": self.last_verified_commit,
            "last_successful_test": self.last_successful_test,
            "next_action": self.next_action,
            "active_blockers": list(self.active_blockers),
            "release_status": self.release_status,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectState":
        return cls(
            data["current_gate"], GateStatus(data["status"]), data.get("last_verified_commit"),
            data.get("last_successful_test"), data["next_action"], tuple(data.get("active_blockers", ())),
            data["release_status"], data["updated_at"],
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> ProjectState:
        return ProjectState.from_dict(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self, state: ProjectState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)
