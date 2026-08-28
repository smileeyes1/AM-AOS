# AM-AOS Claims Ledger v1.0

| Claim | Scope | Evidence required | Status |
|---|---|---|---|
| Authority boundary enforcement works | current automated runtime tests | passing authorization adversarial suite | TESTED |
| Evidence is required for PASS | current verification implementation | missing/insufficient evidence tests | TESTED |
| Audit integrity is protected | current audit implementation | tamper/integrity tests | TESTED/PARTIAL |
| System is production-ready | production deployment | G0-G6 evidence | UNPROVEN |
| System is secure | defined threat model | independent security testing + operational controls | UNPROVEN |
| System is globally proven | any universal scope | multi-environment independent evidence | UNPROVEN |

This ledger is normative: code, CI, and release documentation must not silently upgrade an UNPROVEN claim to PROVEN.
