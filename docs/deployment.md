# Sigma Command Center Deployment and Operational Release

## Runtime model

The Sigma Development Command Center has no independently hosted application runtime. Its operational release is the reviewed content on the GitHub default branch, `main`, plus GitHub Actions workflows invoked from repository events or by managed product repositories.

## Release path

1. Start from current `main`.
2. Create a task/issue for material work.
3. Create a branch.
4. Make the bounded change.
5. Run `python scripts/validate_control_plane.py` locally where available.
6. Open a pull request.
7. Require the **Sigma control-plane validation** workflow to pass on the exact PR head.
8. Review the change against the issue acceptance criteria and security baseline.
9. Merge only after required gates pass.
10. Update `PROJECT_STATUS.md` and related issue state from repository evidence.

## GitHub Actions

### Sigma control-plane validation

`.github/workflows/sigma-control-plane.yml` runs on pushes to `main` and pull requests. It installs pinned control-plane Python dependencies and executes `scripts/validate_control_plane.py`.

### Sigma Full User Test

`.github/workflows/sigma-full-user-test.yml` is reusable infrastructure for **caller product repositories**. It expects the caller checkout to provide its Playwright/package setup and a complete user-journey command.

A caller must provide an approved deployed preview/staging `base_url`. The workflow installs Chromium, Firefox and WebKit and uploads Playwright/test evidence.

A workflow invocation is not a PASS by itself: the resulting report must cover all applicable critical journeys/roles and explicitly mark untested scope.

## Environment variables

The command-center validation path currently requires no repository-specific environment variables. `.env.example` therefore contains no variable names.

Managed products document their own required environment variable **names only** in their repositories.

## Rollback

For governance/code changes in this repository, rollback is a normal Git revert or follow-up PR restoring the last known-good state. Do not force-push shared/default branch history.

If a workflow change causes widespread product impact, disable or revert the affected workflow through a reviewed PR while preserving evidence of the incident and repair.

## Production and destructive-action boundary

This repository must not be used to smuggle production credentials or bypass a product's release policy. Database changes, irreversible migrations, production releases and security-control reductions follow the managed product's own approval requirements.

## Smoke/verification checks after merge

- Confirm the merge commit exists on `main`.
- Confirm Sigma control-plane validation passes for the merged state.
- Confirm registry and self-manifest remain readable and schema-valid.
- For reusable workflow changes, verify an applicable caller repository on an approved test target before claiming that user-facing browser certification works end-to-end.


## Expert-mesh runtime deployment

The operational expert mesh is container-ready through `Dockerfile.sigma-runtime`.

The runtime must be deployed only to an approved **private** host/volume because its SQLite database can contain mission prompts, expert outputs, audit events and candidate lessons. The public command-center repository remains governance/source only.

### Required runtime configuration

Names only are documented in `.env.example`:

- `SIGMA_LLM_ENDPOINT`
- `SIGMA_LLM_MODEL`
- `SIGMA_LLM_PROTOCOL`
- `SIGMA_LLM_API_KEY` when the endpoint requires authentication
- `SIGMA_RUNTIME_DB`
- `SIGMA_RUNTIME_TOKEN` for any non-loopback HTTP binding

A real runtime fails closed when a live model endpoint/model is not configured. The deterministic provider is reserved for CI/smoke testing and cannot be represented as production intelligence.

### Container

```bash
docker build -f Dockerfile.sigma-runtime -t sigma-mesh-runtime .
docker run --rm -p 8080:8080 \
  -e SIGMA_RUNTIME_TOKEN \
  -e SIGMA_LLM_ENDPOINT \
  -e SIGMA_LLM_MODEL \
  -e SIGMA_LLM_PROTOCOL \
  -e SIGMA_LLM_API_KEY \
  -v sigma-runtime-data:/data \
  sigma-mesh-runtime
```

The runtime has no implicit product-repository write permission. Cross-repository development actions remain governed separately by the autonomous-runner contract and applicable owner/security gates.
