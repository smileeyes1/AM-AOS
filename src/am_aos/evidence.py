from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    task_id: str
    claim: str
    value: Any
    source: str
    sufficient: bool
    content_hash: str
    created_at: str


class EvidenceLedger:
    def __init__(self):
        self._records: dict[str, EvidenceRecord] = {}

    def append(self, evidence_id: str, task_id: str, claim: str, value: Any,
               source: str, sufficient: bool) -> EvidenceRecord:
        if evidence_id in self._records:
            raise ValueError("duplicate evidence id")
        record = EvidenceRecord(
            evidence_id=evidence_id,
            task_id=task_id,
            claim=claim,
            value=value,
            source=source,
            sufficient=bool(sufficient),
            content_hash=canonical_hash(value),
            created_at=utc_now(),
        )
        self._records[evidence_id] = record
        return record

    def get(self, evidence_id: str) -> EvidenceRecord:
        return self._records[evidence_id]

    def sufficient(self, evidence_ids: list[str]) -> bool:
        return bool(evidence_ids) and all(
            eid in self._records and self._records[eid].sufficient
            for eid in evidence_ids
        )

    def all(self) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records.values())
