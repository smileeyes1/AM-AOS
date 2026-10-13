# AM-AOS independent control / ChatGPT interface — candidate v1.0

## Decision
The AM-AOS repository and its reviewed, version-pinned mission profiles are the system of record. ChatGPT, a phone client, scheduled CI, or any other model can serve as an interface or executor. **The ChatGPT custom-instructions field is not an authority store.**

## Invariants
- Goals and authority ceilings originate from the user and cannot be enlarged by agent adaptation.
- An actual trusted execution adapter must verify actor identity, capability, action, resource, mission and explicit high-impact approvals before performing effects.
- Missing or untrusted policy, approval, evidence, worker isolation, or state yields `NO-GO` for the affected operation.
- The last proved successful baseline cannot silently be replaced.
- A task outcome, test pass, artifact delivery and verified user impact are different claims.
- A public source repository must not contain user-specific personal or school/student data or credentials.

## Components and trust boundaries
1. **Reference (frozen):** `docs/REFERENCE_DEFINITION_v1.0.md` stays unchanged.
2. **Versioned control profile:** `control/sovereign-profile-v1.json` (non-sensitive generic governance only), pinned by hash in `src/am_aos/sovereign_control.py`.
3. **Deterministic local decision gate:** the Python module refuses operations beyond immutable mission ceiling and independently provisioned principal permissions. High-impact changes always deny pending an authenticated approval mechanism.
4. **Real execution gate (not wired here):** authenticate principals, register tools, enforce per-resource capabilities, isolate untrusted execution and record audit/evidence before doing actual work. Until that is proven G3 remains NO-GO.
5. **ChatGPT project context:** optional short instructions and source link help ChatGPT consult the system; deleting global custom instructions does not delete external governance, but unconnected ChatGPT chats are NOT thereby governed by it.
6. **Independent runner:** scheduler, durable work queue, supervised worker, authenticated integrations, checked output and retries. GitHub scheduled CI currently checks a code/test subset only, not end-user continuous autonomy.

## Minimal ChatGPT project instructions (optional, not sufficient for enforcement)
> استخدم مرجع AM-AOS الموثق والنسخة المعتمدة من حاكمية حكيم عند توفرهما. افصل بين الطلب والنظام الحاكم. اعمل ضمن صلاحياتي المثبتة، واستعد آخر حالة متحققة. عند غياب المرجع أو الاتصال أو الأدلة لا تفترضها؛ اذكر المانع. لا تعتمد إلا نتائج مُختبرة، ولا تغيّر مقصدي أو صلاحياتي أو النجاح المثبت دون إذن.

## Verification matrix
| Requirement | Proof here | Not yet proven |
|---|---|---|
| Policy lives outside ChatGPT global custom instructions | profile and isolated tests | forced application to unrelated native ChatGPT chats |
| Profile identity | pinned SHA-256 and tamper test | signed ownership against a compromised repo administrator |
| Immutable per-mission goal/ceiling | frozen dataclass and effective-grants check | authenticated mission origin and real external effect boundary |
| Risky changes default deny | six explicit negative tests | external approval workflow |
| Release incomplete-evidence deny | completeness check | provenance/authenticity of evidence |
| Safe continuous operation | not in this PR | isolated worker, restart, watchdog, credentials and operating environment |

## Release decision
**PROTOTYPE / CANDIDATE only**. Do not merge or announce G3 PASS / production readiness until actual authenticated worker/tool integration and an independent regression/security campaign succeed. This change deliberately preserves the `main` baseline.
