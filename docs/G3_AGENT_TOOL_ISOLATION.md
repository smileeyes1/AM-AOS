# G3 — Agent/Tool Isolation Gate

## Objective

Prevent an agent from gaining authority merely by knowing a tool exists. Every sensitive tool invocation must be authorized at the execution boundary by an explicit capability, resource, and action policy.

## Implemented

- Capability objects are immutable.
- Agent identities declare an explicit capability set.
- Authorization is default-deny.
- Unknown capabilities deny.
- Resource mismatch denies.
- Undeclared actions deny.

## Required before G3 PASS

- Integrate the capability guard into the real execution engine.
- Add authenticated identity propagation.
- Add tool registration and lifecycle controls.
- Add sandbox/isolation boundary for high-risk tools.
- Add replay/idempotency controls at tool execution.
- Add integration and failure-injection tests through the complete runtime path.
- Produce CI evidence for the complete G3 suite.

## Gate decision

**NOT READY / NO-GO** until the capability policy is enforced by the actual execution path and adversarial integration tests demonstrate denial at that boundary.
