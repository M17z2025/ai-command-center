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
- The applicable Sigma Cybersecurity Division control matrix is completed against the exact commit/environment.
- Authorization is enforced and hostile negative paths are tested where material.
- Tenant/organisation isolation is verified with direct cross-boundary tests where applicable.
- Database/RLS/storage isolation is verified where applicable.
- No secret or sensitive-data leakage is known; secret scanning is evidenced where supported.
- Dependencies/supply-chain and external integrations have security evidence.
- Infrastructure/container/network/edge controls are reviewed where applicable.
- API/webhook/mobile/session/replay controls are tested where applicable.
- AI/agent prompt-tool injection, authority and data-exfiltration boundaries are tested where applicable.
- Backup/restore/recovery controls are evidenced for persistent critical data.
- No BLOCKER, CRITICAL or HIGH security finding remains open unless an explicit owner/risk-owner exception is recorded where policy permits.
- No required security control is left NOT VERIFIED.
- The independent Sigma Security Gatekeeper has issued PASS or PASS WITH RECORDED NON-BLOCKING FINDINGS.

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


## Sigma real-user certification
For every user-facing web application or user-facing web change:
- Sigma User Tester has exercised the deployed build through a real browser.
- All applicable critical journeys and user roles are covered end-to-end.
- Responsive/mobile behaviour and applicable Chromium/Firefox/WebKit coverage are evidenced.
- Failures include reproducible evidence and GitHub issues.
- The tester provides a first-time-user usability assessment, not only technical assertions.
- No blocker or critical Sigma User Tester defect remains open.
- A partial test run is never represented as a full PASS.

See `docs/SIGMA_USER_TESTER.md`.
