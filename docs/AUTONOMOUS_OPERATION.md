# AM-AOS Autonomous Continuous Operation Contract

## Purpose

AM-AOS may operate continuously inside an explicit mission scope. Autonomy means selecting and executing the next permitted action without requiring a user prompt for every internal step. It does **not** permit changing constitutional constraints, mission authority ceilings, acceptance criteria, or external approval requirements.

## Control loop

`UNDERSTAND → EXTRACT → INTEGRITY → FREEZE → EVIDENCE PLAN → RISK → PLAN → EXECUTE → VERIFY → BREAK → REPAIR → REVERIFY → REGRESSION → EVIDENCE AUDIT → CLAIM-SCOPE → DECIDE → RELEASE`

The supervisor may repeat execution/replanning only within bounded cycle, retry, time, and authority ceilings.

## Automatic continuation

The controller continues automatically when:

- the next action is inside the frozen mission contract;
- the authority is already granted;
- the acceptance criterion is unchanged;
- the required evidence can be produced or inspected;
- no external approval is required;
- no unresolved critical blocker exists.

It stops when a boundary is reached, evidence is insufficient, an oracle is untrusted, a critical failure is detected, a kill switch is activated, or an external/sovereign decision is required.

## Direct end-user delivery

Direct delivery is a release operation, not a generation operation. The delivery gate requires:

1. an explicit claim;
2. a non-empty scope;
3. PASS or an explicitly authorized CONDITIONAL PASS;
4. artifact identity/digest;
5. a release decision already recorded by the assurance process;
6. no unresolved release blocker.

A failed, blocked, unproven, or unscoped artifact cannot be delivered as a successful result.

## Idempotency and recovery

Every mission, task, evidence item, audit event, and delivery receipt must have a stable identifier. Delivery receipts bind the mission, artifact digest, decision, and scope. Retries must not silently create a second logical release.

## Kill switch

An operator must be able to stop execution immediately. The kill switch is higher priority than automatic continuation and cannot be disabled by an agent or model.

## Human/sovereign boundary

The system must stop and surface the exact blocking decision when an action requires authority not present in the mission contract, an external legal/business approval, a change to constitutional constraints, a production credential, a domain-owner decision, or an independence claim that cannot be established by the available evidence.

## Evidence posture

The system must report the strongest defensible state only. Successful execution does not imply verification; verification does not imply independent verification; pilot evidence does not imply system-wide or universal assurance.

## Release posture

A release package must contain the mission identifier, artifact identifier/digest, requirement/acceptance references, test results, evidence references, attack coverage, limitations, decision, and scope. If any required field is absent, the release is blocked or not proven according to the decision-precedence rules.
