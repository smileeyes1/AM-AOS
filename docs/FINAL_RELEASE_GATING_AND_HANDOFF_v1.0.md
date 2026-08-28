# AM-AOS Final Release, Handoff, and End-User Delivery Gate v1.0

## Release objective
A release is eligible only when the product is deployable for a declared scope, has passed its frozen acceptance gate, has auditable evidence, has no known critical defects preventing release, and the exact approved artifact is the one delivered.

## Gate sequence
G0 Constitutional Baseline
G1 Requirements and Acceptance Freeze
G2 Executable Platform Integrity
G3 Security / Identity / RBAC
G4 Agent and Tool Isolation
G5 Persistence / Recovery / Backup-Restore
G6 Observability / Operations / Incident Response
G7 Adversarial Assurance / False-Pass / Regression
G8 Independent Verification
G9 Real-Mission Pilot
G10 Production Qualification
G11 Release Candidate Approval
G12 Production Release
G13 Post-Release Assurance

## Mandatory release package
- immutable release identifier;
- source commit identifier;
- artifact digest(s);
- SBOM/dependency inventory;
- configuration contract with secret names only, never secret values;
- migration plan and rollback plan;
- test and adversarial evidence ledger;
- known limitations and residual-risk register;
- operational runbook;
- backup/restore evidence;
- monitoring and alert definitions;
- incident response procedure;
- release decision record;
- deployment receipt;
- post-release verification receipt.

## End-user delivery rule
No direct user delivery occurs from an unverified working tree, draft artifact, agent output, or mutable path.

The only allowed path is:
CANDIDATE -> CONTENT ADDRESS -> VERIFY -> RELEASE APPROVE -> QUEUE -> RECHECK IDENTITY -> DISPATCH -> RECEIPT -> POST-DELIVERY VERIFY.

If identity differs at any point: DELIVERY NO-GO.

## Automatic post-release verification
Immediately after deployment, the system verifies:
- health and readiness;
- expected version/release identifier;
- artifact digest;
- critical API paths;
- authentication boundary;
- persistence connectivity;
- audit/evidence write path;
- release-gate status;
- absence of critical startup errors.

Failure causes automatic containment according to rollback policy. Rollback must itself be auditable and must not destroy evidence from the failed release.

## Commercial boundary
A production deployment may be technically deployable while commercial readiness remains NOT PROVEN. Commercial release additionally requires any applicable contractual, legal, privacy, security, support, billing, data-processing, and customer acceptance controls.

## Claim language
Allowed examples:
- READY FOR RELEASE WITHIN DECLARED SCOPE.
- PROVEN WITHIN TESTED SCOPE.
- PRODUCTION QUALIFIED FOR DECLARED ENVIRONMENT.

Forbidden without matching evidence:
- universally safe;
- globally proven;
- failure-proof;
- autonomous without limits;
- production-ready for every environment.

## Gate ownership
Engineering may execute and repair. The system may make routine engineering decisions within authority. Sovereign mission changes, external independence, legal acceptance, customer acceptance, and unprovisioned production authority remain external decisions.
