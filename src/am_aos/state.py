from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path

@dataclass
class MissionState:
    mission_id: str
    goal: str
    constitutional_constraints: tuple[str, ...]
    authority_ceiling: str
    current_gate: str
    status: str = "RUNNING"
    last_verified_commit: str | None = None
    last_successful_test: str | None = None
    next_action: str | None = None
    release_status: str = "NOT_READY"
    blocker: str | None = None

class StateStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: MissionState) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> MissionState:
        return MissionState(**json.loads(self.path.read_text(encoding="utf-8")))
