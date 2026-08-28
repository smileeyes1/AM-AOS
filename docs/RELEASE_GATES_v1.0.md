# AM-AOS Release Gates v1.0

## G0 — Baseline
Reference definition, requirements, architecture, threat model, and contracts are versioned.

## G1 — Runtime
Mission/task lifecycle, authority enforcement, evidence, verification, recovery, audit, and regression are executable and tested.

## G2 — Persistence/API
State is durably persisted with transactional semantics; external API is authenticated/authorized and contract-tested.

## G3 — Hardening
Adversarial, failure-injection, security, integrity, replay, isolation, and resilience tests pass for the declared scope.

## G4 — Operations
Observability, health checks, configuration, backup/restore, deployment, rollback, and incident procedures are tested.

## G5 — Release Candidate
All mandatory gates pass; open risks are explicitly classified; release artifacts are reproducible.

## G6 — Production Readiness
Operational owner, deployment target, secrets, SLOs, backup policy, and rollback authority exist. This gate cannot be completed from code alone when external infrastructure approval is required.

## G7 — External Validation
Independent review/pilot evidence. This is separate from repository CI and is required for any claim stronger than the tested internal scope.

### Rule
A failed mandatory gate is `NO-GO`. A gate cannot be marked PASS from documentation alone.
