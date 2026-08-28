# AM-AOS Autonomous Operations Contract

## Objective
AM-AOS may operate continuously toward a frozen mission goal, but autonomy is bounded by authority, scope, evidence, time, retries, and release gates.

## Autonomous loop
UNDERSTAND -> EXTRACT -> INTEGRITY -> FREEZE -> EVIDENCE PLAN -> RISK -> PLAN -> EXECUTE -> VERIFY -> BREAK -> REPAIR -> REVERIFY -> REGRESSION -> EVIDENCE AUDIT -> CLAIM-SCOPE -> DECIDE -> RELEASE.

## Continue conditions
The controller may continue or replan only when:
- the mission goal and authority ceiling remain unchanged;
- the next action is within the frozen scope;
- the evidence required for the action is available or explicitly obtainable;
- limits have not been exceeded;
- no critical unresolved finding exists.

## Stop conditions
Stop with a bounded decision when any of the following occurs:
- authority boundary violation;
- scope expansion request;
- acceptance criterion mutation;
- evidence insufficiency for a release-critical claim;
- invalid or untrusted oracle needed for judgment;
- critical artifact identity mismatch;
- regression failure;
- repair/cycle/time limit;
- kill switch activation.

## End-user delivery
End-user delivery is downstream of Release Gate. The delivery outbox accepts only PASS or CONDITIONAL PASS with a valid claim scope. Before sending, the artifact digest is recomputed and compared with the released digest. A changed artifact is blocked. A successful delivery is idempotent by delivery ID.

## Human/sovereign boundaries
Autonomy does not grant authority to change mission purpose, legal/commercial commitments, security policy, tenant boundaries, credential ownership, or constitutional controls. Such changes are escalation points.

## Assurance posture
The presence of an autonomous loop is not evidence of production readiness. Production, independent verification, system-wide assurance, and universal validity remain claims that require their own evidence.