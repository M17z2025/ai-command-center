# ALISHA Software Factory and Self-Healing Development Layer

## Objective

ALISHA must behave like a controlled software factory rather than a single coding assistant. The target is Base44/Bolt-style development consistency through repeatable blueprints, reusable components, isolated agent workspaces, continuous verification, automatic diagnosis/repair and objective release evidence.

## Open-source worker layer

- OpenAI Symphony — persistent work/issue orchestration and coding-agent dispatch.
- OpenHands — principal autonomous implementation and repair agent.
- Goose — independent implementation/review agent used to challenge work produced by another agent.
- Cline — specialist IDE/headless coding and delegated worktree agent.

These workers are replaceable. ALISHA owns the orchestration, accumulated knowledge, blueprints, reusable components, error history, repair rules and release governance.

## ALISHA-owned control plane

### Software Factory Controller
Converts an approved requirement into architecture, blueprint, tasks, agent assignments, evidence requirements and deployment plan.

### Continuous Repair Controller
Consumes CI, deployment, runtime, security, visual and performance events. It reproduces failures, creates/updates regression tests, delegates fixes, re-runs gates and submits evidence-backed PRs.

### Blueprint Library
Versioned golden architectures for common product types. New products should compose proven blueprints instead of inventing infrastructure from scratch.

### Component Registry
Stores approved reusable implementations for authentication, tenant/RLS controls, navigation, upload, documents, email, payments, AI chat, permissions, audit, error handling and other repeated capabilities.

### Quality Gate
A release is verified only when applicable compile/type/lint/test/security/accessibility/performance/smoke gates pass.

### Error Bus
Normalises failures from every Mi7z application into repair events with repository, environment, release, trace/log evidence and severity.

## Standard workflow

Requirement -> domain/router -> blueprint selection -> component reuse -> task decomposition -> isolated agent implementation -> independent review -> automated tests -> security/performance/visual gates -> staging -> acceptance -> governed production promotion.

## Self-healing workflow

Failure -> Error Bus -> reproduce -> regression test -> root-cause classification -> repair agent -> independent reviewer -> full relevant gates -> PR -> staging validation -> governed promotion -> incident/lesson stored for reuse.

## Reliability rules

1. No agent may self-certify its own implementation.
2. Prefer a known-good blueprint/component before generating new architecture.
3. A repair should prove the original failure and protect against recurrence where practical.
4. Autonomous code execution happens only in isolated workspaces.
5. Runtime errors never cause direct unreviewed production edits.
6. Objective CI/test evidence overrides an agent's assertion that work is finished.
7. Repeated failures must update the blueprint/component/error knowledge so the same class of defect becomes less likely in future builds.
8. GitHub remains the source of truth for code, PRs, evidence and deployment definitions.

## Target outcome

As ALISHA accumulates proven blueprints, components, failure signatures and repair patterns, a larger percentage of each new application should become composition and verification rather than greenfield generation. This is the mechanism intended to make later builds faster and more reliable than early builds.
