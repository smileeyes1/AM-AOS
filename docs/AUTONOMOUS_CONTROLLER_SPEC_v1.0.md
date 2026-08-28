# AM-AOS Autonomous Controller Specification v1.0

## Purpose

Provide durable, resumable orchestration without making the chat session the system of record.

## Control loop

`Load State → Select Task → Authorize → Execute → Collect Evidence → Verify → Update State → Gate → Enqueue Next/Repair`

## Safety invariants

- No task executes without an explicit authority decision.
- Duplicate task IDs are idempotently rejected by the queue.
- Retries are bounded; exhausted work becomes `PARKED` rather than looping forever.
- State is persisted atomically.
- A blocked tool does not authorize a different action.
- A controller cannot mutate mission goals, constitutional constraints, or authority ceilings.
- A PASS requires evidence produced by the defined verification path.

## Failure handling

`FAIL → bounded retry → PARKED` when the retry budget is exhausted.

Independent tasks remain eligible while one task is blocked.

## Current implementation boundary

The durable task queue is implemented and unit-tested. Full controller integration with the execution engine, gate engine, CI worker, and external worker runtime remains required before autonomous continuation can be declared proven.

## Assurance status

**IMPLEMENTED:** queue persistence, duplicate suppression, bounded retry/parking.

**UNPROVEN:** end-to-end autonomous continuation across process/runner failure.
