# OpenJarvis ↔ Sigma provider integration (Friday remains independent)

**Owner instruction 2026-11-11:** Reuse [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) to accelerate the shared intelligence layer, but **do not delay Friday's Samsung release**. Upstream is Apache-2.0 and currently describes itself as alpha. This is an opt-in, non-production integration; adding tests/docs does **not** install or run OpenJarvis.

## Existing usable contract

OpenJarvis publishes `POST /v1/chat/completions` in `src/openjarvis/server/routes.py`, protected by bearer-key `AuthMiddleware` when `OPENJARVIS_API_KEY` is set. Sigma already supports that wire format in `sigma_runtime.provider.HTTPModelProvider`, using a `chat-completions` protocol, so a second brain or new model-provider implementation is **not** needed.

For an approved **private staging** runtime, set the following only in the appropriate protected configuration stores (never in Git, APK or log):

| Sigma setting | Staging value/meaning |
| --- | --- |
| `SIGMA_RUNTIME_PROVIDER` | `http` |
| `SIGMA_LLM_PROTOCOL` | `chat-completions` |
| `SIGMA_LLM_ENDPOINT` | Private OpenJarvis loopback/allowlisted service `http://127.0.0.1:<port>/v1/chat/completions` (only if in same network namespace; otherwise authenticated private TLS) |
| `SIGMA_LLM_MODEL` | Exact model ID confirmed by the staged OpenJarvis `/v1/models` |
| `SIGMA_LLM_API_KEY` | Secret from OpenJarvis instance's `OPENJARVIS_API_KEY`; supply securely, never inline |

Set an explicit finite timeout. Do not configure an untrusted public `http://` host, or point `SIGMA_LLM_ENDPOINT` at arbitrary user input.

## Security and staging prerequisites

1. Pin and review the exact upstream Git commit and its transitive dependencies/SBOM; audit licence and advisories before running. **Do not execute the upstream `curl | bash` installer on production OVH/Leaseweb.**
2. Deploy to a separate unprivileged, resource-bounded **non-production** container, loopback/private ingress only, with per-service bearer authentication and **no real owner data, telephony secrets or production storage mounts**. Verify negative 401/403 coverage; the upstream keyless local mode must never be used on exposed interfaces.
3. Initially deny external tools, file/network/system access, autonomous agent scheduling and outbound messaging. Upstream's roadmap still lists operator capability-policy enforcement as a work item; default-deny sandboxing and independent review are mandatory.
4. Exercise the offline contract: `python -m unittest tests.test_sigma_openjarvis_contract -v`. Then repeat with a **real, staged OpenJarvis instance** using only synthetic prompts; record exact source commit, model, latency and 401/503/timeout outputs.
5. Compare the real model response time and quality with Sigma's existing provider. If worse/unavailable, disable the feature flag and return to the existing provider. No silent fallback of sensitive inputs to public cloud models.
6. Only after a separate authenticated, replay-protected, permissioned and audited Friday→Sigma contract is verified may Friday invoke Sigma agent capabilities. **No model keys in the Android app; no raw OpenJarvis admin API exposed to Friday.**

## Actual acceptance and release authority

OpenJarvis does not supply the required signed Kotlin/Samsung APK or production UK telephone voice journey. Those remain in `M17z2025/alisha-ai-platform` issue [#1169](https://github.com/M17z2025/alisha-ai-platform/issues/1169). Its [#1362](https://github.com/M17z2025/alisha-ai-platform/pull/1362) source branch remains separately gated by runtime ingress, backup/rollback, permanent signing and physical owner testing.

**Evidence levels:** offline wire test ≠ real OpenJarvis staged inference ≠ deployed Friday voice/inbox ≠ signed installed Samsung release ≠ physical end-to-end acceptance.

Tracked in [Sigma #159](https://github.com/M17z2025/ai-command-center/issues/159). Claude must produce actual test/commit/review evidence, not planning-only status.
