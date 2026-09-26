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

## 3. Expert advisory plan

For material development, route the relevant Sigma Expert Advisory Council specialists and create/update `templates/SIGMA_DEVELOPMENT_ADVISORY_PLAN.md` (or an equivalent repository-backed issue/plan).

The advisory plan must include the product objective/users, facts/assumptions/proposals, specialist recommendations, architecture/platform implications, UX/creative direction, legal/security/privacy and commercial/HR/finance implications where applicable, dependencies/gates, risks, phased delivery, ordered backlog/pull plan, acceptance criteria, evidence/test plan and exact next executable actions.

## 4. Algorithmic engineering / solution tournament

For applicable software/technical work, use the Sigma Algorithmic Engineering & Solution Lab before and during implementation.

The engineering team must:
- formalise objective/invariants/constraints;
- generate multiple candidates where a meaningful choice exists;
- define the evidence needed to distinguish them;
- prototype/implement the strongest candidate(s) where authorised;
- run appropriate unit/integration/regression/property/fuzz/concurrency/recovery/performance tests;
- obtain independent Solution Judge review;
- preserve rejected alternatives and reasons;
- record unresolved work honestly with the exact next experiment.

Persist the result with `templates/SIGMA_ALGORITHMIC_SOLUTION_REPORT.md` or an equivalent repository-backed report.

## 5. Implementation plan

Select the smallest safe implementation path from the advisory and algorithmic engineering outputs. Identify files/modules, schema changes, external services, migrations, ownership and rollback/recovery impacts.

## 6. Build

Create a branch and implement. Keep security and backward compatibility in scope from the beginning.

Recommended branch names:
- `feat/<issue>-<short-name>`
- `fix/<issue>-<short-name>`
- `security/<issue>-<short-name>`
- `chore/<issue>-<short-name>`

## 7. Verify

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

## 8. Self-review

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

## 9. Independent cybersecurity assurance

Route every material change through the Sigma Cybersecurity Division before READY/release classification.

Use `templates/SIGMA_CYBER_SECURITY_REPORT.md` and record:
- exact commit/environment reviewed;
- applicable trust boundaries;
- hostile authorization/tenant/data-path evidence;
- secret/dependency/supply-chain checks;
- infrastructure/API/integration/AI/recovery checks where applicable;
- findings, severity and retest evidence;
- independent Security Gatekeeper verdict.

The implementing agent cannot self-certify this verdict. Required NOT VERIFIED controls block PASS. BLOCKER, CRITICAL and HIGH findings block release by default.

## 10. Pull request

PR body must include:
- what changed;
- why;
- test evidence;
- migrations/config changes;
- security impact;
- screenshots for UI changes where practical;
- rollback notes for high-risk changes.

## 11. Review and repair

Sigma or another reviewer checks the PR against acceptance criteria and system architecture. Repair substantive findings before merge.

## 12. Merge and deploy

Merge only when required gates pass. Deployment follows the product manifest.

## 13. Close the loop

Update `PROJECT_STATUS.md` with:
- completion state;
- deployed/not deployed;
- current blockers;
- next three highest-value actions.

The next autonomous cycle starts from the updated status, not from chat recollection.
