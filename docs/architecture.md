# Sigma Command Center Architecture

## Purpose and boundary

The Sigma Development Command Center is a GitHub-hosted engineering control plane. It coordinates repository contracts, portfolio status, development rules, security baselines, handoffs and verification policy across managed Mi7z/Lycia products.

It is **not** a product runtime and does not contain managed-product application source code.

## Source-of-truth layers

### Portfolio truth

- `projects/registry.yaml`
- command-center governance documents under `docs/`
- command-center issues, pull requests and commits

### Product truth

Each managed product remains authoritative for its own:

- source code;
- `.sigma/project.yaml`;
- `PROJECT_STATUS.md`;
- issues and pull requests;
- migrations and infrastructure configuration;
- CI/test evidence.

A product's repository evidence must be inspected before development or readiness claims are made.

## Core components

### Registry

`projects/registry.yaml` maps product names to exact GitHub repositories, lifecycle and category.

### Repository contract

`schemas/project-manifest.schema.json`, `templates/project.yaml` and `docs/PROJECT_REPOSITORY_CONTRACT.md` define the minimum discoverable contract expected from managed repositories.

### Governance and execution rules

- `AGENTS.md`
- `docs/OPERATING_MODEL.md`
- `docs/DEVELOPMENT_LOOP.md`
- `docs/CHATGPT_HANDOFF.md`
- `docs/SECURITY_BASELINE.md`
- `docs/DEFINITION_OF_DONE.md`
- `docs/SIGMA_REVIEW_PROTOCOL.md`

These define authority ordering, work selection, implementation, review, security and completion rules.

### Universal expert mesh

`headquarters/mesh/` defines Sigma's application-level Mixture-of-Experts architecture:
- hierarchical human-knowledge taxonomy;
- permanent domain leaders;
- bounded temporary specialist-team creation;
- multi-domain mission routing;
- independent critic and evidence verifier roles;
- synthesis and action gates;
- evidence/freshness policy;
- controlled, versioned evolution.

The mesh governance is consumed by the operational runtime in `sigma_runtime/`. Unknown domains fail over to Research Director plus nearest leaders rather than being answered by an invented permanent specialist.

### Operational expert-mesh runtime

The runtime provides:
- deterministic taxonomy/leader routing;
- Thinker/cognitive-lens selection;
- bounded temporary specialist creation;
- parallel model-backed expert analysis;
- independent critic and evidence verifier stages;
- bounded repair loops;
- final synthesis with unresolved uncertainty preserved;
- SQLite persistence for private mission, audit, artifact and candidate-learning state;
- authenticated HTTP API plus CLI;
- a vendor-neutral HTTP model adapter supporting Responses and chat-completions response shapes;
- deterministic CI smoke execution that proves orchestration without pretending to be a live intelligence provider.

The public Git repository stores code/configuration only. Mission databases and private payloads belong on a private runtime host/volume and are excluded from Git. The runtime is advisory by default and does not inherit repository-write, production, financial or secret-management authority.

### Independent user testing

`docs/SIGMA_USER_TESTER.md` defines the independent real-browser acceptance role for applicable user-facing products.

`.github/workflows/sigma-full-user-test.yml` is a reusable GitHub Actions workflow that caller product repositories may use to execute their complete Playwright user-journey suite against an approved deployed preview/staging URL.

The command center itself has no end-user web application, so browser UAT is not applicable unless a user-facing runtime is introduced later.

### Control-plane validation

`scripts/validate_control_plane.py` is the fail-closed repository consistency check used by `.github/workflows/sigma-control-plane.yml`.

It validates mandatory control-plane artefacts, registry uniqueness/basic repository syntax and project-manifest schema compliance.

## Security boundaries

- No application secrets or production credentials belong in this repository.
- GitHub repository permissions are the authentication/authorization boundary for command-center mutations.
- Product authorization, tenancy, RLS and data-security controls remain inside product repositories and must be verified there.
- Browser acceptance never substitutes for hostile authorization/isolation testing.
- Destructive production actions remain outside autonomous control unless explicitly approved under product policy.

## Autonomous runner boundary

`docs/AUTONOMOUS_RUNNER.md` defines the separate portfolio development runner. The expert-mesh runtime is executable, but it does not automatically gain product-repository mutation authority. Issue #2 continues to track the development-runner path that selects and changes product work.

## Evidence model

A readiness or completion statement must name the exact evidence supporting it, such as:

- commit SHA;
- PR;
- GitHub Actions run;
- test report;
- deployed candidate identity;
- browser evidence where applicable.

Historical green evidence does not certify a changed head.
