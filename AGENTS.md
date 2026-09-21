# Agent Operating Contract

This file applies to Sigma, ChatGPT and any coding agent working under this command center.

## Authority order

When instructions conflict, use this order:

1. Explicit current instruction from the product owner.
2. Product repository `.sigma/project.yaml`.
3. Product repository `PROJECT_STATUS.md`.
4. Open GitHub issue / accepted implementation plan.
5. Current code, tests and database migrations.
6. Historical documentation.
7. Chat history.

Never silently override a higher-authority source.

## Mandatory pre-work inspection

Before changing a product repository:

1. Read `.sigma/project.yaml`.
2. Read `PROJECT_STATUS.md`.
3. Read the repository README and architecture documentation.
4. Inspect recent commits and open issues/PRs relevant to the task.
5. Identify the runtime, package manager, test commands and deployment target.
6. Check security-sensitive areas: auth, tenancy/RLS, secrets, storage, payments and external integrations.
7. Confirm the exact acceptance criteria.

If a required artefact is missing, create or repair it as part of the work rather than guessing.

## Development rules

- Work from an issue or a clearly recorded task.
- Use a branch for material changes.
- Keep commits focused and descriptive.
- Prefer production code over mock-only implementations.
- Do not hard-code credentials, customer data, environment-specific secrets or fake production values.
- Do not disable security controls to make a test pass.
- Do not claim a feature is complete until the relevant tests/build checks pass or the failure is documented.
- Preserve existing working behaviour unless the task explicitly changes it.
- For multi-tenant systems, prove tenant isolation for every new data path.
- For migrations, provide forward migration, rollback/recovery notes and data-safety considerations.
- For third-party integrations, document required environment variable names and failure behaviour.

## Mandatory Sigma Full User Tester

Every material user-facing development must pass the independent Sigma Full User Tester before it can be called complete or release-ready. Read `docs/SIGMA_USER_TESTER.md` and use `templates/SIGMA_USER_TEST_REPORT.md`.

The tester must operate the deployed preview/staging product through a real browser as an end user, not infer usability from source code. It must cover all applicable critical journeys, relevant roles, desktop/mobile browser coverage, negative/error paths, and provide an explicit UX assessment plus evidence. A blocked or untested critical journey is not a pass.

The implementing agent cannot self-certify user acceptance. The tester is a separate assurance role. Product repositories should expose a complete Playwright user-journey suite and may call the reusable `.github/workflows/sigma-full-user-test.yml` workflow from this command center.

## Required completion output

Every material task must leave:

- code changes;
- tests or a documented reason tests are not applicable;
- updated documentation when behaviour/architecture changes;
- updated `PROJECT_STATUS.md`;
- a concise handoff note describing what changed, what remains and any blocker;
- no unresolved TODO that is required for the stated acceptance criteria.

## Handoff rule

An agent must never rely on private memory as the only record of a decision. Put durable project state in the repository.

## Stop conditions

Stop an autonomous change and escalate through an issue when:

- a destructive production action is required;
- a secret or credential must be supplied by the owner;
- legal/compliance approval is required;
- two authoritative requirements conflict;
- data loss is possible and a safe migration path is unclear.

Everything else should be progressed as far as safely possible.
