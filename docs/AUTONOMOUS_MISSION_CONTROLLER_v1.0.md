# AM-AOS Autonomous Mission Controller v1.0

## Purpose
Turn the AM-AOS assurance workflow into a continuously self-directed, bounded operating process that advances toward the frozen mission without requiring a human to orchestrate routine engineering work.

## Core contract
The controller owns sequencing and routine engineering decisions. It never owns constitutional authority.

### Immutable inputs
- mission goal
- requirements
- acceptance criteria
- authority ceiling
- safety/security policy
- evidence burden
- release policy
- tenant boundary

### Autonomous decisions permitted
- task decomposition
- work ordering
- implementation strategy
- agent/tool selection within capability policy
- retry strategy
- diagnosis
- repair strategy
- test selection within the approved assurance budget
- bounded replanning
- checkpoint frequency

### Autonomous decisions forbidden
- changing mission intent
- weakening acceptance criteria
- increasing authority
- disabling safety/security controls
- declaring evidence sufficient when it is not
- declaring independence that does not exist
- approving an artifact outside the release policy
- bypassing a failed gate
- silently discarding contradictory evidence

## Continuous state machine

`INIT -> MISSION_LOCKED -> PLAN -> EXECUTE -> OBSERVE -> VERIFY -> ASSURANCE -> DECIDE`

From `DECIDE`:
- `PASS_WITHIN_SCOPE -> RELEASE_GATE`
- `FAIL -> DIAGNOSE -> REPAIR -> REVERIFY -> REGRESSION -> ASSURANCE`
- `NOT_PROVEN -> EVIDENCE_GAP -> REPLAN -> EXECUTE`
- `INCONCLUSIVE -> DIAGNOSE -> REPLAN -> EXECUTE`
- `BLOCKED -> ESCALATE_OR_STOP`
- `NO_GO -> STOP`
- `RELEASE -> DELIVERY_GATE`

## Continuation controller
Each run maintains:
- run_id
- mission_id
- current_gate
- current_state
- plan_digest
- policy_digest
- checkpoint_id
- attempt_count
- repair_count
- stagnation_signature
- evidence_state
- artifact_identity
- authority ceiling
- next_action
- terminal_reason when stopped

The controller continues automatically when the next action is safe, authorized, evidence-producing, and within budget.

## Anti-stagnation
A failure signature is formed from requirement, test, fault class, artifact identity, and relevant environment. Repeated equivalent failures trigger a mandatory strategy change. Persistent failure beyond the configured repair budget terminates the run rather than looping indefinitely.

## Progress invariant
A cycle is productive only if it produces at least one of:
1. requirement progress;
2. evidence improvement;
3. fault reduction;
4. uncertainty reduction;
5. release-gate progress;
6. a justified escalation.

Otherwise the controller marks the cycle low-yield and replans.

## Evidence preservation
Before any repair or destructive action, the controller records the current evidence ledger and artifact identity. New evidence is appended; old evidence is never rewritten to make a failed result appear successful.

## Exact-artifact delivery invariant
The artifact approved by the Release Gate is content-addressed. Immediately before dispatch, the Delivery Gate recomputes identity and requires an exact match. Any mismatch cancels delivery and creates an identity failure.

## Post-delivery assurance
A successful dispatch creates a delivery receipt. The controller then verifies that the delivered artifact identity equals the approved identity and records the result. A failed receipt or identity mismatch is an operational incident, not a silent success.

## Escalation protocol
The controller automatically creates an escalation record containing:
- blocker class
- exact missing authority/dependency
- evidence collected
- actions already attempted
- why autonomous continuation is unsafe or unauthorized
- smallest external decision required

After recording the escalation, the controller enters a terminal blocked state rather than repeatedly asking for the same permission.

## Restart/recovery
On restart, the controller loads the latest checkpoint, validates mission/policy/artifact/evidence identities, and resumes only if all invariants match. Otherwise it quarantines the checkpoint and stops.

## Definition of autonomous completion
Autonomous completion is reached only when:
- the frozen mission is satisfied;
- applicable requirements pass;
- evidence is sufficient and traceable;
- required attacks are covered;
- regressions pass;
- artifact identity is stable;
- release policy passes;
- delivery policy passes;
- post-delivery verification succeeds;
- no critical unresolved finding remains;
- the claim is limited to the demonstrated scope.

Otherwise the controller continues, replans, escalates, or stops according to the state machine.

## Non-negotiable principle
`CONTINUE BY DEFAULT WITHIN AUTHORITY; STOP BY DEFAULT AT AUTHORITY, SAFETY, EVIDENCE, IDENTITY, OR RELEASE BOUNDARIES.`
