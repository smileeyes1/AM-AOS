# AM-AOS Autonomous Completion Control Specification v1.0

## Mission
Drive an authorized mission continuously from persisted state to verified completion or an explicit sovereign/human blocker, without relying on chat-session memory.

## Control invariants

1. Mission goal, constitutional constraints, authority ceiling, and mandatory human approvals are immutable to autonomous execution.
2. Every executable action has an identity, capability, policy decision, timeout, retry budget, and audit correlation ID.
3. Every material claim requires evidence: claim, scope, test/run, artifact, timestamp, version/commit, and verification result.
4. A release cannot be delivered unless release gates pass and the delivery destination is authorized.
5. Delivery is a separate state machine from release and requires post-delivery confirmation.
6. Unknown, missing, unverifiable, or tampered evidence fails closed.
7. Worker/tool failure may trigger bounded recovery and replanning; it never grants additional authority.
8. Repeated failure is parked, not looped indefinitely.
9. Autonomous execution may optimize strategy, sequencing, delegation, and implementation approach, but may not redefine the mission or safety boundaries.
10. Completion is terminal only after delivery confirmation, or an explicitly documented mission outcome that does not require delivery.

## State machine

`INIT → PLAN → AUTHORIZE → SCHEDULE → EXECUTE → OBSERVE → VERIFY → ADVERSARIAL → REGRESSION → GATE → RELEASE → DELIVERY_AUTH → DELIVER → CONFIRM → COMPLETE`

Failure transitions:

`EXECUTE/VERIFY/TEST → DIAGNOSE → REPAIR/REPLAN → RETEST`

Blocked transitions:

`ANY → BLOCKED_HUMAN | BLOCKED_EXTERNAL | PARKED`

## Autonomous continuation

A persistent supervisor must reload state after process restart, reconcile in-flight tasks, detect stale leases, recover only idempotent work automatically, and require explicit reconciliation for uncertain non-idempotent actions.

A watchdog monitors controller health. A scheduler continues independent ready tasks while a blocked task is parked.

## Delivery control

The delivery adapter is capability-scoped and destination-bound. It must not accept an arbitrary destination supplied by an agent. Before delivery, verify artifact digest, release identity, gate decision, evidence completeness, policy authorization, and destination allowlist. After delivery, record provider receipt/confirmation and verify the delivered artifact identity where the destination supports it.

## Stop conditions

Stop autonomous work only for: authority exhaustion, mandatory human approval, unavailable required external capability, safety violation, irrecoverable integrity failure, or exhausted bounded recovery with no safe alternative. Preserve resumable state and blocker evidence.

## Required evidence for final completion

- final mission state
- complete gate ledger
- test and adversarial results
- security findings and disposition
- artifact digests
- release metadata
- delivery authorization
- delivery receipt/confirmation
- known limitations
- last verified commit
- reproducible execution record

## Assurance status

This document defines the control contract. It does not itself prove that the full end-to-end runtime exists or has passed these conditions. Those claims remain UNPROVEN until executable evidence is produced.
