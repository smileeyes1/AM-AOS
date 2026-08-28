from __future__ import annotations
from dataclasses import dataclass
import time

class IdempotencyConflict(ValueError): pass

@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    operation: str
    result_digest: str
    created_at: float

class IdempotencyStore:
    def __init__(self): self._items: dict[tuple[str, str], IdempotencyRecord] = {}
    def get(self, operation: str, key: str) -> IdempotencyRecord | None:
        return self._items.get((operation, key))
    def put(self, operation: str, key: str, result_digest: str) -> IdempotencyRecord:
        existing = self.get(operation, key)
        if existing and existing.result_digest != result_digest:
            raise IdempotencyConflict("IDEMPOTENCY_KEY_REUSE")
        if existing: return existing
        record = IdempotencyRecord(key, operation, result_digest, time.time())
        self._items[(operation, key)] = record; return record
