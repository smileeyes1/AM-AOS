# AM-AOS Autonomous Continuation Protocol v1.0

The project must remain resumable across chat sessions, tool failures, CI runs, and partial execution.

## Rules

1. Git is the engineering source of truth; conversation memory is not a required dependency.
2. `ProjectStateStore` persists the current gate, status, blockers, last verified commit/test, next action, and release state.
3. A tool failure blocks only the dependent branch unless a safe alternative does not exist.
4. Every blocked branch is recorded explicitly; blocked work is never reported as completed.
5. A completed gate requires machine-readable test evidence and an auditable decision.
6. Failed material controls trigger repair and regression; they cannot be bypassed by editing the gate status.
7. Human-only decisions remain `BLOCKED-BY-HUMAN` and never become implicit approvals.
8. Runtime adaptation may change execution strategy but cannot mutate mission goals, constitutional constraints, authority ceilings, or mandatory human approvals.

## Continuation state

The controller's persisted state is the handoff contract between execution windows. A new execution window should load state first, verify the last known evidence, and continue from `next_action` rather than restarting the project.
