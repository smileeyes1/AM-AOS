# AM-AOS Autonomous Project Operating Model v1.0

## Objective
Make the repository, not the chat, the durable system of record for autonomous engineering progress.

## Required durable records

`MISSION.md` — immutable mission and constitutional boundaries.

`PROJECT_STATE.json` — current gate, active tasks, blockers, last verified commit, last successful run, next action, release state.

`DECISIONS/` — non-sovereign engineering decisions with rationale and evidence.

`EVIDENCE/` — machine-readable claim/test/artifact/provenance records.

`GATES/` — entry/exit criteria and immutable gate decisions.

`BLOCKERS/` — external/human blockers with resume conditions.

`RELEASES/` — release manifests, digests, notes, and rollback references.

## Autonomous loop

1. Load and integrity-check project state.
2. Reconcile stale/in-flight work.
3. Select the highest-value authorized ready task.
4. Create an execution lease.
5. Execute inside the permitted worker boundary.
6. Collect artifacts and evidence.
7. Run verification and adversarial checks.
8. On failure, diagnose, repair, and retest within bounded budgets.
9. Run regression before changing gate state.
10. Record an immutable gate decision.
11. Schedule the next ready work or park the blocker.
12. Build a release candidate only after release criteria pass.
13. Run delivery authorization checks.
14. Deliver only through an authorized destination adapter.
15. Confirm receipt/integrity and record completion evidence.

## Anti-stall rules

- Never wait on chat input for an engineering decision that is already within authority.
- Never retry indefinitely.
- Never treat a missing tool as successful execution.
- Never skip a failed gate to reach a later gate.
- Never delete failure evidence to make a gate pass.
- Never mark completion from intent; completion requires evidence.

## External boundary

If credentials, human approval, legal/financial/security sovereignty, or an unavailable external service is required, create a blocker with an exact resume condition and continue all independent authorized work.

## Current status

This operating model is a target control specification. The repository must separately prove each implementation claim through executable tests and artifacts.
