from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    labels: dict[str, str]
    timestamp: float

class Telemetry:
    def __init__(self):
        self.metrics: list[Metric] = []
    def observe(self, name: str, value: float, **labels: str) -> Metric:
        m = Metric(name, float(value), dict(sorted(labels.items())), time.time())
        self.metrics.append(m); return m
    def snapshot(self) -> list[dict]:
        return [asdict(m) for m in self.metrics]
    def jsonl(self) -> str:
        return "\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in self.snapshot())
