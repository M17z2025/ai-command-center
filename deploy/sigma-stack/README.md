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
