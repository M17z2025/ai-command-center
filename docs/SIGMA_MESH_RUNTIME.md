# Sigma Operational Expert Mesh Runtime

## Status

This document describes the executable runtime introduced by issue #24. It turns the governed mesh under `headquarters/mesh/` into a working mission pipeline.

The runtime is **advisory by default**. It does not grant agents production deployment, financial, destructive, secret-management or repository-write authority.

## Execution path

```text
mission
  -> deterministic taxonomy routing
  -> leader selection
  -> Thinker/cognitive-lens selection
  -> bounded temporary specialists
  -> parallel expert inference
  -> independent critic
  -> evidence verifier
  -> bounded repair loop
  -> synthesis
  -> postmortem
  -> CANDIDATE lesson
```

Temporary specialists expire when the mission closes. Lessons are stored as `CANDIDATE`; the runtime cannot promote itself or rewrite production governance.

## Components

- `sigma_runtime/config.py` loads the mesh.
- `sigma_runtime/router.py` selects domains, leaders, Thinkers and bounded specialists.
- `sigma_runtime/provider.py` provides a vendor-neutral HTTP model adapter.
- `sigma_runtime/orchestrator.py` executes the multi-agent loop.
- `sigma_runtime/store.py` persists private mission/audit/lesson state to SQLite.
- `sigma_runtime/server.py` exposes an authenticated HTTP API.
- `scripts/sigma_mesh_runtime.py` exposes CLI, server and smoke commands.

## Model provider

Live execution fails closed unless a model endpoint is configured.

Environment variables:

```text
SIGMA_RUNTIME_PROVIDER=http
SIGMA_LLM_ENDPOINT=https://provider.example/v1/responses
SIGMA_LLM_MODEL=<model-id>
SIGMA_LLM_PROTOCOL=responses
SIGMA_LLM_API_KEY=<runtime secret, optional for trusted self-hosted endpoints>
SIGMA_LLM_TIMEOUT_SECONDS=120
```

`SIGMA_LLM_PROTOCOL` may be `responses` or `chat-completions`.

This makes the runtime usable with a self-hosted/OpenAI-compatible endpoint or a hosted provider without hard-coding one vendor.

No API key belongs in GitHub source, issues or logs.

## Private runtime storage

By default:

```text
runtime-data/sigma-runtime.db
```

The directory is gitignored. It may contain mission prompts and outputs and must be stored on a private encrypted host/volume appropriate to the mission data. This public repository must never receive the database.

Override with:

```text
SIGMA_RUNTIME_DB=/private/path/sigma-runtime.db
```

## CLI

Plan without calling a model:

```bash
python scripts/sigma_mesh_runtime.py plan "Design a secure medical records platform"
```

Run a real mission after configuring a provider:

```bash
python scripts/sigma_mesh_runtime.py run "Design a secure medical records platform"
```

Attach local evidence:

```bash
python scripts/sigma_mesh_runtime.py run "Review this proposal" \
  --evidence-file /private/evidence/regulation.txt \
  --evidence-file /private/evidence/technical-report.txt
```

Inspect durable state:

```bash
python scripts/sigma_mesh_runtime.py missions
python scripts/sigma_mesh_runtime.py mission <mission-id>
python scripts/sigma_mesh_runtime.py lessons
```

## HTTP API

For local-only use:

```bash
python scripts/sigma_mesh_runtime.py serve
```

For any non-loopback bind, `SIGMA_RUNTIME_TOKEN` is mandatory.

Endpoints:

- `GET /health`
- `GET /mesh`
- `GET /missions`
- `GET /missions/{id}`
- `POST /missions`
- `GET /lessons`

Example request:

```json
{
  "prompt": "Design a secure AI service",
  "evidence": [
    {"id": "policy-1", "source": "internal-policy", "content": "..."}
  ],
  "requested_by": "owner",
  "max_cycles": 2
}
```

## Evidence boundary

The Evidence Verifier validates the relationship between expert claims and **evidence supplied to the mission**. It must not fabricate citations or claim that current external facts were checked when they were not.

A separate governed research/search connector can later supply current evidence bundles. High-impact legal, medical, finance, political and security missions retain the risk gates in `pipeline.yaml`.

## CI smoke mode

The deterministic provider proves orchestration only; it is intentionally not an intelligence substitute:

```bash
SIGMA_RUNTIME_PROVIDER=test SIGMA_ALLOW_TEST_PROVIDER=1 \
python scripts/sigma_mesh_runtime.py --db /tmp/sigma-runtime.db smoke
```

A successful smoke proves routing, expert fan-out, critique, verification, repair, synthesis and persistence. It does not prove the quality of a live model provider.

## Development advisory planning

For prompts classified as material development missions, the runtime sets `development_planning_required=true` in the mission plan.

The router may select multiple prompt-specific permanent advisers for the same taxonomy domain (for example marketing + sales, or film direction + production + editing) when their routing keywords are materially present.

After parallel expert analysis, the runtime invokes the **Sigma Development Planning Director** to create a structured development advisory plan. The Independent Critic and Evidence Verifier receive that plan alongside the expert analyses. When repair occurs, the plan is regenerated from the repaired expert work.

The final plan is persisted as the mission artifact:

`development-advisory-plan`

and the mission event:

`development-advisory-plan`.

The plan follows `templates/SIGMA_DEVELOPMENT_ADVISORY_PLAN.md` and is intended to contain an ordered backlog/pull plan, acceptance criteria, evidence requirements, specialist ownership and exact next executable actions.

This runtime behavior does not claim that a plan is legally, financially or technically verified beyond the evidence and assurance stages actually completed.

## Algorithmic engineering solution tournament

For applicable software/technical development prompts, the router sets `algorithmic_engineering_required=true`.

The runtime can then persist:

- `algorithmic-solution-report` — formal problem, candidate approaches, comparison criteria, required test/benchmark evidence, selection/rejection rationale and unresolved uncertainty.
- `engineering-solution-judge` — independent Solution Judge review.

The runtime records the mission event `algorithmic-solution-search`. During repair cycles, the algorithmic report is regenerated from repaired expert work and the judge is rerun.

The model-backed runtime is not itself proof that code executed. It must not report tests, benchmarks or prototypes as run unless mission/repository evidence proves they ran. Interactive implementation agents and CI perform the actual repository code/test work; the runtime orchestrates and preserves the decision/evidence structure.

Correctness and mandatory security are hard gates. If no candidate satisfies the evidence requirements, Sigma must record the problem as unresolved and identify the next experiment.

## Engineering Rescue Mode

Prompts indicating broken/failing/regressed behavior set `rescue_mode_required=true`.

The runtime persists `engineering-rescue-report` and an `engineering-rescue-mode` event owned by `sigma-engineering-support-desk`.

The orchestration runtime deliberately does **not** convert a convincing proposed repair into a fixed status. Without supplied evidence of type `engineering-rescue-verification` and status `FIXED_VERIFIED`, a Rescue Mode mission remains `ACTIVE_WORKING`.

This protects the product truth boundary: repository implementation, CI, deployed preview/staging and applicable Sigma Full User Tester evidence are what prove a real defect is fixed. The orchestration layer structures the investigation and retains ownership/evidence; it does not fabricate execution.

A runtime error during Rescue Mode is persisted as `ACTIVE_WORKING_RUNTIME_ERROR`, not as a closed failed incident.

