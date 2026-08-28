# AM-AOS Enterprise Requirements Baseline v1.0

## Functional requirements

- Mission intake must produce a structured mission contract.
- Mission goals, constitutional constraints, and authority ceilings must be immutable at runtime.
- Tasks must declare required authority and verification policy.
- Agents must be registered with explicit capabilities/authorities.
- Authorization must be checked before execution.
- Execution must emit structured outcomes and evidence references.
- Verification must evaluate both outcome and evidence sufficiency.
- Failed execution or verification must enter a controlled failure path.
- Recovery/replanning must remain inside immutable mission boundaries.
- Regression gates must detect degradation of previously passing behavior.
- Material events must be auditable.
- Release gates must distinguish tested scope from proven scope.

## Non-functional requirements

- Deterministic policy enforcement for authority decisions.
- Append-oriented audit semantics.
- Explicit state transitions.
- Machine-readable evidence and claims.
- Testability of every safety/assurance invariant.
- Separation of control, execution, assurance, and audit concerns.
- Provider/model agnosticism at the control-plane boundary.

## Acceptance baseline

A release candidate must demonstrate automated tests for normal execution, unauthorized execution, insufficient evidence, execution failure, recovery, immutable-boundary violation, and regression failure. Production readiness additionally requires security, persistence, observability, deployment, backup/recovery, and operational testing beyond this baseline.
