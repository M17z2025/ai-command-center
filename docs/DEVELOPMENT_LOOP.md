# Development Execution Loop

This is the standard loop for every managed product.

## 1. Discover

Read the manifest, status, architecture, open work, recent commits and tests. Establish the real current state from the repository.

## 2. Define

Convert the requested outcome into:
- problem statement;
- scope;
- acceptance criteria;
- non-goals;
- dependencies;
- risks;
- test plan.

Record this in an issue when the work is material.

## 3. Plan

Select the smallest safe implementation path. Identify files/modules, schema changes, external services and migration impacts.

## 4. Build

Create a branch and implement. Keep security and backward compatibility in scope from the beginning.

Recommended branch names:
- `feat/<issue>-<short-name>`
- `fix/<issue>-<short-name>`
- `security/<issue>-<short-name>`
- `chore/<issue>-<short-name>`

## 5. Verify

Run, as applicable:
- type checking;
- linting;
- unit tests;
- integration tests;
- build;
- database/RLS tests;
- security checks;
- manual smoke test of the affected path.

Do not substitute a successful compile for functional verification.

## 6. Self-review

Check:
- acceptance criteria;
- regressions;
- tenant/data isolation;
- auth/authorization;
- error states;
- mobile/responsive UX where relevant;
- logging/auditability;
- documentation;
- secret leakage.

## 7. Pull request

PR body must include:
- what changed;
- why;
- test evidence;
- migrations/config changes;
- security impact;
- screenshots for UI changes where practical;
- rollback notes for high-risk changes.

## 8. Review and repair

Sigma or another reviewer checks the PR against acceptance criteria and system architecture. Repair substantive findings before merge.

## 9. Merge and deploy

Merge only when required gates pass. Deployment follows the product manifest.

## 10. Close the loop

Update `PROJECT_STATUS.md` with:
- completion state;
- deployed/not deployed;
- current blockers;
- next three highest-value actions.

The next autonomous cycle starts from the updated status, not from chat recollection.
