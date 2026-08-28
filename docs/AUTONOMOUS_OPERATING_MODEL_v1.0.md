# AM-AOS Autonomous Operating Model v1.0

## Objective

Run the mission continuously without relying on a chat session as the execution engine. The repository and persistent runtime state are the engineering source of truth.

## Autonomous loop

1. Load immutable mission and current state.
2. Validate policy and authority ceiling.
3. Select only dependency-ready work.
4. Execute in an isolated worker.
5. Capture result and provenance.
6. Verify against the gate contract.
7. Attack the result where required.
8. On failure: diagnose, repair, targeted retest, adversarial retest, regression.
9. Record evidence and update durable state atomically.
10. Advance the gate only on sufficient evidence.
11. Produce a release candidate only after release criteria pass.
12. Run a separate delivery gate; generation never implies delivery.
13. Deliver only through an authorized adapter and record confirmation.

## Continuity

The chat is not a required state store. A durable state record must contain the current gate, completed/failed gates, blockers, last verified commit, last successful test, next action, and release status. Workers are disposable; state is durable.

## Failure policy

A failed worker is replaceable. A failed tool is isolated. An exhausted retry budget parks the task. A missing secret, mandatory human approval, legal decision, or sovereign authority change blocks only the affected path unless it invalidates a global safety condition.

## Completion semantics

`IMPLEMENTED` means code exists. `TESTED` means the defined automated test passed. `VERIFIED` means the claim has sufficient linked evidence. `HARDENED` requires adversarial coverage. `PRODUCTION-READY` requires all release gates and operational criteria. `INDEPENDENTLY-VALIDATED` requires an independent evaluator. `GLOBALLY-PROVEN` is never inferred from internal tests.

## Non-negotiable invariants

- Mission goal and constitutional constraints are immutable at runtime.
- Authority ceilings cannot be increased by an agent.
- Deny-by-default for capabilities.
- Unknown evidence is not success.
- Missing gate checks are not PASS.
- Delivery is fail-closed.
- Duplicate/replay of non-idempotent work is prevented by design.
- Every material claim has provenance.
- Every security or logic defect becomes a regression case.
- No release is declared from a green-looking dashboard without underlying evidence.
