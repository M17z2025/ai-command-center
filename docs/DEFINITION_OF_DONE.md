# Definition of Done

A task is Done only when all applicable conditions are satisfied.

## Functional
- Acceptance criteria are met.
- Primary and failure paths behave correctly.
- No required feature is represented only by a placeholder or fake success state.

## Code quality
- Build/type check passes.
- Lint/static checks pass where configured.
- Code follows existing project architecture unless an approved architecture change is documented.

## Tests
- Relevant automated tests pass.
- New logic has appropriate coverage.
- Critical flows receive integration/e2e coverage where practical.
- Manual smoke test is documented for UI/device behaviour not covered automatically.

## Security
- Authorization is enforced.
- Tenant isolation is verified where applicable.
- No secret or sensitive data leakage.
- New dependencies/integrations have been security-considered.

## Data
- Schema changes are migrated safely.
- Data migration and rollback/recovery implications are documented.
- Financial/audit records retain required integrity.

## UX
- Loading, empty, error and success states exist.
- Responsive/mobile behaviour is checked for user-facing web apps.
- Accessibility basics are not knowingly regressed.

## Operations
- Environment variable names are documented.
- Deployment notes are updated if required.
- Observability/logging is sufficient for the changed flow.

## Project control
- Issue/PR reflects actual state.
- `PROJECT_STATUS.md` is updated.
- Remaining work is explicitly recorded rather than hidden in chat or memory.
