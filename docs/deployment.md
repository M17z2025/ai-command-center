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

The command-center validation path itself requires no secret.

Runner phase-1 discovery may optionally use `SIGMA_GITHUB_TOKEN` to read managed repositories that are not publicly accessible. Supply it only at runtime and prefer a least-privilege GitHub App installation token with read access to the required repository metadata/contents/issues/pull requests. The discovery client rejects non-GET GitHub API operations.

GitHub Actions may expose `GITHUB_TOKEN` automatically; its effective repository access remains constrained by GitHub permissions and does not prove cross-repository access.

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
