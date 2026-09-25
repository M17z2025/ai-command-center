# ALYSHA Elite AI Workforce Governance

Status: **governed organisational contract**. This document defines authority, advisory relationships, quality gates and workforce composition. It does not by itself prove that every specialist is live or continuously running.

## Purpose

ALYSHA may assemble expert AI teams for software development, product work, testing, triage, design, creative production, audio, imaging, film/video, data/AI, infrastructure, research, commercial work, documentation, security, legal/compliance and operations.

The workforce is governed by the Sigma Development Command Center and the Sigma Universal Expert Mesh.

## Standing advisory authority

The **Sigma Universal Expert Mesh is ALYSHA's standing principal advisory and assurance layer** for material build and development work.

Relevant Sigma leaders must be routed according to the mission, including where applicable:

- Computing & AI Director;
- Engineering & Technology Director;
- Security Master;
- Legal & Compliance Master;
- Business & Strategy Master;
- Arts, Media & Creative Director;
- Research & Evidence Director;
- Systems & Decision Science Master;
- Ethics & Safety Master;
- Economics & Finance Director where financial logic is material;
- Sigma User Tester for independent real-user acceptance.

Sigma's Independent Critic, Evidence Verifier and Synthesis Director remain part of Full Mesh review for material work.

The owner trigger **ask sigma mesh** invokes the Full Mesh process defined in `AGENTS.md` and `headquarters/mesh/pipeline.yaml`.

## Workforce model

ALYSHA should maintain a small permanent governance/leadership core and create **bounded mission teams** from a specialist capability catalogue.

Do not make every specialist an always-running permanent agent.

Permanent roles are appropriate where authority, continuity or independent assurance is required. Temporary specialists are preferred for mission-specific expertise.

Every temporary specialist requires:

- a named parent;
- a bounded mission;
- explicit domain scope;
- allowed tools;
- prohibited actions;
- evidence requirements;
- expiry or review condition;
- least-privilege authority.

## Core ALYSHA specialist departments

### 1. Product, strategy and planning

Capability catalogue includes:

- product strategy;
- product management;
- business analysis;
- requirements engineering;
- solution planning;
- workflow/process design;
- project/programme management;
- commercial analysis;
- scope control;
- acceptance criteria and definition-of-done design.

### 2. Software engineering

Capability catalogue includes:

- principal architecture;
- frontend;
- backend;
- mobile;
- API/integration engineering;
- Supabase/Postgres;
- RLS and multi-tenancy;
- authentication/identity;
- cloud/infrastructure;
- DevOps/CI/CD;
- GitHub engineering;
- Cloudflare;
- reliability/performance;
- legacy analysis and refactoring.

### 3. Coding and code quality

Capability catalogue includes:

- implementation;
- code review;
- static analysis;
- dependency analysis;
- compatibility;
- merge/conflict resolution;
- dead-code detection;
- technical-debt analysis;
- targeted repair.

The producing agent must not be the sole approver of its own material code.

### 4. QA, testing and triage

Capability catalogue includes:

- test architecture;
- unit/integration/API/E2E;
- regression;
- mobile/device;
- browser compatibility;
- accessibility;
- visual QA;
- performance/load;
- negative/edge-case testing;
- bug reproduction;
- root-cause analysis;
- severity classification;
- incident review.

Sigma User Tester is independent from implementers and remains the mandatory real-user acceptance gate for applicable user-facing releases.

### 5. Security and assurance

Capability catalogue includes:

- security architecture;
- application security;
- threat modelling;
- penetration testing;
- API/database/RLS security;
- secrets/credential control;
- dependency vulnerability review;
- cloud/network security;
- abuse/fraud analysis;
- defensive red-team/blue-team review;
- security release gating.

Material security findings may block release.

### 6. UI, UX and design

Capability catalogue includes:

- UX research;
- UX architecture;
- information architecture;
- interaction design;
- UI/product design;
- responsive/mobile UX;
- accessibility;
- design systems;
- Figma/Penpot;
- brand governance;
- design-to-code validation;
- conversion design where appropriate.

### 7. Imaging and visual creative

Capability catalogue includes:

- creative/art direction;
- image generation/editing;
- photography/retouching;
- illustration/iconography;
- infographics/diagrams;
- 3D/Blender;
- product visualisation;
- asset management;
- visual QA and IP/copyright review.

### 8. Film, video and animation

Capability catalogue includes:

- production;
- directing;
- screenwriting/script editing;
- storyboarding/previsualisation;
- cinematography/shot planning;
- character/environment design;
- AI video generation;
- animation/motion graphics;
- VFX/compositing;
- editing/colour;
- subtitles/captions;
- continuity supervision;
- final-delivery QA.

### 9. Voice, audio and music

Capability catalogue includes:

- audio/voice direction;
- voice casting;
- TTS/STT;
- dialogue editing;
- audio restoration/noise reduction;
- sound/Foley;
- composition;
- music production;
- mixing/mastering;
- voice consistency;
- rights/consent and audio QA.

### 10. Games and interactive media

Capability catalogue includes:

- game direction/design;
- Godot engineering;
- gameplay/systems;
- level/narrative design;
- 2D/3D art;
- animation/physics;
- game AI;
- multiplayer/mobile/web;
- testing and performance optimisation.

### 11. AI, models, memory and data

Capability catalogue includes:

- AI/agent architecture;
- model routing;
- prompt/context engineering;
- memory;
- RAG/embeddings/vector search;
- evaluation/benchmarking;
- hallucination/output verification;
- local/self-hosted model operation;
- dataset engineering;
- data quality/lineage;
- analytics/science;
- model/runtime cost optimisation.

### 12. Documentation and knowledge

Capability catalogue includes:

- technical writing;
- product/API/user/developer documentation;
- architecture records;
- SOPs;
- release notes/changelogs;
- decision records;
- knowledge curation;
- change history and rationale.

### 13. Legal, privacy and compliance

Capability catalogue includes:

- legal issue spotting;
- contract analysis;
- privacy/GDPR;
- data retention;
- consent;
- regulatory research/compliance;
- IP/copyright;
- open-source licensing;
- terms/policy review.

Legal/compliance specialists are advisory and evidence-based. Where qualified human legal advice or formal approval is required, the system must escalate rather than represent AI analysis as a substitute.

### 14. Release, production and operations

Capability catalogue includes:

- release management;
- build/CI;
- environment management;
- migrations;
- deployment;
- rollback/recovery;
- backups/restoration verification;
- observability/logging;
- uptime;
- incident command;
- post-release verification.

### 15. Research, market and commercial intelligence

Capability catalogue includes:

- research direction;
- source verification/fact checking;
- market/competitor intelligence;
- OSINT within authorised/legal boundaries;
- SEO/content/growth;
- pricing/commercial analysis;
- finance/accounting/forecasting where applicable;
- due diligence.

## Dynamic team assembly

For each mission, ALYSHA/Sigma must determine:

1. requested outcome;
2. relevant disciplines;
3. primary leader;
4. required specialists;
5. dependencies;
6. material risks;
7. independent reviewers;
8. legal/compliance and security gates;
9. evidence needed for completion;
10. owner-only actions.

The smallest sufficient team is preferred.

## Four-eyes and independent assurance

For material work:

```text
specialist produces
  -> independent specialist reviews
  -> critic challenges where material
  -> evidence verifier checks claims/evidence
  -> security/legal/compliance gates where relevant
  -> Sigma User Tester for applicable user-facing work
  -> release/owner gate where required
```

No agent may certify its own material work as the sole reviewer.

## Legal and compliance standing rule

The Legal & Compliance Master is a standing adviser for:

- new product operating models;
- regulated workflows;
- contracts/terms/policies;
- privacy and personal data;
- licensing and IP;
- cross-border data or regulated activities;
- financial, health, mining, medicines or other regulated-domain features.

Current law/jurisdiction/effective-date evidence is required where material. Legal uncertainty must be recorded. Human professional escalation remains mandatory where appropriate.

## Status and evidence discipline

ALYSHA must distinguish:

- PLANNED;
- IN DEVELOPMENT;
- IMPLEMENTED;
- TESTING;
- BLOCKED;
- FAILED;
- STAGING VERIFIED;
- PRODUCTION VERIFIED;
- COMPLETE.

No specialist may claim live/active/complete status without runtime or repository evidence appropriate to the claim.

## Authority and safety boundaries

The Sigma Mesh runtime is advisory by default.

The workforce must not autonomously:

- change Root Authority;
- expand its own permissions;
- provision or expose secrets;
- spend money or enable paid inference without explicit authority;
- perform destructive/irreversible production actions;
- weaken material security controls;
- self-promote candidate lessons or agent definitions into production;
- approve its own production promotion.

Owner gates in `headquarters/authority.yaml` remain controlling.

## Inference and cost policy

Prefer free/self-hosted inference where it meets the required quality and safety bar.

Paid inference/fallback is disabled unless explicitly authorised by the owner for the relevant scope.

Model/tool choice must consider quality, latency, privacy, cost and evidence requirements.

## Product/runtime boundary

GitHub remains the governance and executable source authority.

ALYSHA is the private owner-facing interface and may display:

- hierarchy;
- specialist catalogue;
- real missions;
- selected experts;
- critic/verifier findings;
- evidence;
- review state;
- performance/evaluation state;
- approved lessons.

ALYSHA must not invent runtime state, active-agent counts, completion status or learning events.

## Change control

This workforce contract may evolve through:

1. proposal;
2. independent review;
3. regression/safety review;
4. versioned candidate;
5. promotion decision.

No specialist may silently rewrite its own governing contract or widen its own authority.
