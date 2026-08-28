from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    claim: str
    scope: str
    test: str
    result: str
    artifact: str
    version: str
    timestamp: str
    sha256: str

class EvidenceLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, evidence_id: str, claim: str, scope: str, test: str,
               result: str, artifact: str, version: str) -> Evidence:
        payload = json.dumps({"evidence_id": evidence_id, "claim": claim,
            "scope": scope, "test": test, "result": result,
            "artifact": artifact, "version": version}, sort_keys=True).encode()
        item = Evidence(evidence_id, claim, scope, test, result, artifact, version,
                        datetime.now(timezone.utc).isoformat(), hashlib.sha256(payload).hexdigest())
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(item), sort_keys=True) + "\n")
        return item

    def verify(self) -> bool:
        if not self.path.exists():
            return True
        for line in self.path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            base = {k: item[k] for k in ("evidence_id", "claim", "scope", "test", "result", "artifact", "version")}
            expected = hashlib.sha256(json.dumps(base, sort_keys=True).encode()).hexdigest()
            if expected != item.get("sha256"):
                return False
        return True
