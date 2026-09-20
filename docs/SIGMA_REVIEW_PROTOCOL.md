# Sigma Review Protocol

Sigma should review projects at two levels.

## Portfolio review

For every managed repository:
- verify the repository contract exists;
- compare status against open issues and recent commits;
- identify stalled work;
- identify duplicate platforms or overlapping responsibilities;
- identify shared components that should become reusable packages/services;
- surface high-impact security or deployment gaps;
- keep the master registry current.

## Task/PR review

For each implementation:
1. Re-read objective and acceptance criteria.
2. Inspect changed files and migration impact.
3. Verify tests/build evidence.
4. Check auth, tenancy, secrets and external integration effects.
5. Check whether the implementation creates architectural duplication.
6. Check failure states, not only happy path.
7. Verify PROJECT_STATUS.md was updated.

## Review output

Use one of:
- READY — criteria satisfied and checks pass.
- CHANGES REQUIRED — list concrete repair items.
- BLOCKED — identify the external decision/access required.

Do not mark work READY based only on an agent's prose summary; inspect repository evidence.
