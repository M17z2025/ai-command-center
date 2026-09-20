# Sigma Development Command Center

Sigma is the central control repository for the Mi7z/Lycia software portfolio.

Its purpose is to let Sigma, ChatGPT and human developers work from the same source of truth across all product repositories without relying on chat history.

## Core responsibilities

1. Maintain the master project registry.
2. Define the minimum repository structure every product must expose.
3. Define the development execution loop.
4. Define the handoff contract between Sigma, ChatGPT and developers.
5. Track project status, blockers, risks and next actions.
6. Enforce security, testing and definition-of-done standards.
7. Prevent duplicate, conflicting or undocumented development work.

## Operating model

- Product code remains in each product repository.
- Sigma stores orchestration rules, manifests, templates and portfolio status.
- Each product repository must expose a `.sigma/project.yaml` manifest and `PROJECT_STATUS.md`.
- Work is performed on branches and reviewed through pull requests.
- Secrets, API keys, production credentials and customer data must never be committed.
- ChatGPT can inspect the manifest, status, issues, code and tests, then implement changes directly in the product repository.
- Sigma can review the same artefacts, create/triage work items and keep the portfolio aligned.

## Start here

Read these files in order:

1. `AGENTS.md`
2. `docs/OPERATING_MODEL.md`
3. `docs/DEVELOPMENT_LOOP.md`
4. `docs/CHATGPT_HANDOFF.md`
5. `docs/SECURITY_BASELINE.md`
6. `docs/DEFINITION_OF_DONE.md`
7. `projects/registry.yaml`

## Repository layout

```
.
├── AGENTS.md
├── SECURITY.md
├── docs/
├── projects/
├── schemas/
├── scripts/
├── templates/
└── .github/
```

## Golden rule

No agent should guess project state. Read the repository, manifest, current status, issues, recent commits and tests before changing code.
