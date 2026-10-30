# Sigma Free LLM Directory: controlled inference integration

## Source and decision (30 October 2026)

- Discovery source: https://github.com/open-free-llm-api/awesome-freellm-apis (MIT directory; not a gateway, a model host, or a provider contract).
- Registered with Sigma Scouter as **REVIEW**, not accepted as an unlimited free API.
- The directory describes hosted providers with quotas, sign-up requirements, variable terms and occasional credits. It does not turn a provider into an unlimited free or commercially guaranteed service.
- Existing Sigma **Ollama** and separate **FreeLLMAPI pilot** remain untouched as independent execution paths.
- Only reviewed OpenAI-compatible chat-completions endpoints are eligible for this experimental router. No repository-sourced URL is automatically trusted or executed.

## Operational boundaries

1. **Default OFF:** `SIGMA_FREE_LLM_ENABLED=0`. Existing primary provider is unchanged.
2. **Data minimisation:** a task is externally routed only if all conditions hold:
   - `request.kind` is `analysis` or `postmortem`;
   - `request.metadata["data_classification"] == "public"`;
   - `request.metadata["allow_free_tier"] is True`.
   Otherwise it uses the primary provider. No automatic inference that a prompt is safe to share.
3. **Endpoint allowlist:** HTTPS only; Groq, Cerebras, NVIDIA NIM and OpenRouter chat-completions paths only. These are integration candidates, **not claims of live availability**.
4. **No hardcoded secrets:** API keys are read from named `SIGMA_FREE_LLM_KEY_*` environment variables on the host and must never enter Git, URLs, logs or dashboards.
5. **Bounded demand:** every route has configured per-process RPM/RPD ceilings, a 60-second failure cooldown, max 60-second request timeout and no automatic unlimited retry. **Counters reset on process restart and are not shared among replicas**; these are protective limits, not provider-enforced or account-wide quotas. For scaled production, use a shared durable quota ledger.
6. **Costs:** primary-model fallback is disabled unless `SIGMA_FREE_LLM_ALLOW_PRIMARY_FALLBACK=1` is explicitly set. Keep off until primary cost and policy are understood. Never infer free-tier status from a model name alone.
7. **Assurance:** use existing primary for private prompts, engineering execution, critic/verifier, compliance, final synthesis and sensitive workflows. Vendor privacy, commercial-use rights, model licences and retention must be checked per provider before sending any real user/business material.

## Approved endpoint shapes (candidate list)

| Provider | Exact completions endpoint | Key environment name |
|---|---|---|
| Groq | `https://api.groq.com/openai/v1/chat/completions` | `SIGMA_FREE_LLM_KEY_GROQ` |
| Cerebras | `https://api.cerebras.ai/v1/chat/completions` | `SIGMA_FREE_LLM_KEY_CEREBRAS` |
| NVIDIA NIM | `https://integrate.api.nvidia.com/v1/chat/completions` | `SIGMA_FREE_LLM_KEY_NVIDIA` |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | `SIGMA_FREE_LLM_KEY_OPENROUTER` |

API keys and quotas must be checked in each provider's **own current dashboard/docs** before activation; the external directory is secondary evidence. A provider may withdraw models or change quotas without notice.

## Pilot setup (private server only; not committed populated values)

Use the existing `deploy/sigma-stack/.env` or secret manager, and configure:

```dotenv
SIGMA_FREE_LLM_ENABLED=1
SIGMA_FREE_LLM_KEY_GROQ=<from-provider-dashboard>
SIGMA_FREE_LLM_ROUTES_JSON=[{"name":"groq","endpoint":"https://api.groq.com/openai/v1/chat/completions","model":"llama-3.3-70b-versatile","key_env":"SIGMA_FREE_LLM_KEY_GROQ","max_requests_per_minute":2,"max_requests_per_day":50,"timeout_seconds":20}]
SIGMA_FREE_LLM_ALLOW_PRIMARY_FALLBACK=0
```

The model is an illustrative ID from the upstream directory, **not confirmed currently available on the owner's key**. Check the provider's live `/models` response/console and its terms first. This configuration permits at most 2 calls/min and 50/day *per running process*, for public/opted-in tasks only.

The host must allow HTTPS egress to the chosen provider. No ports need opening for inbound traffic.

### Verify

1. Run offline unit tests: `python -m unittest tests.test_sigma_free_tier` or the full suite through the existing Sigma mesh CI workflow.
2. With an **approved live key**, run `python scripts/sigma_free_llm_probe.py` inside the configured runtime environment. This sends a fixed, public synthetic string and refuses primary fallback.
3. Record provider, model, request result, context, observed limits and terms. Use explicit owner authority before any commercial/production prompt is routed externally.
4. For rollback, set `SIGMA_FREE_LLM_ENABLED=0` and restart the affected Sigma runtime/runner processes. This restores the existing model path without deleting Ollama data.

## Remaining verification gates

- No live API key or successful third-party model call is proved by a source commit or offline test.
- Live VPS/OVH deployment, reachable endpoint, commercial TOS/privacy review, independent security audit, replica-wide quota persistence and meaningful model quality benchmarking are **not yet verified**.
- Do not enable external inference for Friday, Winkday, customer data, legal/medical investigations or financial workflows by default.
- Do not replace Claude Code, local Ollama, or high-assurance reviewers with free, quota-limited services simply to reduce cost.
