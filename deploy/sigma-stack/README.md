# Sigma private live stack

This directory is the deployment pack for issue #25. The remaining commissioning inputs are an approved private host and runtime/provider credentials.

## Security defaults

- Sigma binds to `127.0.0.1` by default.
- The optional inference gateway is not published to the host in the pilot overlay.
- Runtime and gateway SQLite state use persistent named volumes.
- The populated `.env` is private host state and must never be committed.
- No repository-write, production, financial or secret-management capability is granted to Sigma by this stack.

## Option A — approved private OpenAI-compatible endpoint

Use an owned/private Ollama, vLLM, llama.cpp, internal gateway, or another explicitly approved endpoint.

```bash
cd deploy/sigma-stack
cp .env.example .env
chmod 600 .env
# populate SIGMA_RUNTIME_TOKEN and SIGMA_LLM_* in .env
docker compose up -d --build
```

Required values:
- `SIGMA_RUNTIME_TOKEN`
- `SIGMA_LLM_ENDPOINT`
- `SIGMA_LLM_MODEL`
- `SIGMA_LLM_API_KEY` only where the endpoint requires bearer auth.

## Option B — FreeLLMAPI development pilot

The optional overlay pins `ghcr.io/tashfeenahmed/freellmapi:v0.12.0`, the latest upstream release verified on 25 September 2026.

FreeLLMAPI is kept on the internal Docker network with no host `ports` mapping. Upstream describes its aggregated free-provider service as personal experimentation, so this overlay is for development/evaluation unless the actual chosen provider's commercial/data terms are separately verified.

Populate these values in the private `.env`:
- `FREELLMAPI_ENCRYPTION_KEY`
- `FREELLMAPI_UNIFIED_KEY`

Start the gateway and Sigma together after the gateway has approved provider credentials and a unified key:

```bash
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.freellm-pilot.yml \
  up -d --build
```

Sigma then uses:
- endpoint: `http://freellmapi:3001/v1/chat/completions`
- protocol: `chat-completions`
- model: `auto` by default.

Do not commit `.env`, provider keys, the unified key or database volumes.

## Commissioning verification

Run from the repository root after the service is live:

```bash
export SIGMA_RUNTIME_TOKEN='<private runtime token>'
python scripts/sigma_live_probe.py \
  --url http://127.0.0.1:8080 \
  --prompt "Design and verify a secure multi-tenant application."
```

The probe creates a **real model-backed mission**, then reads the persisted mission and verifies that routing, team formation, criticism, evidence verification and synthesis were recorded.

Restart Sigma and verify persistence:

```bash
docker compose restart sigma-runtime
python scripts/sigma_live_probe.py --url http://127.0.0.1:8080 --read <mission-id>
```

A successful read after restart proves the durable runtime volume retained mission state.

## Production boundary

For business production, use a model route whose commercial/data terms have been verified. The FreeLLMAPI overlay is replaceable; Sigma itself remains vendor-neutral.
## Option C — fully self-hosted Ollama + always-on Sigma runner

The Ollama overlay keeps inference on the private Docker network and publishes no Ollama port to the host. The overlay is pinned to Ollama `0.34.3`; re-verify upstream security and model licences before upgrades.

Choose an open-weight model whose licence and resource requirements are acceptable for the OVH/VPS, then set only its model identifier in the private host `.env`:

```bash
OLLAMA_MODEL=<approved-model>
SIGMA_RUNTIME_TOKEN=<private-random-token>
```

Start the private inference service, Sigma API, and runner:

```bash
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose.ollama.yml \
  up -d --build
```

The model-init service pulls the selected model once and Sigma uses Ollama's OpenAI-compatible endpoint internally:

`http://ollama:11434/v1/chat/completions`

No paid fallback exists in this overlay.

### Runner commissioning

The runner starts in planning-only/read-only mode:

```text
SIGMA_RUNNER_ALLOW_WRITE=0
SIGMA_RUNNER_EXECUTE=0
```

This is sufficient to scan the portfolio, select executable work and persist mesh-backed plans.

To allow real implementation dispatch later, provision a least-privilege GitHub runtime credential and a governed private worker service, then deliberately enable:

```text
SIGMA_GITHUB_TOKEN=<runtime secret>
SIGMA_WORKER_ENDPOINT=http://<private-worker>/missions
SIGMA_WORKER_TOKEN=<runtime secret if required>
SIGMA_RUNNER_ALLOW_WRITE=1
SIGMA_RUNNER_EXECUTE=1
```

A worker result is not accepted as a repository change unless it returns both branch and pull-request evidence. Independent CI/security/user-test gates remain mandatory.

### Verification

Inside the Sigma network, probe inference with:

```bash
python scripts/sigma_inference_probe.py
```

Probe the public-facing local Sigma API with:

```bash
python scripts/sigma_live_probe.py --url http://127.0.0.1:8080 \
  --prompt "Run a Sigma runtime commissioning verification mission."
```

Read runner state through the authenticated API:

```text
GET  /runner/cycles
POST /runner/cycle   {"trigger":"operator","execute":false}
```

A source-valid stack is not the same as a commissioned host. Live commissioning is proven only after a real model mission, service restart/persistence check, and at least one real runner cycle are evidenced on the private host.
