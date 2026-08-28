# AM-AOS Threat Model v1.0

## Assets

- Mission contracts
- Authority policies
- Evidence records
- Audit records
- Credentials/configuration
- Runtime state

## Primary threats

| Threat | Required control | Gate evidence |
|---|---|---|
| Authority escalation | deny-by-default capability policy | adversarial authorization tests |
| Mission mutation | immutable contract hash + boundary check | mutation tests |
| Evidence tampering | content digest + append-oriented persistence | tamper tests |
| Audit deletion/rewrite | append-only store + integrity chain | audit integrity tests |
| Replay/duplicate execution | idempotency key/state transition checks | replay tests |
| Tool compromise | sandbox/capability adapter | isolation tests |
| Prompt/agent manipulation | agent treated as untrusted executor | policy tests |
| Recovery abuse | recovery remains subject to authorization/verification | recovery abuse tests |
| Secret leakage | secret redaction + least privilege | secret scanning/tests |
| Supply-chain compromise | pinned/managed dependencies + CI security checks | dependency/security gate |

## Security principle

The LLM/agent layer is not the security boundary. Policy enforcement, authorization, state transitions, and evidence verification must remain in deterministic control-plane components.

## Current status

This is a threat-model baseline, not a security certification. Penetration testing, dependency scanning, sandbox validation, and production identity integration remain required before a production-security claim.
