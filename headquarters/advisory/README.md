# Sigma Universal Expert Advisory & Development Planning Council

## Mission

The Sigma Universal Expert Advisory & Development Planning Council is the permanent cross-disciplinary advisory layer for Sigma-managed development.

Its purpose is to turn broad owner goals into evidence-backed, executable development plans by combining the smallest relevant set of domain experts, challenging the proposal, exposing risks and trade-offs, and leaving developers with an ordered plan they can implement without reconstructing the strategy from chat history.

"Universal" means broad routed coverage with a research fallback and controlled creation of bounded specialists. It is not a claim of omniscience, infallibility or complete knowledge.

## Core duties

For every material development mission, the council should:
1. understand the business/user objective and constraints;
2. identify which expert domains materially matter;
3. independently analyze the problem from those domains;
4. surface conflicts, dependencies, trade-offs and missing evidence;
5. produce a Development Advisory Plan;
6. define acceptance criteria, testing/evidence requirements and owner/external gates;
7. convert the plan into an ordered execution queue;
8. hand the plan to the development team and remain available for specialist review as implementation progresses.

## Permanent expert coverage

The council includes permanent experts for:
- universal research and evidence coordination;
- legal, law and compliance;
- marketing, brand and growth;
- HR, organisational design and people operations;
- sales, commercial strategy and customer success;
- mobile app engineering;
- business strategy, operations, product and programme management;
- finance, accounting, tax, treasury, investment, capital and risk;
- multidisciplinary engineering;
- aerospace engineering;
- coding and software engineering;
- graphic design, branding and visual communication;
- fashion, textiles and wearable products;
- photography;
- film direction;
- film production;
- film editing and post-production;
- scriptwriting and screenwriting;
- songwriting, composition and music/audio across genres;
- plus the wider Sigma knowledge taxonomy.

Where a subject is not explicitly represented, the Research & Evidence Director must route to the closest domains, perform evidence-backed domain discovery and create a bounded temporary specialist if needed. Permanent promotion requires independent evaluation.

## Development Advisory Plan

Use `templates/SIGMA_DEVELOPMENT_ADVISORY_PLAN.md`.

A material plan should cover:
- problem statement and intended users;
- business outcome and success measures;
- evidence and assumptions;
- recommended features;
- explicit non-goals;
- domain-expert recommendations;
- material disagreements and unresolved questions;
- architecture/stack implications;
- mobile/web/platform implications;
- UX/UI, brand and creative direction;
- legal/compliance and privacy considerations;
- cybersecurity requirements;
- commercial, marketing, sales and customer-success implications;
- HR/operating-model implications;
- finance/cost/revenue implications;
- dependencies and owner/external gates;
- risk register and mitigations;
- phased delivery sequence;
- ordered backlog / pull plan;
- acceptance criteria;
- test, security, user-testing and evidence plan;
- deployment/rollout/recovery considerations;
- assigned leaders/specialists;
- exact next executable actions.

## Planning principles

- Facts, assumptions and proposals must be separated.
- Current legal, financial, regulatory and market claims require current evidence when material.
- The smallest sufficient expert team is preferred over routing every problem to every expert.
- Material disagreement is preserved rather than averaged away.
- Advice never weakens the Sigma Cybersecurity Division, Evidence Verifier, Independent Critic, User Tester or owner gates.
- A plan is not "complete" if its next action is vague.
- Development should continue from the plan until the repository Definition of Done is satisfied or a genuine hard gate is reached.

## Relationship to development

The council guides development; it does not replace implementation agents.

The normal flow is:

OWNER GOAL -> MISSION ROUTER -> RELEVANT EXPERTS -> ADVISORY PLAN -> CRITIC / EVIDENCE / SECURITY -> DEVELOPMENT EXECUTION -> USER TEST -> RELEASE GATE -> POSTMORTEM.

The plan is a durable artifact. Repository state remains authoritative over chat memory.
