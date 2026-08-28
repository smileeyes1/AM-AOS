# AM-AOS Autonomous Release Pipeline v1.0

## Mission
Provide one bounded pipeline that can take a declared mission from intake to end-user delivery without routine human orchestration, while fail-closing on every condition that requires authority, trustworthy evidence, or an external decision.

## Pipeline

`INTAKE -> NORMALIZE -> INTEGRITY -> FREEZE -> RISK -> PLAN -> EXECUTE -> VERIFY -> ATTACK -> REPAIR -> REVERIFY -> REGRESSION -> EVIDENCE AUDIT -> CLAIM AUDIT -> RELEASE GATE -> DELIVERY GATE -> DISPATCH -> RECEIPT -> POST-DELIVERY VERIFY -> CLOSE`

The loop returns to PLAN automatically after recoverable failures and evidence gaps. It does not return to EXECUTE after a terminal blocker.

## Autonomous loop rules
1. Select the highest-value safe next action.
2. Execute only within the authority ceiling.
3. Require observable evidence for every material transition.
4. Detect stagnation and force strategy change.
5. Preserve failed evidence before repair.
6. Never mutate the acceptance criterion to obtain PASS.
7. Never broaden the claim to compensate for incomplete evidence.
8. Recompute artifact identity after material changes.
9. Require regression after every repair.
10. Stop on unresolved critical failure.

## Release-to-delivery invariant
`RELEASE_APPROVED` is necessary but not sufficient for dispatch. Dispatch additionally requires:
- approved artifact identity;
- unchanged artifact digest;
- active approval;
- delivery destination authorized for the mission;
- no revoked evidence;
- no new critical incident;
- idempotency key accepted;
- audit event emitted.

## Delivery failure handling
- identity mismatch -> cancel dispatch + NO-GO/incident
- revoked approval -> cancel dispatch + BLOCKED
- duplicate idempotency key -> return prior receipt; never duplicate side effect
- transient transport failure -> bounded retry
- persistent transport failure -> BLOCKED with evidence
- post-delivery identity mismatch -> incident + quarantine + BLOCKED

## End-user boundary
The end user receives only an artifact that passed the Release Gate and the immediate pre-dispatch identity check. The user-facing channel must not expose internal secrets, hidden chain-of-thought, credentials, or unverifiable claims.

## Operational memory
The controller persists machine-readable mission state, evidence records, decisions, incidents, and delivery receipts. Restart recovery is deterministic from the latest valid checkpoint.

## Human boundary
Human interaction is required only for a genuinely external or sovereign decision, such as new mission authority, production credentials, legal acceptance, customer approval, infrastructure ownership, or independent verification. Routine engineering choices are autonomous.

## Completion semantics
`CLOSED` means the mission reached a terminal, evidenced state. It does not necessarily mean success. Success is represented explicitly as `RELEASED_WITHIN_SCOPE` and requires the complete release and delivery chain.

## Safety property
No component may transform `BLOCKED`, `NOT_PROVEN`, `INCONCLUSIVE`, `NO_GO`, or `STOPPED` into `RELEASED_WITHIN_SCOPE` without a new evidence-producing transition that satisfies the applicable gate.
