# AM-AOS Autonomous Delivery Contract v1.0

## Objective

Enable AM-AOS to progress from a durable project state toward a validated release without requiring conversational continuation, while preserving hard authority and safety gates.

## Control loop

`LOAD → PLAN → AUTHORIZE → EXECUTE → VERIFY → RECORD EVIDENCE → GATE → RELEASE/PARK → RESUME`

## Autonomous decisions

The controller may choose implementation details, task ordering, retries, test strategy, refactoring, and non-destructive operational actions inside the frozen mission and authority ceiling.

## Mandatory human gates

The controller must park and request human action for secrets, account authorization, legal/financial decisions, mission changes, authority-ceiling changes, destructive production operations, or any policy exception.

## Delivery rule

No artifact is delivered to an end user merely because it was generated. Delivery requires a successful release gate, artifact integrity verification, configured destination, and a non-destructive delivery action permitted by policy.

## Release progression

`DEV → VERIFIED → RELEASE_CANDIDATE → PRODUCTION_READY → PUBLISHED`

`PUBLISHED` is prohibited unless all required release evidence exists.

## Continuity

The durable project state and task queue are the source of resumption. A worker crash, process restart, or temporary tool failure must not erase state or silently widen authority.

## Current status

This contract defines the target operating model. End-to-end unattended execution and automatic end-user delivery remain **UNPROVEN** until a real worker runtime, gate engine, delivery adapter, and failure/recovery integration tests demonstrate them.
