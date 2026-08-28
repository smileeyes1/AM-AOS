# AM-AOS Production Architecture

## Control plane
Mission contract is frozen before execution. Runtime owns authority ceilings, task lifecycle, evidence capture, verification, recovery and release decisions.

## Data plane
Agents/tools execute only through registered capabilities. External provider credentials and network access remain outside the assurance core and must be injected through deployment-specific adapters.

## Evidence plane
Evidence is content-addressed; audit events are hash chained. Evidence state cannot be escalated by assertion. Every release must retain mission, requirement, test, artifact, evidence, attack, decision and limitation records.

## Security boundaries
Tenant, identity, authority, tool, network and secret boundaries are explicit. Never place secrets in mission payloads, evidence, logs or source control. Production identity should use an external OIDC/SSO provider; the bundled local authenticator is for development and controlled pilots only.

## Availability/recovery
Use SQLite WAL for single-node controlled deployments; use managed PostgreSQL for multi-instance production. Backups must be encrypted, tested by restore drills, and versioned with release manifests. Rollback must restore both executable version and compatible schema.

## Observability
Emit structured events for mission start, authorization, tool invocation, evidence, verification, recovery, regression, release and incident. Monitor latency, error rate, denied authority, evidence gaps, verification disagreements and release-block rate.

## Non-go conditions
Critical security findings, broken audit chain, authority bypass, unverifiable evidence, failed migration rollback, failed backup restore, or unresolved release-gate regression block production release.
