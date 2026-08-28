# AM-AOS Enterprise Architecture v1.0

## Planes

1. **Control Plane** — mission contracts, task graph, policy evaluation, state transitions, orchestration.
2. **Execution Plane** — agents and tools behind explicit capability/authority adapters.
3. **Assurance Plane** — evidence collection, verification, failure classification, recovery, replanning, regression.
4. **Audit Plane** — append-oriented audit events, evidence digests, decision records.
5. **Operations Plane** — health, metrics, configuration, deployment, backup/recovery.

## Trust boundaries

- User/API → authenticated control plane
- Control plane → policy engine
- Policy engine → agent/tool adapters
- Execution output → evidence normalization
- Evidence → verification gate
- Runtime state → persistent store

No agent is trusted to redefine the mission contract. Tool access is capability-based and must be explicitly granted.

## Core invariants

- I1: runtime adaptation cannot mutate goal, constitutional constraints, or authority ceiling.
- I2: unauthorized actions are denied before execution.
- I3: PASS requires sufficient evidence.
- I4: material decisions/actions/evidence are auditable.
- I5: recovery cannot silently bypass verification.
- I6: regression failures block release.
- I7: assurance claims are scoped to their evidence; no automatic global-proof claim.

## Production evolution

Prototype runtime → persistent transactional store → authenticated API → policy/capability isolation → observability → deployment/HA → external validation.
