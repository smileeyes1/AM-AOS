# AM-AOS Release Qualification Gate

A release is eligible only when every applicable control is evidenced.

| Gate | Required evidence | Current |
|---|---|---|
| G0 Requirements | frozen mission/acceptance records | PARTIAL |
| G1 Runtime | automated unit/integration tests | TESTED |
| G2 Security | threat model + independent security test | NOT PROVEN |
| G3 Evidence/Audit | integrity verification + replayable records | TESTED, LIMITED SCOPE |
| G4 Independent verification | independent verifier result | NOT PROVEN |
| G5 Real mission pilot | real external mission evidence | NOT PROVEN |
| G6 Operations | monitoring, backup restore, rollback drill | NOT PROVEN |
| G7 Commercial | docs, support, SLA, claims review | NOT PROVEN |

## Current decision

**NO-GO for unrestricted production/commercial release.**

The repository now has a stronger executable foundation and CI contract, but local automated tests cannot establish independent assurance, production security, customer-pilot evidence, or system-wide validity.

## Required next gate

G2/G4 combined: security challenge and independent verification in a separately controlled environment. The verifier must not use the primary runtime's decision as its oracle.

## Release invariant

`NO-GO` is sticky for critical findings until repair, reverification and regression evidence exist.
