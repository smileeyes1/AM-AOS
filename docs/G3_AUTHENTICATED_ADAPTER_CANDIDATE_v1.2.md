# AM-AOS G3 — Authenticated adapter candidate v1.2

Status: **TESTED LOCAL SCOPE / DRAFT / PRODUCTION NO-GO**

## Improvement over v1.1

The trusted registered-tool gateway now has an optional **token-verifying entrypoint**:

`SignedIdentityVerifier → AuthenticatedExecutionAdapter → TrustedExecutionGateway → registered handler`

ChatGPT message text, client-supplied `Principal`, or self-proclaimed role is never accepted at this new entrypoint. A token must be MAC-authenticated under a key provisioned to the verifier, and must be issued by an independently trusted service that authenticated the actor and restricted its capability list.

## Exact token contract

Version `amaos1`, canonical base64url JSON, HMAC-SHA256 covering the prefix and payload. Strict fixed claim schema: version, issuer, audience, subject, capability list, mission ID, mission goal SHA-256, tool ID, complete tool request fingerprint (arguments and idempotency key), pinned policy profile SHA-256, issue/not-before/expiry timestamps. The request may run only if all fields match trusted server-side mission and tool configuration. TTL is bounded (default max 300 seconds), expired or premature tokens deny; no automatic session creation.

**Key management:** a unique random secret (minimum 32 bytes) MUST be provisioned outside source control by the deployer; there is deliberately no production signing API, default key, static deploy key, or built-in identity provider. Test keys are test-only. Use protected secrets, TLS, audience-specific issuance and rotation; implement a key-ID or controlled key-rotation procedure before production.

## Tested claims

- 30 new isolated tests for correct token, missing/forged/wrong-key/tampered claims, wrong issuer/audience, strict types and duplicate keys, expiry/time bounds, exact request scope (including arguments and nonce), mission goal, authority ceilings, critical-action denial and durable replay refusal.
- 66 local tests across the new and prior sovereign/gateway suite passed (2026-10-13).
- The GitHub PR `#5` runs the repository regression suite in CI; the exact latest commit result must be verified before promoting the claim to `CI TESTED`.

## Explicit remaining risks

1. **Issuer does not yet exist as a deployed, trusted authentication service.** HMAC validation is not independent evidence that a real person or service was authenticated. A caller in possession of the key can mint tokens; protect and separate key material.
2. **Bypass paths remain.** The existing raw `SandboxWorker.execute` and Python process imports can invoke tools outside the adapter. The gateway is an assured interface only for calls routed through it, not universal enforcement. Do not expose raw worker entrypoints to untrusted callers.
3. **Not an OS sandbox.** The worker has Python subprocess capabilities without filesystem, network, syscall or resource isolation. Do not run untrusted code. A secure process/container boundary with testing is required.
4. **No external approval workflow** for high-impact changes; these remain denied. No production credentials, network endpoint, delegated personal accounts, automatic ChatGPT-wide interception, or user-device deployment.
5. **At-most-once is scoped** to one intact, protected journal and nonce; cross-host replication, backups, external immutable audit anchors, credential revocation, multi-key rotation and crash restoration are not yet proven.
6. **Tested code is not user acceptance.** `EXECUTED` does not mean artifact quality, delivery or mission impact.

## Mandatory release gate

Keep the PR in DRAFT and `main` untouched; G3 remains **NO-GO**. Next: implement a real authentication issuer/inbound transport in a separate protected service with secret handling, harden the true execution boundary, test adversarial isolation and crash/backup recovery, and prove no unmanaged bypass before production deployment.
