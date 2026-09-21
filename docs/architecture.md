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

`docs/AUTONOMOUS_RUNNER.md` defines the target separate execution runner. The repository currently stores the orchestration policy and durable state; it does not itself prove that a continuous unattended implementation service is running.

Issue #2 tracks that implementation gap.

## Evidence model

A readiness or completion statement must name the exact evidence supporting it, such as:

- commit SHA;
- PR;
- GitHub Actions run;
- test report;
- deployed candidate identity;
- browser evidence where applicable.

Historical green evidence does not certify a changed head.
