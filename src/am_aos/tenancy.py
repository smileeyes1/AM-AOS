from __future__ import annotations
from dataclasses import dataclass

class TenantBoundaryError(PermissionError): pass

@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    principal_id: str

class TenantGuard:
    @staticmethod
    def require(context: TenantContext, resource_tenant_id: str) -> None:
        if not context.tenant_id or context.tenant_id != resource_tenant_id:
            raise TenantBoundaryError("TENANT_BOUNDARY")
