# AM-AOS Continuous Execution Architecture v1.0

## Objective

Make project progress resumable and bounded without requiring the chat session to be the system of record.

## Components

- Project State: durable source of execution position.
- Task Queue: durable, idempotent, bounded retry queue.
- Autonomous Controller: deterministic orchestration loop with a hard step budget.
- Capability Guard: execution authorization boundary.
- Verifier/Gates: evidence-based acceptance.
- CI Worker: repeatable execution environment.

## Controller invariant

The controller may select and execute only queued work. It cannot mutate mission goals, constitutional constraints, or authority ceilings.

## Failure invariant

Worker exceptions become bounded task failure; exhausted retries are parked. The controller never retries indefinitely.

## Important limitation

This controller is an orchestration shell, not yet an autonomous coding worker. End-to-end unattended execution requires a worker adapter, sandbox, credentials policy, CI orchestration, and integration with the real Gate/Verification path. Those integrations must be tested before claiming continuous autonomous operation.
