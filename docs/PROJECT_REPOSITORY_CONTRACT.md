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
