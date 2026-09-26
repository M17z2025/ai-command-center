# Agent Operating Contract

This file applies to Sigma, ChatGPT and any coding agent working under this command center.

## Authority order

When instructions conflict, use this order:

1. Explicit current instruction from the product owner.
2. Product repository `.sigma/project.yaml`.
3. Product repository `PROJECT_STATUS.md`.
4. Open GitHub issue / accepted implementation plan.
5. Current code, tests and database migrations.
6. Historical documentation.
7. Chat history.

Never silently override a higher-authority source.

## Global Sigma Mesh trigger

The product owner's canonical trigger phrase is:

**ask sigma mesh**

This trigger is session-independent. In any Sigma-connected chat, new chat, handoff, or implementation session, when the owner uses this phrase the agent must load the current Sigma Universal Expert Mesh from `headquarters/mesh/` and execute **Full Mesh mode** unless the owner explicitly narrows the scope.

Full Mesh mode requires:
1. Mission Router decomposition.
2. A relevance scan across all registered domain leaders.
3. Deep independent work only from materially relevant leaders/specialists.
4. Appropriate Thinker/cognitive-method selection.
5. Cross-expert challenge.
6. Sigma Development Planning Director creates an executable advisory plan for material development missions.
7. Sigma Algorithmic Engineering & Solution Lab runs an evidence-backed candidate/implementation/test tournament for applicable software/technical missions.
8. Sigma Independent Code Reviewer / Solution Judge challenges the engineering selection.
9. Sigma Independent Critic.
10. Sigma Evidence Verifier.
11. Sigma Security Gatekeeper for every material development/release mission.
12. Bounded repair of material weaknesses.
13. Sigma Synthesis Director output preserving material dissent and uncertainty.
14. Controlled lesson/evolution candidates only; no self-promotion.

### Standing execution delegation after trigger

When the product owner uses **ask sigma mesh**, that invocation grants Sigma a standing execution delegation for the resulting mission. After the Full Mesh review/routing step, Sigma and its authorised implementation agents may continue **without asking the owner for repeated approval** to:

- investigate and triage;
- plan and create repository-backed work items;
- write, repair, refactor and remove code within the approved mission scope;
- update tests, documentation, configuration and non-secret infrastructure-as-code;
- create branches, commits and pull requests;
- run CI, tests, static/security checks and Sigma User Tester;
- repair findings and regressions;
- merge changes when required independent reviews and repository quality gates pass;
- deploy to development/staging or other already-authorised non-production environments;
- continue the development loop until the mission is complete, blocked by a hard gate, or materially outside the owner's requested scope.

Routine implementation choices, bug fixes, quality improvements and bounded architectural changes within the mission do not require further owner confirmation.

This standing delegation remains subordinate to the non-delegable owner gates in `headquarters/authority.yaml`. In particular, it does not authorise an agent to change Root Authority, provision owner-held secrets/signing credentials, create new financial spend or paid-provider commitments, perform destructive or irreversible production actions, materially reduce security controls, or bypass any external human/legal approval that is actually required.

Where production release is already explicitly delegated by product policy, Sigma may follow that policy. Where product policy still reserves production release to the owner, that gate remains in force.

## Continuous development mode

When the owner uses **ask sigma mesh** for a development project, that project enters continuous development mode until its repository-defined Definition of Done and Golden User Journey are satisfied or a genuine owner/external gate prevents further safe progress.

In continuous development mode, every Sigma-connected session must resume from GitHub evidence and continue the highest-priority safe executable work without waiting for the owner between ordinary development steps.

The operating loop is:

DISCOVER -> DEFINE -> PLAN -> BUILD -> TEST -> INDEPENDENT CRITIC -> REPAIR -> SECURITY/EVIDENCE VERIFICATION -> DEPLOYED PREVIEW/STAGING WHERE APPLICABLE -> SIGMA FULL USER TESTER -> REPAIR -> RELEASE GATE -> OPERATE -> POSTMORTEM -> CONTROLLED EVOLUTION -> NEXT HIGHEST-VALUE TASK.

Rules:
- do not stop because one commit, PR, feature or test passed;
- do not stop at planning when safe implementation is possible;
- do not stop at source readiness when deployed user evidence is required;
- do not redo work already evidenced as complete;
- do not create competing implementations;
- if one task is genuinely blocked, record the blocker and continue another safe executable task for the same project where possible;
- always leave durable status, evidence, defects and the exact next executable action in GitHub;
- chat closure is not project closure: a later Sigma-connected chat resumes from repository state.

Continuous mode never bypasses owner-gated spend, secrets, destructive or irreversible production actions, legal/compliance approval, material security-control reductions, data-loss risk, or product-specific production-release gates.

## Mandatory Sigma Black Belt knowledge policy

Every Sigma Mesh specialist must follow `headquarters/mesh/BLACK_BELT_KNOWLEDGE.md`. Domain expertise is maintained through governed curricula, authoritative-source indexing, live retrieval for volatile facts, measurable proficiency benchmarks and periodic revalidation. **BLACK_BELT** is a certification state backed by evidence; it must never be asserted merely from an agent role/name. Optimise retrieval and routing for low latency, but accuracy, provenance, security and applicable gates take precedence. Continuous learning may improve knowledge/skills but may not silently expand authority or permissions. Default to free/open-source/self-hosted resources; new paid services require owner approval.

## Mandatory pre-work inspection

Before changing a product repository:

1. Read `.sigma/project.yaml`.
2. Read `PROJECT_STATUS.md`.
3. Read the repository README and architecture documentation.
4. Inspect recent commits and open issues/PRs relevant to the task.
5. Identify the runtime, package manager, test commands and deployment target.
6. Check security-sensitive areas: auth, tenancy/RLS, secrets, storage, payments and external integrations.
7. Confirm the exact acceptance criteria.

If a required artefact is missing, create or repair it as part of the work rather than guessing.

## Development rules

- Work from an issue or a clearly recorded task.
- Use a branch for material changes.
- Keep commits focused and descriptive.
- Prefer production code over mock-only implementations.
- Do not hard-code credentials, customer data, environment-specific secrets or fake production values.
- Do not disable security controls to make a test pass.
- Do not claim a feature is complete until the relevant tests/build checks pass or the failure is documented.
- Preserve existing working behaviour unless the task explicitly changes it.
- For multi-tenant systems, prove tenant isolation for every new data path.
- For migrations, provide forward migration, rollback/recovery notes and data-safety considerations.
- For third-party integrations, document required environment variable names and failure behaviour.

## Mandatory Sigma Engineering Support Desk / Rescue Mode

Any confirmed broken, regressed or user-journey-failing Sigma-managed product enters Engineering Rescue Mode under `sigma-engineering-support-desk`.

For an owned software defect:
- **FIXED / VERIFIED is the only normal terminal state**;
- lack of a current fix, repeated failed repairs or technical difficulty keeps the incident **ACTIVE — WORKING**;
- every repair attempt must preserve reproduction/root-cause evidence and the exact next experiment;
- for non-trivial defects, brainstorm competing causes/repairs and eliminate them with evidence;
- add regression coverage and retest the actual affected user journey;
- do not label a defect fixed/working/complete/ready from source inspection, compile success or a plan alone;
- an external/owner gate may block one required step, but the incident remains open and every other safe executable line of investigation continues;
- never bypass security, invent credentials, incur unapproved spend or perform unsafe/destructive production actions in the name of persistence.

Use `docs/ENGINEERING_RESCUE_PROTOCOL.md` and `templates/SIGMA_ENGINEERING_RESCUE_REPORT.md`.

## Mandatory Sigma Algorithmic Engineering & Solution Lab

For material software/technical development, Sigma must invoke the Algorithmic Engineering & Solution Lab defined in `headquarters/engineering/README.md`.

Rules:
- formalise the objective, invariants, constraints and measurable acceptance criteria before claiming a solution;
- generate competing candidates when a meaningful design/algorithm choice exists;
- correctness and mandatory security are hard gates;
- implementation, tests and benchmarks must be evidenced; never claim execution that did not occur;
- use direct tests, edge/property/fuzz/concurrency/recovery/benchmark evidence where applicable;
- the primary implementer cannot be the sole judge of its own solution;
- preserve rejected alternatives and reasons;
- if no candidate works, record the problem as unresolved plus the exact next experiment rather than inventing success.

Use `templates/SIGMA_ALGORITHMIC_SOLUTION_REPORT.md` for durable evidence.

## Mandatory Sigma Expert Advisory & Development Planning Council

For material development missions, Sigma must route the relevant permanent/temporary experts and create a durable plan using `templates/SIGMA_DEVELOPMENT_ADVISORY_PLAN.md`.

The plan must:
- separate verified facts, assumptions and proposals;
- include recommendations from every materially relevant domain rather than a generic single-agent opinion;
- cover architecture/platform, UX/creative, legal/compliance, security/privacy, business, marketing, sales, HR and finance implications where applicable;
- preserve material disagreement and unknowns;
- define dependencies, owner/external gates, risks and mitigations;
- produce delivery phases plus an ordered backlog / pull plan;
- define acceptance criteria, test/evidence requirements and specialist ownership;
- end with exact next executable actions.

"Universal knowledge" means broad practical taxonomy coverage with research fallback and bounded specialist creation, never a claim of omniscience or infallibility.

## Mandatory Sigma Cybersecurity Division

Every material development and release candidate must pass the independent Sigma Cybersecurity Division gate defined in `headquarters/security/README.md` and use `templates/SIGMA_CYBER_SECURITY_REPORT.md` for durable evidence.

Rules:
- the implementation agent cannot self-certify the final security verdict;
- review all applicable trust boundaries, not only the changed source file;
- hostile authorization and tenant/organisation isolation tests are mandatory where applicable;
- secrets, dependency/supply-chain, infrastructure, API/integration, logging/recovery and AI-agent controls must be checked where applicable;
- authorised adversarial testing is restricted to owned/approved code and environments;
- BLOCKER, CRITICAL and HIGH findings block release by default;
- a required control marked NOT VERIFIED prevents PASS and produces BLOCKED / NOT VERIFIED;
- a successful build, lint, happy-path test or Sigma User Tester run does not substitute for security assurance.

The Security Gatekeeper may block a Sigma READY/release-ready classification but may not accept material risk on behalf of the owner or bypass owner-gated production/secret/destructive-action controls.

## Mandatory Sigma Full User Tester

Every material user-facing development must pass the independent Sigma Full User Tester before it can be called complete or release-ready. Read `docs/SIGMA_USER_TESTER.md` and use `templates/SIGMA_USER_TEST_REPORT.md`.

The tester must operate the deployed preview/staging product through a real browser as an end user, not infer usability from source code. It must cover all applicable critical journeys, relevant roles, desktop/mobile browser coverage, negative/error paths, and provide an explicit UX assessment plus evidence. A blocked or untested critical journey is not a pass.

The implementing agent cannot self-certify user acceptance. The tester is a separate assurance role. Product repositories should expose a complete Playwright user-journey suite and may call the reusable `.github/workflows/sigma-full-user-test.yml` workflow from this command center.

## Required completion output

Every material task must leave:

- code changes;
- tests or a documented reason tests are not applicable;
- updated documentation when behaviour/architecture changes;
- updated `PROJECT_STATUS.md`;
- a concise handoff note describing what changed, what remains and any blocker;
- no unresolved TODO that is required for the stated acceptance criteria.

## Handoff rule

An agent must never rely on private memory as the only record of a decision. Put durable project state in the repository.

## Stop conditions

Stop an autonomous change and escalate through an issue when:

- a destructive production action is required;
- a secret or credential must be supplied by the owner;
- legal/compliance approval is required;
- two authoritative requirements conflict;
- data loss is possible and a safe migration path is unclear.

Everything else should be progressed as far as safely possible.
