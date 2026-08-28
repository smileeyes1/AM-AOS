# AM-AOS Final User Delivery Policy v1.0

## Principle
Generated output is not final output. Final output is a verified release artifact that has passed all applicable gates and is delivered only to an authorized destination.

## Delivery preconditions

All must be true:

- Mission scope is valid and unchanged.
- Artifact is bound to a specific version/commit and digest.
- Required functional and regression tests pass.
- Required adversarial/security tests pass.
- Evidence is complete and integrity-verified.
- Release gate is PASS.
- Destination is allowlisted and capability-authorized.
- No unresolved blocker invalidates the artifact.
- Any mandatory human approval is present.

## Delivery state machine

`READY → AUTHORIZED → TRANSMITTING → RECEIVED → INTEGRITY_CONFIRMED → DELIVERED`

Any failure becomes `DELIVERY_FAILED` and triggers bounded recovery; it never silently becomes success.

## Destination protection

Agents must not select or alter the final destination outside an explicit capability and policy. The delivery adapter validates destination identity before transmission.

## Post-delivery verification

Where technically possible, the system records provider acknowledgement and verifies that the delivered artifact corresponds to the release digest. If receipt cannot be verified, the delivery claim remains UNPROVEN.

## Safety

No automatic delivery of an artifact that is unknown, unverifiable, tampered, unauthorized, or outside the mission scope.
