# Hermes Agent — Sigma controlled pilot (30 October 2026)

**State: GitHub integration candidate, not deployed or validated on the live VPS.**
Upstream: https://github.com/NousResearch/hermes-agent (MIT).

## Role and boundary
Hermes is a subordinate worker, **never** the Sigma source of truth, security reviewer, release authority or evidence verifier. The existing OpenHands/Claude pipeline and Sigma PR/CI gates remain intact.

Implemented `sigma_runtime.workers.hermes.HermesWorkerAdapter`:
- opt-in, disabled until an isolated Hermes deployment has been independently verified;
- bounded Runs API dispatch with a durable `Idempotency-Key`, bounded polling and bearer authentication;
- refuses unverified sandbox, missing capability/filesystem scope, credentials, production release and nonzero spend;
- returns `PLANNED` candidate evidence only; GitHub commit/PR, CI and signed release still need independent confirmation;
- no browser-accessible API secrets, no untrusted upstream response bodies in errors, no embedded credentials.

## Required environment (secrets remain off GitHub)
Hermes itself requires an actual inference provider/model; a healthy HTTP server is **not** proof the agent works. Deploy a pinned stable Nous Research image with persistent `/opt/data`, a private ingress, `API_SERVER_ENABLED=true`, `API_SERVER_KEY`, and a configured model. Bind to `127.0.0.1` or a private network, not a public internet endpoint. Enable a verified execution sandbox before sending tasks.

Sigma deployment adapter wiring example:
```python
from sigma_runtime.workers.hermes import HermesWorkerAdapter, HermesWorkerConfig
adapter = HermesWorkerAdapter(HermesWorkerConfig(
    endpoint="https://YOUR-PRIVATE-HERMES-GATEWAY/v1",
    api_key=private_runtime_secret,
    enabled=True, sandbox_verified=True,
))
result = adapter.execute(restricted_mission)
assert result.status.value == "PLANNED"  # never proof of delivery
```

Sigma's normal model provider can separately consume Hermes using `SIGMA_LLM_PROTOCOL=chat_completions`, `SIGMA_LLM_ENDPOINT=<private Hermes /v1/chat/completions>`, and model `hermes-agent`; validate network reachability, provider readiness and cost separately.

## Acceptance tests before promotion
1. Hermes `/health/detailed` reports ready; actual authorised model chat completes with a real provider.
2. Restart preserves session/run state and idempotency identity.
3. An isolated agent cannot read host secrets or act outside a disposable scope.
4. Send an allowed sandbox task; record `run_id`, compare actual changed files against the declared scope.
5. Require GitHub PR, exact-head CI, independent security/evidence and release gate; do not infer success from the agent's text.
6. Run regression: `python -m unittest tests.test_sigma_hermes_worker -v`.

Deployment requires the existing separate host/network access and runtime credentials. Do **not** repurpose OVH Friday/Winkday containers or enable this on a public endpoint merely to demonstrate liveness.
