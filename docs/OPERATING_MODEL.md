# Sigma Operating Model

## Purpose

Sigma is the portfolio-level engineering command center. Product repositories remain independent deployable systems; Sigma coordinates standards, context and work across them.

## Roles

### Product Owner
Sets commercial goals, priorities and final business decisions.

### Sigma
Acts as portfolio architect, technical programme controller and reviewer. Sigma should:
- inspect project state;
- decompose goals into executable work;
- create/maintain issues;
- identify cross-project dependencies;
- enforce repository contracts;
- surface blockers and security risks;
- prepare precise handoffs for implementation agents.

### ChatGPT
Acts as implementation and problem-solving agent. ChatGPT should:
- read repository state before coding;
- implement scoped changes;
- test and review its work;
- update status/handoff artefacts;
- create PRs where appropriate;
- report concrete blockers rather than generic uncertainty.

### CI/CD
Acts as the objective gatekeeper. Builds, tests, linting, security checks and deployment validation should be automated where practical.

## Source-of-truth model

Portfolio truth:
- this repository;
- `projects/registry.yaml`.

Product truth:
- product code repository;
- `.sigma/project.yaml`;
- `PROJECT_STATUS.md`;
- issues and pull requests;
- database migrations and infrastructure configuration.

Google Drive may hold business blueprints, contracts and source documents, but executable technical state must be linked back into GitHub.

## Required product contract

Each managed product repository should contain:

```
.sigma/project.yaml
PROJECT_STATUS.md
AGENTS.md
README.md
docs/architecture.md
docs/deployment.md
.env.example
```

Equivalent existing files can be referenced from `.sigma/project.yaml` instead of duplicated.

## Repository boundaries

Sigma contains control-plane information, not product source code. Shared reusable code should live in a dedicated package/library repository, not be copied into Sigma.
