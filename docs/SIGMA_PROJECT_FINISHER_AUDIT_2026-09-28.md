# Sigma Project-Finisher Audit — 28 September 2026

## Executive verdict

Sigma has the major source components of an autonomous engineering system, but it is **not yet a proven project-finisher**.

Current source contains:
- portfolio discovery and task selection;
- expert-mesh planning/critic/evidence-verifier runtime;
- durable SQLite mission/runner state;
- Graphiti/FalkorDB memory;
- local Ollama inference overlay;
- private OpenHands coding worker;
- branch/commit/PR wrapper;
- Sigma User Tester specification/workflow;
- security/advisory/engineering governance.

The blocking gap is not another advisory layer. It is the **execution lifecycle after a worker opens a PR**, plus live commissioning, secure credential/control boundaries, worker/toolchain breadth and portfolio standardisation.

## Measured portfolio state

Active repositories in `projects/registry.yaml`: **15**.

Fresh GitHub inspection:
- protected active default branches: **0 / 15**;
- active repositories with any `.github/workflows` directory on default branch: **7 / 15**;
- active repositories missing the complete `.sigma/project.yaml` + `PROJECT_STATUS.md` pair on default branch: **4 / 15** — Lycia Zambia, Tattooit, Signit and Designit;
- repositories currently supported by the private worker's independent verification function: **1 / 15** — command center only;
- proven live full-stack autonomous Sigma commissioning on OVH: **0**;
- implemented post-PR completion supervisor: **0**.

The command-center repository itself is currently public and its `main` branch is unprotected.

## P0 finding 1 — runner stops after PR creation

Current `PortfolioRunner.cycle()` accepts a worker result containing a branch and pull-request URL, records `WORKER_CHANGED`, and returns.

It does not currently:
- poll exact-head CI/check runs;
- independently review the implementation diff after the code change;
- run the Cybersecurity Division gate against the changed code;
- dispatch repair work back to the same PR branch;
- re-run checks after each repair;
- merge a verified PR;
- trigger an authorised staging deployment;
- run Sigma Full User Tester;
- close/update the issue;
- update `PROJECT_STATUS.md`;
- select the next project task.

This is the principal reason Sigma can create work but cannot yet prove it finishes projects.

Tracked by: **#82**.

## P0 finding 2 — worker only supports Sigma's Python repository

`scripts/sigma_openhands_worker_service.py::_verify_command()` only defines an independent verification command for `M17z2025/ai-command-center`.

Every other repository currently raises:
`No independent verification command registered for <repository>`.

The worker image is `python:3.12-slim` with Git/Bash. It does not contain the toolchains needed by most of the portfolio:
- Node/npm/pnpm;
- browser/Playwright runtime;
- Java/Gradle/Android SDK;
- provider-specific build/deployment tooling.

A worker fleet / trusted adapter registry is required.

Tracked by: **#83**.

## P0 finding 3 — current OVH deployment path is legacy and incomplete

The existing self-hosted OVH workflows prove that GitHub can reach the owner-controlled VPS and run Docker. However, the current ALYSHA / MI7Z Build Factory deployment paths deploy only the older `sigma-mesh-runtime` against the Build Factory / FreeLLMAPI route.

They do **not** commission the current full autonomous stack:
- Ollama;
- Sigma runtime;
- Sigma runner daemon;
- OpenHands worker;
- FalkorDB;
- Graphiti memory.

The legacy ALYSHA wrapper also hard-requires:
`/home/alisha/.config/mi7z-build-factory/factory.env`.

That makes Sigma dependent on an unrelated Build Factory secret/config package.

Additional deployment-contract defects:
- the legacy Build Factory workflow launches Sigma without `SIGMA_RUNTIME_TOKEN`, while current `sigma_live_probe.py` requires that token;
- the current Ollama overlay uses `ollama-chat` / `/api/chat`, while `sigma_inference_probe.py` currently accepts only `chat-completions`;
- model-init pulls the primary and embedding models but does not explicitly pull `OLLAMA_WORKER_MODEL` if it differs;
- deployment documentation describes an OpenAI-compatible Ollama endpoint while the current overlay configures the native Ollama chat endpoint;
- the base Compose file still has required `SIGMA_LLM_ENDPOINT` / `SIGMA_LLM_MODEL` interpolation that must be proven compatible with the overlay using real `docker compose config` CI.

Tracked by: **#84**.

## P0 finding 4 — unsafe to enable autonomous writes yet

### Branch/ruleset state

Every active repository inspected reports `main protected:false` with no required status checks.

### Privileged self-hosted-runner triggers

- ALYSHA's current Sigma OVH workflow still has a push trigger in addition to manual dispatch.
- `mi7z_core_Intelliegence` is unprotected and its Build Factory + Sigma deployment workflow can run on the self-hosted OVH runner after pushes to factory/workflow paths.
- privileged self-hosted runner workflows must not be controllable from unprotected direct pushes.

### GitHub credential boundary

The current `sigma-worker` service receives `SIGMA_GITHUB_TOKEN` in the same service environment in which the OpenHands terminal agent executes.

Source inspection does not prove that the agent cannot read the environment or alter Git configuration/hooks in the checkout before wrapper-owned Git commands execute.

Required architecture: agent produces an untrusted patch/worktree result **without GitHub credentials**; a separate trusted broker applies the patch to a fresh checkout, disables hooks/credential helpers, independently verifies it, mints a short-lived least-privilege GitHub App token, then commits/pushes/opens the PR.

### API execution-authority defect

The runner daemon honours `SIGMA_RUNNER_EXECUTE`, but the runtime API currently accepts caller-supplied `{"execute": true}` and passes it directly to the portfolio runner. Execution authority must be fixed at runtime construction; an API request may reduce authority but must never elevate it.

### Untrusted issue content

Current selection can turn any qualifying open issue title/body into model/worker instructions. Priority may be influenced by a `P0` title string. Executable tasks require a trusted structured admission state/label and must treat issue prose as untrusted data.

### Container/build context

- repository currently has no `.dockerignore`;
- `Dockerfile.sigma-runtime` uses `COPY . .`;
- a populated host-side `.env` in a persistent checkout can enter the build context unless excluded;
- runtime and memory images currently run as root inside the container;
- resource/network limits for coding execution need stronger enforcement.

Tracked by: **#85**.

## P0 finding 5 — task state and contracts are not machine-reliable enough

Current runner uses issue prose substring matching for blockers. Words such as `blocked` or `owner-gated` anywhere in the issue can make an otherwise executable issue non-executable.

Conversely, stale/source-complete issues can remain open and be selected again.

Current project manifests are structurally inconsistent with the central schema. Examples observed include different top-level keys and repository placement.

Projects with missing manifest/status are marked `CONTRACT_GAP` and are skipped entirely. That means Sigma cannot autonomously repair the very onboarding gap that prevents selection.

Task selection currently sorts roughly by priority then repository name/issue number. There is no project priority, task aging, dependency graph, fair scheduling or in-flight continuity.

Tracked by: **#86**.

## P0 finding 6 — current worker cannot safely take over existing PRs

Most real projects already contain in-flight branches/PRs. The worker always clones the default branch and creates a new `sigma/*` branch.

Sigma needs a governed continuation mode:
- identify one unambiguous linked PR;
- inspect exact head;
- safely continue the same branch where permitted;
- refresh exact-head checks after every repair;
- preserve human work;
- create a new branch only for new work or an explicitly superseded PR.

Tracked by: **#82**.

## P0 finding 7 — task-type routing is absent

The portfolio contains software engineering, research, legal/compliance, deployment, browser QA, film/creative production and governance issues.

The current runner has one generic worker dispatch path. It must not send non-code tasks to OpenHands merely because they are the next open issue.

Required task types / capability matching:
- coding;
- browser/user testing;
- deployment;
- research/evidence;
- data migration;
- creative/media;
- governance/documentation.

Missing worker capability must produce `CAPABILITY_GAP`, not wrong-worker execution.

Tracked by: **#83**.

## Portfolio readiness gaps

### Missing contract/status on default branch
- M17z2025/lycia-zambia
- M17z2025/tattooit
- M17z2025/signit-by-mi7z
- M17z2025/designit-ai-platform

### No default-branch GitHub workflow currently found
- M17z2025/lycia-zambia
- M17z2025/total-mining-intelligence
- M17z2025/mybodyfit
- M17z2025/tattooit
- M17z2025/legalit
- M17z2025/signit-by-mi7z
- M17z2025/synergy-ai-pay
- M17z2025/lycia-limited

### Current material project blockers

**Mi7z Web**
- open PR #2;
- two bounded TypeScript failures recorded;
- vulnerable Next 15.5.3 recorded;
- production Supabase/R2/Cloudflare path not commissioned.

**ALYSHA**
- many current P0/P1 branches/PRs;
- trusted release / physical Samsung journey remains a separate hard gate;
- current main still contains the older push-triggered OVH Sigma commissioning path.

**Invoiceit**
- source-side tenant hardening is advanced;
- genuine two-tenant/restricted-user hostile runtime proof remains missing;
- typecheck debt remains large;
- end-to-end financial concurrency/idempotency proof remains incomplete.

**Lycia Zambia**
- missing contract/status/CI;
- content/regulatory provenance and user/security verification remain incomplete.

**Marketit**
- exact source has substantial security hardening;
- last durable strict audit still records 156 tenant-isolation findings;
- current head needs a fresh strict isolation audit.

**Total Mining Intelligence**
- no automated test script/CI;
- service-role paths and source provenance/live-vs-mock truth require audit.

**BodyFit**
- typecheck baseline remains materially broken;
- health/youth/privacy/service-role boundaries need independent verification.

**Tattooit**
- baseline PR remains open;
- contract/status not on main;
- dependency-security gate has recorded HIGH findings;
- hostile cross-studio/cross-role verification remains required.

**Legalit**
- systemic checkJs/shared UI typing debt;
- no repo-local CI;
- hostile cross-organisation/confidentiality proof missing.

**Signit**
- baseline PR open;
- no contract/status/CI on main;
- signer/document/audit authorization proof missing.

**Humanit**
- source quality gate is strong;
- deployed Base44 parity, runtime integrations/OAuth and Sigma Full User Tester remain release gates;
- stale open PR/issue backlog needs reconciliation so automation does not select obsolete work.

**Designit**
- contract/status missing on main;
- stacked Supabase PR chain requires reconciliation and exact-head assurance.

**Synergy AI Pay**
- no CI;
- server-side tenant isolation and financial command/audit/idempotency are P0.

**Lycia Limited**
- no CI;
- typecheck debt;
- DPIA/ROPA/retention operational evidence and HMRC/Shufti/SMTP live proof incomplete.

## Security tooling gap

Org-wide code search found no deployed Gitleaks or Semgrep integration across the portfolio. Trivy references are largely concentrated in ALYSHA.

Candidate proven open-source components found in GitHub search:
- OpenHands/OpenHands — retain as replaceable coding executor;
- SWE-agent/SWE-agent — useful independent coding-agent benchmark/fallback, not Sigma authority;
- microsoft/playwright / playwright-mcp — browser acceptance and exploratory testing;
- gitleaks/gitleaks — secret scanning;
- aquasecurity/trivy — filesystem/container/dependency/IaC scanning;
- semgrep/semgrep — SAST;
- renovatebot/renovate — controlled dependency update automation.

Each component still requires pinned-version/licence/security review before admission through Sigma Scouter.

## Knowledge/memory is not the immediate blocker

Graphiti/FalkorDB memory and lesson candidate/evaluation/promotion code exist. Black-Belt/continuous-knowledge PR #50 is currently stale/diverged and is governance/architecture only.

Do **not** block Milestone 1 on further workforce expansion, Black-Belt growth, film production or broad AGI features.

First prove project completion.

## Required execution order

### Gate 0 — freeze non-essential expansion
No new Sigma departments/creative programmes/infrastructure rewrites should outrank project-finisher work until Milestone 1 passes.

### Gate 1 — secure the control plane
Execute #85:
- protect branches;
- remove/guard privileged push-triggered self-hosted workflows;
- isolate GitHub credentials in a broker;
- fix execute-authority and prompt-injection admission;
- add Docker secret/root/resource hardening;
- add secret/SAST/container scanning.

### Gate 2 — commission current full stack
Execute #84:
- current command-center main;
- Ollama;
- runtime;
- memory;
- worker;
- runner;
- live mission;
- restart persistence;
- planning cycle;
- write/execute still off.

### Gate 3 — make workers portfolio-capable
Execute #83:
- canonical manifest schema;
- trusted verification adapters;
- task-type routing;
- Node/browser/Base44 profiles;
- initial allowlist expansion only after security review.

### Gate 4 — implement project-finishing state machine
Execute #82:
- CI observation;
- independent diff review;
- repair loop;
- security gate;
- merge;
- staging deployment adapter;
- Sigma Full User Tester;
- issue/status closure;
- next-task continuation;
- existing PR takeover.

### Gate 5 — normalise portfolio
Execute #86:
- contracts/status;
- CI;
- security gates;
- labels/state;
- backlog grooming;
- Golden User Journey metadata;
- fair/dependency-aware scheduling.

### Gate 6 — prove Milestone 1
Issue #77 remains the non-negotiable acceptance gate.

Required proof:
real registered issue -> plan -> worker -> branch -> code -> tests -> independent critic -> repair if needed -> security/evidence -> PR -> merge/status update -> candidate lesson -> independent evaluation -> later retrieval.

No owner shell operation.

### Gate 7 — expand one repository at a time
After command-center proof:
1. choose one bounded Node/web repository;
2. commission its worker profile;
3. prove full completion loop;
4. then expand the allowlist.

Do not enable all 15 repositories at once.

## Definition of “Sigma can finish projects”

Do not use this phrase until all are true:
1. full current stack is continuously live on OVH;
2. runner survives restart and resumes state;
3. worker has no GitHub credentials in the agent execution boundary;
4. one real issue completes autonomously through merge;
5. a failed CI/review is automatically repaired;
6. applicable security gate is independently passed;
7. user-facing change is deployed to approved staging and Sigma User Tester passes;
8. issue and PROJECT_STATUS are updated durably;
9. next executable task starts automatically;
10. promoted operational learning is later retrieved;
11. branch protection prevents bypass;
12. no paid/destructive/production owner gate is silently crossed.

Until then, Sigma is a strong orchestration/worker platform under construction—not yet a proven autonomous project-finisher.
