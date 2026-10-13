# AM-AOS G3 — Trusted Execution Gate candidate v1.1

Status: **DRAFT / TESTED LOCAL SCOPE / NO-GO FOR PRODUCTION**

## Purpose
Enforce the independently stored AM-AOS policy **at a registered tool's execution path**, not merely in ChatGPT instructions or in a standalone policy checker. ChatGPT custom instructions may be absent without removing the profile from the repository. Unconnected native ChatGPT conversations are NOT controlled by this code.

## Execution sequence
1. Trusted adapter constructs immutable MissionContract from a user-approved goal/authority ceiling and a Principal from independently authenticated identity/grants; free-text chat content must not be accepted as credentials or proof of approval.
2. Register tools inside trusted process from an approved catalog. Each tool binds a stable ID, capability, operation, resource, action and handler. Conflicting capability-to-resource/action registrations are rejected.
3. For each ToolCall, deny missing/unknown principal or tool, invalid input, cross-mission requests, unknown/critical operation, absent capability, or authority beyond the mission ceiling.
4. Verify the persistent audit event chain; atomically reserve the idempotency token in SQLite **before** invoking any registered handler. An already used token (whether completed, failed, abandoned, or with different arguments) is BLOCKED. No automatic retries of side effects.
5. Invoke only the trusted registered handler and durably record completion or failure. A successful callback returns `EXECUTED`, never `PASS` or `MISSION_COMPLETE`. Verification, approval and delivery remain independent gates.
6. Any journal failure or audit-chain alteration blocks subsequent execution. The database must be explicitly provisioned by a trusted initializer; absence is not silently recovered by creating new replay history.

## Evidence mapping
| Invariant | Test(s) | Supported conclusion |
|---|---|---|
| Missing authenticated principal denies | `test_no_authenticated_principal_no_side_effect` | Trusted-gateway entry stops unassigned identity |
| Scope, mission, grants and critical operations | `test_unregistered_tool_cannot_execute`, `test_mission_mismatch_blocks_runner`, `test_principal_capability_is_required`, `test_mission_authority_ceiling_is_required`, `test_high_impact_tool_cannot_use_exec_path`, `test_conflicting_resource_scope_for_same_capability_refused` | Registered local tool path denies specified disallowed requests |
| Replay/crash resistance | `test_duplicate_nonce_not_replayed_across_gateway_restarts`, `test_changed_args_same_nonce_denied`, `test_crash_fails_without_auto_reexecution`, `test_abandoned_started_token_parked`, `test_parallel_same_token_executes_once` | At-most-once per nonce while durable journal is intact |
| Journal and audit integrity | `test_missing_journal_fails_closed`, `test_corrupt_journal_fails_closed`, `test_audit_tamper_prevents_future_effects` | Missing/corrupt/altered state prevents new execution |
| Real worker through gate | `test_gate_controls_actual_worker_subprocess_invocation` | A harmless Python subprocess is invoked only after gateway permission |
| Independent policy | `test_operates_without_chatgpt_custom_instructions` | Local execution does not read a ChatGPT-custom-instruction variable |

The test fixture uses temporary files and no external credentials, deployments or user data. Source workflow at `.github/workflows/assurance.yml` executes the entire pytest suite on pull requests; success is limited to that tested commit and job environment.

## Remaining blockers — MUST NOT claim G3 PASS
- Caller-supplied Python `Principal` is **not** cryptographically authenticated. A remote endpoint must verify identity and derive privileges from an external trusted identity provider, never from chat text or client-supplied role strings.
- The legacy `SandboxWorker` still directly exposes `execute()` to in-process callers. The new gateway protects only tools explicitly routed through it; production wiring must remove all bypass paths.
- A Python interpreter with filesystem access is **not an OS sandbox**. A working directory and a subprocess timeout cannot prevent access to sibling files, inherited secrets, network, or the host. Isolate untrusted code with a tested sandbox/container, restricted identity, filesystem and network policies.
- The SQLite hash chain is only tamper-evident against some edits: an attacker with unrestricted DB/repository access can rewrite data, reset history, or re-pin a policy hash. External authentication, signed versions, independent immutable evidence anchors, protected branch rules and backup/restore remain required.
- Full mission-to-tool authorization, approvals for high-impact actions, audit provenance, user-visible delivery, observability, hard failure recovery and production durability across hosts require separate end-to-end integration evidence.
- Per-event full-chain verification is intentionally simple and potentially expensive at scale. A scalable verified checkpoint strategy is required before sustained production use.
- `EXECUTED` means the handler returned successfully. It does not prove the requested output, truth, safety, classroom value, end-user delivery, or field impact.

## Release decision
**Keep PR in draft; do not merge or deploy.** Do not weaken the frozen AM-AOS reference definition or the existing `main` baseline. Next highest-value work: authenticate a real tool adapter and prove complete authority enforcement and isolation in the actual execution environment; run recovery and adversarial tests before G3 transition.
