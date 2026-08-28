# AM-AOS Autonomous Continuous Operations Contract v1.0

## Purpose
Define the bounded control loop that allows AM-AOS to continue operating toward a frozen mission without requiring a human to orchestrate routine engineering decisions, while preventing self-expansion of mission, authority, evidence scope, or release authority.

## Non-negotiable invariants
- Mission, requirements, acceptance criteria, authority ceilings, and release policy are immutable during a run unless an authorized external change is introduced.
- The controller may choose implementation, sequencing, retries, diagnosis, repair, and replanning within those bounds.
- No agent, model, tool, verifier, or delivery worker may grant itself additional authority.
- A failed gate blocks release; it does not mutate the criterion to obtain PASS.
- A changed artifact invalidates evidence tied to the previous artifact identity.
- Delivery is permitted only from a release-approved, content-addressed artifact.
- Uncertainty that prevents a trustworthy decision produces BLOCKED, INCONCLUSIVE, NOT PROVEN, or NO-GO according to the decision precedence.

## Continuous controller
The controller repeats the following bounded cycle until a terminal state:

UNDERSTAND -> EXTRACT -> INTEGRITY -> FREEZE -> EVIDENCE PLAN -> RISK -> PLAN -> EXECUTE -> VERIFY -> BREAK -> REPAIR -> REVERIFY -> REGRESSION -> EVIDENCE AUDIT -> INDEPENDENCE -> CLAIM-SCOPE -> DECIDE -> RELEASE

A cycle may terminate only as:
- RELEASED: all applicable release gates pass within declared scope.
- BLOCKED: an external dependency or unavailable authority is required.
- NO-GO: a critical failure or unresolved release blocker exists.
- NOT_PROVEN: evidence is insufficient for a required claim.
- INCONCLUSIVE: valid evaluation cannot determine the result.
- STOPPED: safety, budget, time, retry, or kill-switch boundary was reached.

## Autonomous decision hierarchy
1. Constitutional constraints and explicit user decisions.
2. Frozen mission and acceptance criteria.
3. Safety/security constraints.
4. Authority ceilings and capability policy.
5. Release gates.
6. Evidence sufficiency and claim scope.
7. Risk-weighted engineering optimization.
8. Cost/time optimization.

Lower levels may never override higher levels.

## Self-correction
For every failure:
DETECT -> CLASSIFY -> PRESERVE EVIDENCE -> REJECT INVALID RESULT -> DIAGNOSE -> PATCH -> VERIFY PATCH -> REVERIFY FAILED TEST -> REGRESSION -> REASSESS GATE.

A repair is not successful merely because the original test passes. The controller must also check affected invariants and previously passing critical tests.

## Self-replanning
Replanning is allowed when execution cannot satisfy the frozen requirements with the current plan. Replanning may change method, ordering, agent allocation, or tool choice. It may not change mission, acceptance criteria, authority ceiling, required evidence burden, or release policy.

## Evidence lifecycle
Every material result carries:
mission_id, requirement_id, claim_id, artifact_id, artifact_digest, test_id, method, expected, observed, validity, oracle_status, evidence_location, attack_status, independence, limitation, decision.

Evidence is invalidated when its artifact identity, criterion, environment, or material precondition changes.

## Delivery safety
Delivery is a separate state machine:

CANDIDATE -> VERIFIED -> RELEASE_APPROVED -> QUEUED -> DISPATCHED -> RECEIPTED

Any mutation, failed gate, revoked evidence, or identity mismatch moves the item out of the delivery path. The delivery worker must re-check identity and approval immediately before dispatch.

## Recovery
The controller must checkpoint before and after material state transitions. Recovery must validate checkpoint integrity, mission identity, policy version, artifact identity, and evidence references before resuming. Corrupt or incompatible state is quarantined and cannot be silently resumed.

## Observability
Every controller transition emits a structured event with correlation id, mission id, run id, state, actor, authority, timestamp, input digest, output digest, and decision. Sensitive payloads must not be logged in plaintext.

## Escalation boundary
The controller must stop and request external authorization only when the next safe action requires one of:
- new sovereign mission requirements;
- authority above the frozen ceiling;
- production credentials/secrets not provisioned by the authorized operator;
- legal/compliance acceptance;
- independent external verification;
- customer approval or real-world side effect;
- infrastructure ownership not delegated to the controller.

Routine engineering choices must not trigger escalation.

## Anti-stagnation
The controller tracks repeated plans, repeated failures, and low-yield cycles. If the same failure signature persists beyond the configured repair budget, it must stop rather than loop indefinitely. A new plan is mandatory after a configurable number of equivalent failed attempts.

## Stop-before-harm
The controller must fail closed on:
- authority ambiguity;
- release approval ambiguity;
- artifact identity mismatch;
- contradictory evidence;
- missing required verifier;
- invalid oracle required for the decision;
- broken audit/evidence integrity;
- safety or security policy violation.

## Final principle
Autonomy means autonomous execution and correction inside a fixed constitutional envelope. It does not mean autonomous authority expansion, autonomous claim inflation, autonomous policy mutation, or autonomous declaration of production readiness.
