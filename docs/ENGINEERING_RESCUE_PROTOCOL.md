# Sigma Golden Engineering Challenge & Rescue Mode

## Purpose

Sigma engineering is judged by real delivery evidence.

Synthetic orchestration tests prove that Sigma can route, critique and persist a mission. They do **not** prove that a product feature works or that a broken application has been repaired.

For material development, the final acceptance test is the actual product/repository/user journey.

## Golden Engineering Challenge — new development

A material new build or feature is complete only when Sigma has:

1. inspected the real product repository, manifest, status, architecture, issues/PRs, recent commits and tests;
2. translated the owner goal into acceptance criteria and a Development Advisory Plan;
3. used the Algorithmic Engineering & Solution Lab where applicable;
4. implemented the work in the real product repository;
5. run exact-head build/type/lint/unit/integration/e2e checks as applicable;
6. completed independent cybersecurity assurance;
7. deployed to an authorised preview/staging candidate where the user journey requires deployment;
8. run Sigma Full User Tester through all applicable critical user journeys and roles;
9. repaired defects/regressions and rerun the failed evidence;
10. updated PROJECT_STATUS.md and durable evidence with what works, what remains and exact next actions.

A design, plan, branch, PR, build pass, unit-test pass or source inspection alone is not a Golden Challenge PASS when deployed/user evidence is applicable.

## Engineering Rescue Mode — broken products and defects

Rescue Mode is activated for requests such as:
- broken / not working;
- error / crash / failing;
- regression;
- fix this;
- cannot login / cannot save / cannot connect;
- user journey fails;
- integration stopped working;
- performance/reliability failure.

### Rescue loop

1. **Discover real state**
   - Read repository truth.
   - Read error reports, logs, failing tests and deployed evidence.
   - Do not start from chat assumptions.

2. **Reproduce**
   - Reproduce the defect in the safest available environment.
   - Prefer an automated failing regression test plus a deployed/browser reproduction where applicable.
   - If reproduction is impossible, record exactly what access/evidence is missing.

3. **Root cause**
   - Isolate the causal chain rather than patching the visible symptom.
   - Trace state across UI, API, auth, database, integration and infrastructure boundaries where relevant.

4. **Competing repair hypotheses**
   - For non-trivial defects, consider at least two credible causes/repairs.
   - Use evidence to eliminate weaker hypotheses.

5. **Repair**
   - Implement the smallest correct repair consistent with architecture and security.
   - Do not weaken tests/security controls to make the symptom disappear.

6. **Regression coverage**
   - Add a test that fails before the repair and passes after it where practical.
   - Cover adjacent failure paths when the root cause suggests broader risk.

7. **Independent challenge**
   - Solution Judge reviews the repair.
   - Cybersecurity reviews affected trust boundaries.
   - Independent Critic challenges hidden assumptions.

8. **Real user verification**
   - For user-facing defects, deploy an authorised preview/staging candidate.
   - Sigma Full User Tester repeats the actual failing journey and relevant regressions.

9. **Close or continue**
   - Close only with reproducible PASS evidence.
   - Otherwise continue the loop or mark **UNSOLVED / BLOCKED** with the exact next experiment or genuine owner/external gate.

## Completion language

Sigma must not use **fixed**, **working**, **complete**, **ready**, **passed**, **release-ready** or equivalent as a factual status unless the relevant exact evidence exists.

Allowed states:
- **FIXED / VERIFIED** — defect reproduced, repaired and verified through applicable exact-head and real-user evidence.
- **FIXED IN SOURCE / DEPLOYED VERIFICATION PENDING** — source evidence passes but deployed user verification is still missing.
- **PARTIALLY REPAIRED** — some acceptance criteria remain open.
- **UNSOLVED / NEEDS NEXT EXPERIMENT** — no current repair has met the hard gates.
- **BLOCKED** — a genuine owner/external gate prevents the next required verification/action.

## Golden Challenge scorecard

Every real pilot records:
- request;
- product/repository;
- starting failure/state;
- time-independent sequence of actions (not optimistic estimates);
- specialists used;
- root cause or design decision;
- implementation/repair refs;
- exact test evidence;
- security verdict;
- deployed user-test verdict;
- regressions found and repaired;
- remaining blockers;
- final classification.

Use `templates/SIGMA_ENGINEERING_RESCUE_REPORT.md`.
