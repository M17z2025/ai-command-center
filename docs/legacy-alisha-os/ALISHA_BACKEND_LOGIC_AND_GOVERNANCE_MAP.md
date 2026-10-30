# ALISHA Backend Logic and Governance Map

Generated: 2026-08-15

## Objective

ALISHA is a private, invite-only AI development and operating platform for the Mi7z group initially, with a future path to commercial offering after the platform is proven. Every capability must therefore be selected and operated as though future commercialisation is possible.

## Global rule

A component is not approved merely because it is free today. Before production use, ALISHA must verify:

1. software licence and redistribution rights;
2. model/checkpoint licence and commercial-use rights;
3. dataset/data-source terms, attribution and redistribution rights;
4. privacy/data-processing implications;
5. security posture and supply-chain provenance;
6. operational dependency, including whether a supposedly free hosted service could disappear or change terms;
7. an internal fallback or replacement path where the component is business-critical.

Commercial products must never depend solely on an external free tier.

## Request-to-stack routing

Every request enters the ALISHA Orchestrator and is classified before tools are invoked.

### 1. Identify domain

Examples: web app, mobile app, game, document, finance, FX, commodity, recipe, architecture/BIM, movie, image, video, voice, biometrics, 3D/volumetric, research, automation, analytics, email, chat.

### 2. Determine risk class

- Low: drafting, ideation, non-sensitive transformation.
- Medium: external research, web automation, generated code, customer-facing content.
- High: finance, legal/compliance, biometrics, authentication, regulated data, production deployment, contractual pricing, irreversible external actions.

High-risk flows require stronger evidence, logging and approval gates.

### 3. Select data source before model

For data-dependent tasks ALISHA must identify the authoritative or approved source first. Models may interpret data but must not invent live prices, rates, regulations, identities or measurements.

### 4. Select local vs external model

Default routing order:

- local/Ollama or approved local specialist model when quality is sufficient;
- approved external frontier model when quality/complexity requires it;
- specialist tools for deterministic operations;
- no unofficial mirrors of proprietary paid models.

### 5. Execute in isolated capability adapter

Each third-party component is accessed behind an ALISHA adapter. Third-party code does not become the system of record.

### 6. Validate result

Use deterministic validation, Promptfoo/evals, schema checks, source verification, security scanning, or specialist review depending on the domain.

### 7. Log and persist

Persist source, tool/model, version, prompt/version, timestamps, provenance, approvals and output references appropriate to the task.

## Domain map

### Web applications

Primary stack: Next.js + TypeScript + Supabase/Postgres + Cloudflare + GitHub.

ALISHA uses OpenHands for coding work, Promptfoo for AI behaviour tests, GitHub Actions for build/test/security gates, and Browser Use/Maestro where end-to-end testing is required.

### Mobile applications

- React Native + Expo for native-first mobile applications.
- Capacitor when an existing web product can safely be packaged with native-device bridges.
- Maestro for mobile UI testing.
- Native OS biometric APIs are preferred for phone authentication.

### Games

Godot is the primary game engine. Blender, Material Maker, Pixelorama, LDtk, TrenchBroom, Jolt/Box2D, ENet and Nakama provide asset, level, physics, networking and multiplayer capability.

### AI reasoning / brain

Primary memory and reasoning layer:

Postgres/pgvector + Mem0 + GraphRAG + DSPy + Langfuse + Promptfoo.

Qdrant remains a scale-up option only if measured retrieval scale/latency justifies another vector system.

### Prompt engineering

Prompt creation follows:

brief -> base prompt -> PromptWizard/DSPy optimisation -> Promptfoo evaluation/red-team -> Langfuse evidence -> approved version registry -> deployment.

Prompts must have an owner, purpose, allowed tools, prohibited actions, response schema, risk class and evaluation criteria.

### Currency and FX

Primary reference-rate source: Frankfurter/self-hosted adapter using central-bank and monetary-authority reference data.

Requirements:

- distinguish reference FX from executable/trading quotes;
- persist provider/source, currency pair, observation time, retrieval time and stale state;
- cache historical series;
- do not use an unapproved free market feed as contractual settlement data.

### Commodities

Historical baseline: World Bank commodity/Pink Sheet connector where appropriate.

Current/reference data: approved public-source adapters. Stooq/croncopia may be evaluated as pilot/reference sources but cannot become commercial dependencies until their data terms/provenance are explicitly approved.

Every commodity observation stores instrument, market/source, unit, currency, observed_at, retrieved_at and stale/indicative flags.

For gold, copper or other contract calculations, ALISHA must use the explicitly approved benchmark defined by that product's governance policy rather than silently substituting a free indicative feed.

### Finance / market analysis

ALISHA can calculate, chart, compare and analyse approved historical/reference data. Trading, execution, regulated advice or money movement are separate capabilities and are not implicitly enabled by adding market data.

### Recipes

Mealie provides self-hosted recipe storage, planning and REST integration. Crawl4AI can discover/import permitted recipe pages. ALISHA normalises ingredients and units and can generate variations, scaling and meal plans.

Governance:

- preserve original source URL/attribution;
- do not republish copyrighted editorial copy or images beyond permitted use;
- label AI-modified recipes;
- food-allergy and medical dietary claims require caution and explicit user-supplied restrictions.

### House / architecture / BIM

Core stack: FreeCAD + IfcOpenShell + Bonsai + Blender + Three.js + ComfyUI.

ALISHA workflow:

requirements -> dimensions/site constraints -> concept layouts -> parametric CAD/BIM -> IFC data -> clash/validation checks -> 2D plans -> 3D visualisation/render -> export.

ALISHA may automate modelling, but conceptual output must not be represented as architect/engineer-approved construction documentation without professional review and jurisdiction-specific planning/building/structural/fire/accessibility checks.

### Voice, facial recognition and biometrics

faster-whisper handles speech-to-text; pyannote/sherpa-onnx handle speaker analysis/verification; CompreFace/DeepFace handle face recognition/verification.

Biometric matches alone cannot approve high-risk actions. Explicit enrolment, liveness/anti-spoofing, encryption, retention/deletion and consent rules apply.

### Movie / animation / media

ComfyUI + LTX/Wan/AnimateDiff + KupkaProd/OpenMontage + Blender + FFmpeg + ACE-Step + Kokoro/Chatterbox + restoration tools. Heavy inference/rendering runs on RunPod workers. Each model/checkpoint must be commercially approved separately.

### 3D / volumetric / holographic

Nerfstudio + gsplat + Blender for reconstruction/content; Three.js/WebXR for browser delivery. Assets should use approved geometry/texture compression before CDN delivery.

### ALISHA Chat

LibreChat is approved as the open-source self-hosted chat shell/reference because it is MIT licensed and supports local and external model endpoints, agents, MCP and multi-user authentication.

ALISHA Chat must remain a separate intelligence layer from the UI shell:

User -> invite/auth -> RBAC/capability policy -> ALISHA Orchestrator -> memory/RAG -> model router -> tools -> validators -> audit -> response.

The UI can be replaced or fully reimplemented later without changing ALISHA's brain, governance or tool adapters.

## Invite-only access model

Initial access is invitation-only. Roles should include at minimum:

- Owner/Master;
- Platform Administrator;
- Developer/Builder;
- Reviewer/Approver;
- Business User;
- Read-only/Auditor;
- Specialist roles as required by domain.

Every tool is permission-scoped. Authentication does not automatically grant permission to deploy, send bulk communications, access biometric data, use regulated data, or perform production-changing actions.

## Backend control-plane map

```text
ALISHA CHAT / WEB / MOBILE
          |
          v
AUTH + INVITE + RBAC
          |
          v
ALISHA ORCHESTRATOR
  |       |        |        |
  |       |        |        +--> Governance / approval engine
  |       |        +-----------> Memory / GraphRAG / pgvector / Mem0
  |       +--------------------> Model router (Ollama / external models)
  +----------------------------> Capability router
                                   |
      -----------------------------------------------------------------
      |        |        |       |        |       |       |            |
     DEV     DATA     DOCS    MEDIA    VOICE    GAME   MOBILE      ARCH/BIM
      |        |        |       |        |       |       |            |
 OpenHands  FX/Commod Docling ComfyUI Whisper Godot RN/Expo FreeCAD/IFC
 GitHub     adapters   OCR    Blender  TTS     Nakama Maestro  Bonsai
      |        |        |       |        |       |       |            |
      -----------------------------------------------------------------
                                   |
                              VALIDATION
                                   |
                      Promptfoo / schemas / security
                                   |
                              AUDIT / LANGFUSE
                                   |
                       STORAGE / OUTPUT / DELIVERY
```

## Deployment placement

Normal application/CPU infrastructure:

- ALISHA web/chat/control plane;
- authentication/RBAC;
- Supabase/Postgres/pgvector;
- Mem0 service layer;
- Langfuse;
- n8n;
- Plausible;
- listmonk;
- Mealie;
- Frankfurter;
- data-source cache/adapters;
- Crawl4AI;
- LibreChat/ALISHA Chat shell;
- governance and capability registry.

RunPod/GPU workers when required:

- local larger LLMs/Ollama/vLLM;
- ComfyUI/video models;
- speech/TTS acceleration;
- Blender rendering;
- Nerfstudio/gsplat;
- AI movie/animation workers;
- other approved GPU-heavy models.

## Commercialisation gate

Before ALISHA is offered commercially, perform a complete dependency audit covering licences, model rights, data redistribution, trademark/branding, privacy terms, open-source notice obligations, hosted-service dependencies and support/security lifecycle. A component marked internal/pilot/reference must not automatically graduate into the commercial product.
