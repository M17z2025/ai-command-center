# Decision 2 — Mitz PA consolidated into Friday AI
**Owner instruction: Option A, 2026-10-30**

Mitz PA appeared only as an **intake project with no GitHub repository** in Sigma's previous `headquarters/chat-ownership/teams.yaml`. It is **not** a second app or service.

Canonical product: Friday AI (`M17z2025/alisha-ai-platform`).
Canonical Sigma record: `Alysha AI Platform`, display name `Friday AI`.
Historic aliases: `Mitz PA`, `Mitz personal assistant`, `Jarvis`, `personal assistant`.

## Implemented control-plane transition
1. Remove the standalone Mitz PA row from `intake_projects`.
2. Route historical titles/phrases to Friday in the existing canonical project alias list.
3. Add a non-executable `consolidated_products` record to both the project register and ownership map.
4. Regression tests verify those aliases return Friday and no `PROJECT_REPOSITORY_REQUIRED` duplicate appears.
5. Keep all other projects and Decision 1 repository redirects unchanged.

## Unique historical requirements preserved
The original Mitz PA Google Drive blueprint, requirements register, architecture, delivery roadmap and build instructions were inspected before consolidation. The detailed requirement-to-acceptance matrix and historical-source links are recorded privately in Friday:
`docs/consolidations/2026-10-30-mitz-pa-into-friday.md`.

The main capabilities are secure voice and text, project-scoped memory controls, Gmail/Calendar/Contacts integrations with read/write permission separation, approvals, agent status, authorised workflow automation and project status reporting. This is a **requirements consolidation**, not proof that all listed capabilities are already operational.

## Governance and architecture precedence
- Reuse Friday's existing Kotlin/Compose Android application and SIP/Asterisk + OpenAI Realtime phone stack. Historical React Native/Expo or Vercel proposals do not override those decisions.
- Sigma remains owner of the cross-repository development workforce and agent/CI automation. Friday can surface its evidence or delegate bounded approved operations, not run a second Sigma.
- No new account, app, repository, domain, Android signing path, database, payment service or live provider is created.
- No approved release, live model action, phone call or device verification is inferred by this documentation change.

## Verification
Pass exact-head Sigma control-plane validation, Sigma mesh runtime and the explicit routing/negative tests. Friday's exact-head web quality gate must pass, and no existing Android/mobile release files may change. Only then merge.
