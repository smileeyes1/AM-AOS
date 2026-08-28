# AM-AOS Autonomous Mission Control v1.0

## Objective
AM-AOS shall continue mission execution from durable project state without depending on conversational memory. The chat session is an operator interface, not the system of record.

## Control loop

`LOAD → PLAN → AUTHORIZE → SCHEDULE → EXECUTE → OBSERVE → VERIFY → ATTACK → REPAIR/REPLAN → REGRESSION → GATE → RELEASE → DELIVERY → CONFIRM`

## Persistent truth

Git repository state, versioned project state, task state, gate records, evidence, audit records, and release artifacts are the authoritative engineering record.

## Autonomy boundary

Autonomous decisions: implementation, refactoring, test design, task ordering, retries, recovery, worker replacement, documentation, and other non-sovereign engineering decisions.

Human-only decisions: mission changes, constitutional constraint changes, authority-ceiling changes, legally required approvals, protected secrets, and explicitly destructive or irreversible production actions requiring human approval.

## Continuation guarantees

- Controller state is checkpointed before/after consequential transitions.
- Task IDs are idempotent.
- Retries are bounded.
- Failed work becomes repairable or parked rather than looping indefinitely.
- Independent tasks may continue while one task is blocked.
- Restart resumes from the last verified state.
- Unknown evidence never upgrades a claim to PASS.

## Release-to-user rule

Generated output is never automatically delivered merely because generation succeeded. Delivery requires a dedicated fail-closed Delivery Gate proving artifact existence, integrity, tests, security, evidence sufficiency, release approval, and destination authorization. Delivery confirmation is a separate state from transmission.

## Operational states

`RUNNING`, `VERIFYING`, `REPAIRING`, `BLOCKED`, `PARKED`, `RELEASE_CANDIDATE`, `RELEASED`, `DELIVERING`, `DELIVERED`, `FAILED`.

## Watchdog requirements

The deployed controller must expose a heartbeat and health state. A supervisor/runner must detect stale execution, restart safely, and preserve the last checkpoint. Restart must not bypass authorization or verification.

## Required external capabilities

An unattended controller that can modify repositories, call LLMs, deploy services, or deliver to an end user requires explicitly provisioned runtime credentials and an execution environment. The repository alone cannot manufacture those credentials. Missing capabilities are recorded as blockers; they are never fabricated.

## Assurance claim levels

`IMPLEMENTED → TESTED → VERIFIED → HARDENED → PRODUCTION-READY → INDEPENDENTLY-VALIDATED → GLOBALLY-PROVEN`.

A higher level requires evidence beyond the previous level; no level is inferred automatically.
