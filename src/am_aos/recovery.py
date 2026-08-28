from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json


def _digest(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()

@dataclass(frozen=True)
class Checkpoint:
    mission_id: str
    sequence: int
    state: dict
    digest: str

class CheckpointStore:
    def __init__(self): self._items: dict[str, list[Checkpoint]] = {}
    def save(self, mission_id: str, state: dict) -> Checkpoint:
        seq = len(self._items.get(mission_id, [])) + 1
        cp = Checkpoint(mission_id, seq, dict(state), _digest(state))
        self._items.setdefault(mission_id, []).append(cp); return cp
    def latest(self, mission_id: str) -> Checkpoint | None:
        items = self._items.get(mission_id, []); return items[-1] if items else None
    def verify(self, checkpoint: Checkpoint) -> bool:
        return checkpoint.digest == _digest(checkpoint.state)
    def restore(self, mission_id: str) -> dict | None:
        cp = self.latest(mission_id)
        if cp is None or not self.verify(cp): return None
        return dict(cp.state)
