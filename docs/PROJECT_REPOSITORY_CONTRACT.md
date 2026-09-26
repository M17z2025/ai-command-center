# Product Repository Contract

Every product managed by Sigma should expose enough machine-readable and human-readable context for an implementation agent to work safely.

## Required structure

```
<product-repo>/
├── .sigma/
│   └── project.yaml
├── AGENTS.md
├── PROJECT_STATUS.md
├── README.md
├── .env.example
└── docs/
    ├── architecture.md
    └── deployment.md
```

Existing equivalent documents may be referenced in the manifest instead of duplicated.

## .sigma/project.yaml

The manifest is the machine-readable entry point. It must identify:
- exact repository;
- product purpose;
- primary users and critical flows;
- frontend/backend/database/auth/storage/hosting stack;
- install/dev/build/lint/typecheck/test commands;
- deployment provider and production branch;
- security classification;
- required environment variable names;
- key integrations;
- constraints;
- product-specific definition-of-done additions.

Secret values must never appear in this file.

## AGENTS.md

Product-specific instructions override the generic Sigma agent contract only where explicitly stated. It should record architectural rules, naming conventions, protected modules, data-safety requirements and prohibited shortcuts.

## Algorithmic engineering inheritance

Every registered product inherits the Sigma Algorithmic Engineering & Solution Lab for applicable material software/technical development.

The product issue/PR/status must link a current `SIGMA_ALGORITHMIC_SOLUTION_REPORT.md` or stricter equivalent when the work involves a meaningful algorithm/architecture/debugging/performance/testing decision. The report must not claim tests or benchmarks that were not actually executed and evidenced.

If no candidate satisfies correctness/security hard gates, the repository must record the work as unresolved or blocked with the exact next experiment rather than marking it complete.

## Expert advisory planning inheritance

Every repository registered in `projects/registry.yaml` inherits the Sigma Universal Expert Advisory & Development Planning Council for material development work.

Before major implementation, Sigma must route materially relevant experts and create/update a durable plan using `templates/SIGMA_DEVELOPMENT_ADVISORY_PLAN.md` or an equivalent repository-backed issue/plan. Product repositories may add stricter planning requirements but must preserve the central requirements for evidence, specialist advice, risks, ordered backlog/pull plan, acceptance criteria and exact next actions.

## Cybersecurity assurance inheritance

Every repository registered in `projects/registry.yaml` inherits the Sigma Cybersecurity Division gate for material work. A product may define stricter controls in its manifest/AGENTS.md but may not silently weaken the central gate.

For material development/release work, the product status/issue/PR must link durable security evidence using `templates/SIGMA_CYBER_SECURITY_REPORT.md` or an equivalent stricter report. Required controls marked NOT VERIFIED prevent a security PASS. The implementation agent cannot self-certify the final verdict.

## PROJECT_STATUS.md

This is the current operational truth. It should be concise and updated after material work. It must separate:
- working;
- in progress;
- broken/blocked;
- security/data risks;
- external dependencies;
- next three actions;
- verification state.

## README.md

The README should enable a developer/agent to understand and run the project from a clean checkout.

## .env.example

Names only. Never credentials. Each variable should be documented or self-explanatory.

## docs/architecture.md

Document runtime boundaries, major components, data model/tenancy, auth, external integrations and key design decisions.

## docs/deployment.md

Document environments, build/deploy process, migrations, rollback/recovery and smoke checks.

## Adoption sequence

1. Audit repository.
2. Create manifest from facts found in code/config.
3. Create/update status.
4. Create/update architecture and deployment docs.
5. Identify missing test/security controls.
6. Open issues for gaps.
7. Only then enter the autonomous development loop.
