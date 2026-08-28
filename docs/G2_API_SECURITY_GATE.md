# G2 — API / Security Boundary Gate

## Scope

This gate covers the first enterprise API boundary: health/readiness endpoints, explicit RBAC action authorization, transactional SQLite persistence for API audit/idempotency records, replay handling, and oversized payload rejection.

## Implemented controls

- Explicit role → action allow-list.
- Default deny for unknown roles/actions.
- Idempotency-Key required for mutating authorization requests.
- Request hash bound to idempotency key; reuse with different payload is rejected.
- Transactional persistence using SQLite WAL.
- API audit record for accepted authorization requests.
- Payload size ceiling.
- Health and readiness endpoints.

## Required next controls before production

- TLS at deployment boundary.
- Enterprise identity provider/OIDC.
- Signed/authenticated tokens with key rotation.
- Rate limiting and abuse controls.
- CSRF policy where cookie auth is used.
- Secret management.
- Database encryption/backup/restore drills.
- Network segmentation and tool/agent sandboxing.
- Dependency/SBOM scanning.
- DAST and external penetration testing.

## Gate status

`IMPLEMENTED — NOT YET PROVEN BY CI`

The gate cannot be promoted to PASS until CI executes the API adversarial suite successfully.
