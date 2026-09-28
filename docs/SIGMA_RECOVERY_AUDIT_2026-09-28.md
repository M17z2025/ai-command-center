# Sigma Recovery Audit — 28 September 2026

## Executive conclusion

Sigma has the major source components required for autonomous engineering, but it **cannot yet reliably finish projects end-to-end**.

The decisive gap is not another expert/agent framework. It is the completion machinery after code generation:

`issue -> plan -> worker -> branch/PR -> CI -> repair -> independent security/evidence -> merge -> deployed verification -> user test -> status/issue closure -> next task`.

The current portfolio runner stops at `WORKER_CHANGED`.

## Control-plane findings

### Proven present
- Sigma expert mesh/orchestrator.
- Independent critic/evidence/security governance.
- Durable SQLite mission/runner state.
- Singleton runner lease + stale-cycle recovery.
- Private Ollama inference overlay.
- Graphiti/FalkorDB memory architecture.
- Private OpenHands coding worker.
- Branch-only worker path and wrapper-owned GitHub credential.
- PR creation.
- Reusable Sigma Full User Test workflow.
- Current command-center exact-head PR verification for PR #81 passed Sigma mesh runtime and control-plane validation.

### Missing for project completion
1. PR supervisor / CI watcher.
2. CI failure diagnosis from job logs.
3. Automatic bounded repair loop against the same PR.
4. Independent post-worker critic/security/evidence verdict wired into runner state.
5. Safe PR merge controller.
6. Deployment adapters.
7. User-test execution/repair loop.
8. Durable issue/PROJECT_STATUS closure.
9. Next-task continuation.
10. Portfolio-capable worker toolchains.
11. Lifecycle-aware issue selection.

## Worker findings

Current `Dockerfile.sigma-worker` installs:
- Python 3.12
- git
- bash
- OpenHands SDK/tools

It does **not** include Node/npm, Playwright/browser runtimes, Java/Gradle/Android tooling or other project-specific build systems.

Current `scripts/sigma_openhands_worker_service.py`:
- defaults allowlist to `M17z2025/ai-command-center`;
- hard-codes independent verification for `M17z2025/ai-command-center` only;
- intentionally stops at TESTED and returns PR evidence;
- correctly withholds VERIFIED/RELEASED.

This is safe for Milestone-1 proof but not a portfolio worker.

## Runner findings

Current `sigma_runtime/portfolio_runner.py`:
- discovers repositories and issues;
- skips contract gaps;
- selects executable work;
- creates a Sigma planning mission;
- can dispatch a worker;
- accepts branch + PR evidence;
- persists final state `WORKER_CHANGED`.

It does **not** continue the PR through CI/repair/merge/deploy/user-test/closure.

Selection currently depends heavily on open issue state, title/body and simple blocker keywords. This is insufficient for long-running autonomous delivery.

## Repository governance findings

### Branch protection
GitHub metadata reported `protected:false` and no required status checks on **all 15 active repositories**:
- ai-command-center
- mi7z-web
- alisha-ai-platform
- invoiceit-by-mi7z
- lycia-zambia
- umarketit
- total-mining-intelligence
- mybodyfit
- tattooit
- legalit
- signit-by-mi7z
- ihumanit
- designit-ai-platform
- synergy-ai-pay
- lycia-limited

Autonomous merge should remain disabled until repository protections/check policies are in place.

### Active contract gaps
Missing `.sigma/project.yaml` and/or `PROJECT_STATUS.md`:
- Lycia Zambia
- Tattooit
- Signit by Mi7z
- Designit AI Platform

### Repositories without GitHub workflows
Confirmed no `.github/workflows` directory:
- Lycia Zambia
- Total Mining Intelligence
- BodyFit
- Tattooit
- Legalit
- Signit by Mi7z
- Synergy AI Pay
- Lycia Limited

Only 7/15 active repositories currently expose GitHub workflows.

## Active-project audit

| Project | Current evidence | Primary blocker before autonomous finish |
|---|---|---|
| Sigma Command Center | Mesh, runner, lease, worker merged | Live OVH commission + post-PR completion state machine |
| Mi7z Web | Contract/status + workflow; PR #2 stale/failing typecheck | Repair exact-head quality/security, then deploy/user test |
| ALYSHA | Strong CI surface; multiple owner/runtime gates | Android/runtime/physical golden journey remains unproven |
| Invoiceit | Contract/status + quality workflow; major source hardening | Hostile two-tenant runtime proof + typecheck/financial E2E |
| Lycia Zambia | Active code and issues | Missing Sigma contract/status/CI + factual-claim provenance |
| Marketit | CI green baseline but strict tenant audit debt | 156 last-confirmed isolation findings + deployed hostile proof |
| Total Mining Intelligence | Contract/status | No automated test/CI; service-role/source-truth audit |
| BodyFit | Contract/status; build/lint pass | Typecheck debt + health/youth/privacy/security proof |
| Tattooit | Baseline PR exists | Missing default-branch contract/status/CI + dependency/security proof |
| Legalit | Contract/status; build/lint pass | Typecheck systemic debt + no CI + hostile organisation isolation |
| Signit | Baseline PR exists | Missing default-branch contract/status/CI |
| Humanit | Strong exact-head source gate | Deployed Base44 parity + Full User Tester |
| Designit | Large PR stack + workflow | Missing default-branch Sigma contract/status; stacked PR reconciliation |
| Synergy AI Pay | Contract/status | P0 server-side tenant + financial command/audit/idempotency layer |
| Lycia Limited | Contract/status; build/lint pass | Typecheck + governance records + live HMRC/Shufti/SMTP proof |

## Issue hygiene fix performed during audit

Closed as source-complete/superseded by merged evidence:
- #60 — WorkerAdapter foundation (PR #61 merged)
- #62 — current-main runner/inference source implementation (PR #63 merged)
- #78 — singleton lease/stale recovery (PR #79 merged)
- #80 — private OpenHands coding worker source implementation (PR #81 merged)

Keeping merged source work open was a direct risk to autonomous task selection.

## Recovery programme

Master: #88

- #89 PR supervisor / repair / merge state machine
- #90 manifest-driven worker profiles/toolchains
- #91 portfolio contracts + CI + security normalization
- #92 deployed preview adapters + Full User Tester runtime
- #93 lifecycle-aware work selection

Existing mandatory gates:
- #25 live private Sigma commissioning
- #42 portfolio security rollout
- #14 command-center branch protection
- #4 command-center visibility decision
- #77 first real autonomous engineering proof

## Open-source reuse decision

Do not add another autonomous-agent control plane now.

Keep Sigma as authority/orchestrator and reuse specialist components:
- OpenHands — coding worker (already adopted)
- GitHub Actions — exact-head build/test/check authority
- Playwright — browser user acceptance
- Gitleaks — secret scanning
- Semgrep — SAST where appropriate
- Trivy — container/IaC/dependency scanning where appropriate

SWE-agent/other coding frameworks may remain benchmark/backup workers, not a new authority layer.

## Definition of operational success

Sigma may be called capable of finishing projects only after live evidence proves:
1. current-main runtime commissioned on OVH;
2. real local-model mission succeeds;
3. worker edits real repo and opens PR;
4. Sigma watches CI;
5. failed gate is repaired automatically if present;
6. independent security/evidence gate passes;
7. merge occurs under protected policy;
8. authorised deployed verification occurs when applicable;
9. user-facing work passes full user test;
10. issue + PROJECT_STATUS are updated;
11. lesson is evaluated/persisted;
12. runner proceeds to next task without owner terminal operation.

Until then, the truthful classification is: **components built; autonomous project finishing not yet proven**.
