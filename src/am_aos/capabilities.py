from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any

class CapabilityDenied(PermissionError): pass

@dataclass(frozen=True)
class Capability:
    name: str
    risk: str
    side_effects: bool = False

@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    tenant_id: str
    capabilities: frozenset[str]

@dataclass
class ToolResult:
    ok: bool
    value: Any = None
    error: str | None = None

class CapabilityGateway:
    def __init__(self, registry: dict[str, Capability] | None = None):
        self.registry = registry or {}
    def register(self, capability: Capability) -> None:
        if capability.name in self.registry:
            raise ValueError("capability already registered")
        self.registry[capability.name] = capability
    def authorize(self, identity: AgentIdentity, capability: str, tenant_id: str) -> None:
        if identity.tenant_id != tenant_id:
            raise CapabilityDenied("TENANT_BOUNDARY")
        if capability not in self.registry:
            raise CapabilityDenied("UNKNOWN_CAPABILITY")
        if capability not in identity.capabilities:
            raise CapabilityDenied("CAPABILITY_DENIED")
    def invoke(self, identity: AgentIdentity, capability: str, tenant_id: str, fn: Callable[..., Any], *args, **kwargs) -> ToolResult:
        self.authorize(identity, capability, tenant_id)
        try:
            return ToolResult(ok=True, value=fn(*args, **kwargs))
        except Exception as exc:
            return ToolResult(ok=False, error=type(exc).__name__)
