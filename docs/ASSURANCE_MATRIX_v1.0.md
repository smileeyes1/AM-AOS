# AM-AOS Assurance Matrix v1.0

| Reference requirement | Component | Invariant | Acceptance evidence | Failure test |
|---|---|---|---|---|
| Goal → executable tasks | Mission/Task engine | Every task belongs to a mission contract | Mission/task schema + tests | orphan task |
| Authority boundaries | Policy/Authority guard | Unauthorized action is denied | deny decision + audit event | unauthorized agent |
| Evidence sufficiency | Evidence/Verification | No sufficient evidence → no PASS | verification record | missing/invalid evidence |
| Continuous assurance loop | Orchestrator | Failure enters controlled path | state transition log | execution exception |
| Recovery/replanning | Recovery engine | Recovery cannot mutate immutable boundaries | boundary snapshot + test | goal/constraint mutation |
| Regression protection | Regression gate | Prior PASS cannot silently degrade | regression report | forced regression |
| Auditability | Audit ledger | Material events are recorded | audit record | dropped event |
| Claim scope | Assurance gate | Test success ≠ global proof | scoped claim report | overclaim attempt |

## Gate rule

Any untested invariant is `UNPROVEN`. Any failed material invariant is `NO-GO` until repaired and regression-tested.
