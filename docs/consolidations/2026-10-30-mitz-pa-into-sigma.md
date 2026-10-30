# Sigma Mesh + Mitz PA — Canonical consolidation
**Owner directive: 30 October 2026, superseding earlier Decision 2.**

## One product intelligence and orchestration layer
Sigma Mesh is the **single owner of Mitz PA's brain, personal-assistant intelligence, project-scoped memory, action planning, cross-app integrations, approval policy, auditable task state and development orchestration**. Mitz PA is no longer an independent project, and those requirements are **not** owned by Friday.

```
Owner  →  Sigma Mesh + Mitz PA (intelligence / memory / tasks / approvals)
           ├── Sigma development runner and specialist agents
           ├── Google Mail / Calendar / Contacts (future permissioned connectors)
           ├── other approved business application tools (future scoped connectors)
           └── Friday AI (existing phone/voice/Android communications interface)
                    └── SIP / Asterisk / OpenAI Realtime and the trusted mobile path
```

**Friday remains its own voice and telephone application** with Kotlin/Compose, OVH VPS behind commissioned Cloudflare ingress, SIP/Asterisk, OpenAI Realtime, ElevenLabs where configured, Supabase authorisation, R2 and original Android signing gates. Friday can be an interface to Sigma for approved owner requests after a separate authenticated cross-service contract is implemented and tested. Sigma does not replace Friday's low-latency conversation, telephony or the Samsung app. No live Friday↔Sigma bridge is claimed.

## What is actually implemented in this PR
- Project register and Sigma Build Steward routes `Mitz PA`, `Jarvis`, `personal assistant`, `Sigma PA` to `M17z2025/ai-command-center`, not `alisha-ai-platform`.
- Historical Mitz PA assignments are marked **superseded** in the old Friday/Sigma documents; Mitz PA is no longer a separate intake project.
- `sigma_runtime/owner_pa.py`: bounded owner-personal-assistant role that uses the **existing** SigmaOrchestrator and MissionStore. It forces an audit identifier, rejects oversized inputs, and returns advisory outcome **with `action_executed: false`**.
- `scripts/sigma_owner_pa.py`: real local/private CLI entrypoint using existing Sigma model-provider configuration. Running without a commissioned model fails closed. This is a proof of the Sigma internal integration, not the launch of a consumer app or a privileged external automation gateway.
- Regression and negative tests: aliases, project ownership, no invented GitHub repo, prompt bounds, no direct action claims.

## Historical requirements retained (original Google Drive documents)
1. [Mitz PA master blueprint](https://docs.google.com/document/d/1s1Bjoj_BI7PcSeByVoRfxTh5esJENRO_vjB-lICselg/edit)
2. [Requirements & decision register](https://docs.google.com/document/d/1bFlIVebxByeNK4lTSCEO5kPV1kWLqpyYw_YRuQ0pPFA/edit)
3. [Delivery roadmap and acceptance tests](https://docs.google.com/document/d/1zjpFXhBSN9_OOqopeBKrSWRT3E74qZDOw7HycdIjtwY/edit)
4. [Architecture and technology record](https://docs.google.com/document/d/1FJSAfhbp31tFXAsCccLCsKPQGJq4oUEvi0AXVBvy8rY/edit)
5. [Build instructions](https://docs.google.com/document/d/1jq3kPIBW5E9tB1_a7zPPjg_f4H-uk15maEYLO7B1SOs/edit)

All original Mitz PA functional requirements remain in scope, with responsibilities deliberately separated:

| Legacy requirements | Canonical owner | Acceptance still required |
|---|---|---|
| R-001–R-008, R-030–R-035: conversation intelligence, confirmed/inferred memory, search, correction, deletion, per-project isolation | Sigma | Owner data model, privacy/RLS, persistence and negative isolation tests |
| R-040–R-045: Gmail, Calendar, Contacts, workflow actions, read/write scope, idempotency and approval | Sigma | Actual connected service action, bounded scopes, double-execution prevention and audit receipts |
| R-050–R-055, R-060–R-064: development command centre, specialist agents, state, task progress and security | Sigma | Actual GitHub/CI/deploy/user-test evidence and correct stalled/failed UI |
| R-070–R-078: owner identity, MFA, capability grants, device/session security and audit | Sigma policy; Friday protects its own endpoints and device | Both independent security boundaries and scope/replay/denial tests |
| R-010–R-024: phone-first interface, biometrics, natural UK female assistant, interruption, voice/SIP calls | Friday | Signed Android, device acceptance, approved origin, real SIP/voice tests |
| R-080–R-084: no fake status, simple interaction, explicit privilege gates, fallback | Both | Cross-service contract, fail-closed modes, real deployed journeys |

Legacy claims that React Native/Expo or Vercel must replace Friday's native Kotlin/VPS stack are superseded. Optional external memory and agent tools are candidates only, not installed services.

## Safe execution and security
The owner PA CLI remains advisory only. It never sends Gmail, calendar invites, WhatsApp messages, makes SIP/PSTN calls, purchases, financial transfers, or publishes applications, and never claims those actions were done. A full assistant requires:
- an actual authorised private Sigma inference runtime;
- protected owner identity and separate storage namespaces/encrypted backups;
- least-privilege connectors with verified scopes and approved action receipts;
- a narrow Friday↔Sigma gateway with auth, replay protection and consent/audit;
- feature acceptance and independent security and user verification.

Do not use the CLI for sensitive personal information until its private persistent storage and model-hosting policy are commissioned. No provider keys, tokens, real personal data or production URLs belong in this public repository.

## Running the new Sigma Mitz PA role (only after model configuration)
```bash
printf '%s' 'Summarise the current status of my projects' | \
  python scripts/sigma_owner_pa.py --stdin --db /private/sigma/runtime.db
```
Execution requires `SIGMA_RUNTIME_PROVIDER=http`, `SIGMA_LLM_ENDPOINT`, `SIGMA_LLM_MODEL` and any provider credential in the runtime secret store. The command uses the established expert mesh, audits into its existing mission store and returns `external_action_status: NOT_EXECUTED`.

## Acceptance boundaries
- CI proving this code/routing is a **source implementation test**, not proof of a live phone assistant.
- Original Friday release and security blockers remain in force.
- Next: create a Sigma-owned, evidence-gated implementation backlog; retain a separate Friday-owned SIP/mobile backlog. No new standalone Mitz PA app or platform.
