from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Capability:
    name: str
    resource: str
    actions: FrozenSet[str]


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    capabilities: FrozenSet[str]


class CapabilityGuard:
    """Default-deny capability enforcement at the execution boundary."""

    def __init__(self, capabilities: list[Capability]):
        self._caps = {c.name: c for c in capabilities}

    def authorize(self, agent: AgentIdentity, capability: str, resource: str, action: str) -> bool:
        if capability not in agent.capabilities:
            return False
        cap = self._caps.get(capability)
        if cap is None or cap.resource != resource:
            return False
        return action in cap.actions
