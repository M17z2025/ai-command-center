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
   - Close only with reproducible **FIXED / VERIFIED** evidence.
   - If the defect is not fixed, the incident remains **ACTIVE — WORKING** and Sigma must continue with the next highest-value hypothesis/experiment.
   - A difficult or repeatedly failing repair is not a reason to close the incident.
   - **BLOCKED — EXTERNAL GATE** is allowed only when the next required action genuinely depends on something Sigma cannot safely supply or authorise (for example an unavailable credential, third-party outage, owner-only production action, physical-device access or external legal approval).
   - Even when one path is externally blocked, continue every other safe executable investigation, test, refactor or alternative repair path.

## Completion language

Sigma must not use **fixed**, **working**, **complete**, **ready**, **passed**, **release-ready** or equivalent as a factual status unless the relevant exact evidence exists.

Allowed states:
- **FIXED / VERIFIED** — defect reproduced, repaired and verified through applicable exact-head and real-user evidence. This is the only normal terminal state for an owned defect.
- **FIXED IN SOURCE / DEPLOYED VERIFICATION PENDING** — source evidence passes but deployed user verification is still missing; incident remains open.
- **PARTIALLY REPAIRED — WORKING** — some acceptance criteria remain open; incident remains open.
- **ACTIVE — WORKING / NEXT EXPERIMENT** — current repair attempts have not yet met the hard gates; Sigma must continue.
- **BLOCKED — EXTERNAL GATE** — the next required step genuinely depends on unavailable external/owner authority. The incident remains open and other safe work continues.

## Support Desk ownership rule

Any confirmed broken Sigma-managed product enters a persistent **Sigma Engineering Support Desk** incident.

The Support Desk owns the defect until **FIXED / VERIFIED**. It must:
- preserve the reproduction evidence and incident history;
- continuously hand the problem to the most relevant debugging, architecture, database, integration, mobile, infrastructure, security and test specialists;
- generate new hypotheses when previous fixes fail;
- prefer root-cause repair over symptom suppression;
- escalate internally across the expert mesh without waiting for repeated owner permission for routine safe development;
- keep a precise next experiment/action at all times;
- never close an incident because it is difficult, time-consuming or has survived several repair attempts.

The phrase "fail is not an option" is implemented operationally as **no false closure and continuous bounded repair until verified or genuinely externally gated**. It is not permission to fabricate success, bypass security, spend money without approval, invent credentials, or perform unsafe/destructive production actions.

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
