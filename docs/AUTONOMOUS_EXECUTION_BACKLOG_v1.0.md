# AM-AOS Autonomous Execution Backlog v1.0

This backlog is ordered by dependency and assurance value. The controller must not declare a later gate complete while a prerequisite is unproven.

1. Worker runtime: lifecycle, timeout, cancellation, crash isolation, resource limits.
2. Sandbox/tool boundary: capability enforcement at the actual execution boundary.
3. Gate engine: machine-readable entry criteria, evidence requirements, PASS/NO-GO/BLOCKED transitions.
4. Evidence ledger: provenance, content hashes, verification records, immutable append semantics.
5. Audit: principal, action, resource, policy decision, result, correlation ID.
6. Authentication/RBAC: identity propagation and deny-by-default authorization.
7. Idempotency/replay: execution keys, stale-state protection, duplicate suppression.
8. Recovery/replanning: crash, network, tool, state and partial-execution recovery.
9. Observability: structured logs, metrics, health, traces, execution timeline.
10. CI/CD: build, tests, adversarial checks, evidence artifacts, release gating.
11. Backup/restore: tested backup, restore, integrity verification and resume.
12. Security hardening: threat model, dependency/supply-chain checks, secret isolation, abuse cases.
13. Release engineering: versioning, reproducible artifacts, rollback and migration strategy.
14. Delivery adapter: explicitly configured end-user destination, publish verification and rollback.
15. Chaos/adversarial campaign: repeated fault injection and regression capture.
16. Release Candidate gate.
17. Production Readiness gate.
18. Independent validation; only then may externally validated claims be made.

Global rule: a blocked item is parked with evidence while independent work continues. A security or authority failure is fail-closed and cannot be bypassed by the controller.
