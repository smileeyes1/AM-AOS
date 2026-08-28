# AM-AOS — Adaptive Mission Assurance Operating System

**Enterprise Engineering Baseline v1.0**

AM-AOS is an evidence-governed control plane for mission execution across agents and tools. It enforces mission contracts, authority boundaries, verification gates, recovery/replanning, regression controls, and auditable evidence.

## Assurance status

- Architecture: DEFINED
- Enterprise baseline: INITIALIZED
- Production proof: NOT CLAIMED
- Global proof: NOT CLAIMED

## Operating law

`Plan → Authorize → Execute → Observe → Evidence → Verify → Recover/Replan → Regression → Release Gate`

No success claim is accepted without sufficient evidence. Immutable mission goals, constitutional constraints, and authority boundaries cannot be changed by runtime adaptation.

## Repository roadmap

- `docs/` — requirements, architecture, contracts, threat model, assurance claims
- `src/` — control plane and runtime components
- `tests/` — unit, integration, adversarial, failure-injection, regression
- `.github/workflows/` — CI assurance gates
- `schemas/` — mission, task, evidence, audit, policy schemas
- `deploy/` — deployment configuration

This repository is governed by the project operating contract and release gates. Passing tests establishes only the tested scope; it does not establish universal or global proof.
