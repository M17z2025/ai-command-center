# Sigma Open-Source Agent Integration Audit

Issue: #59
Status: Phase 1 architecture/licence audit
Date: 2026-09-27

## Decision

Sigma remains the governor, authority, evidence and orchestration control plane. Third-party agent systems are not adopted as a replacement runtime and are not described as AGI.

The preferred architecture is a governed worker/adaptor model:

```text
Sigma Governor / Mission Router / Authority
        |
        +-- Sigma native expert mesh
        |
        +-- governed worker adapter layer
              |
              +-- software-engineering worker
              +-- computer-use / GUI worker
              +-- long-horizon task worker
              +-- memory service
              +-- dynamic specialist-construction service
```

Every external worker receives a bounded mission, explicit tools, least privilege, timeout/budget, data classification, audit ID and required evidence. External workers cannot promote themselves, change Sigma authority, bypass the Security Gatekeeper, or mark their own work VERIFIED.

## Candidate decisions

### 1. Letta Code — ADAPT PATTERNS, DO NOT DELEGATE GOVERNANCE

Upstream: https://github.com/letta-ai/letta-code
Licence: Apache-2.0, verified from upstream LICENSE.

Useful capabilities:
- persistent agent identity and memory;
- memory blocks and context rewriting;
- MemFS/git-tracked context;
- project/agent skills;
- hooks and schedules;
- sub-agent invocation.

Sigma fit:
- strong reference implementation for persistent memory, episodic experience and skills;
- useful for Issue #53 knowledge/workforce infrastructure.

Hard boundary:
- upstream explicitly supports agents rewriting memory, skills, prompts and even harness behaviour.
- Sigma must NOT permit uncontrolled self-modification. Any learned change remains a CANDIDATE under headquarters/authority.yaml and headquarters/mesh/evolution.yaml until independently evaluated and promoted.

Integration mode:
- adapt memory/state/versioning concepts behind a Sigma-owned memory interface;
- do not make Letta the root orchestrator or authority service.

### 2. AOrchestra — ADAPT DYNAMIC WORKFORCE CONSTRUCTION

Upstream: https://github.com/FoundationAgents/AOrchestra
Licence: Apache-2.0, verified from upstream LICENSE.

Useful capabilities:
- dynamic creation/selection of specialised agents;
- task-specific context/instruction/tool composition;
- orchestrated specialist delegation.

Sigma fit:
- maps directly onto Mission Router + bounded temporary specialists;
- useful for capability-gap-driven workforce growth without predeclaring every possible specialist.

Hard boundary:
- generated specialists inherit Sigma authority and capability restrictions;
- a generated agent definition cannot grant itself tools, higher authority or persistence;
- every generated specialist must have parent, mission, expiry/review state, allowed tools and evidence requirements.

Integration mode:
- adapt specialist-construction patterns into Sigma's existing workforce compiler;
- do not run a second independent authority/orchestration hierarchy.

### 3. OpenHands — SIDE-CAR SOFTWARE ENGINEERING WORKER

Upstream: https://github.com/OpenHands/OpenHands
Licence: MIT, verified from upstream LICENSE.

Useful capabilities:
- repository-aware coding agent workflows;
- sandboxed software-development execution;
- software engineering task delegation;
- broad ecosystem and integration patterns.

Sigma fit:
- candidate execution worker for Sigma Algorithmic Engineering & Solution Lab and Engineering Support Desk;
- can reduce the need to build every coding-agent primitive inside sigma_runtime.

Hard boundary:
- Sigma remains responsible for issue selection, acceptance criteria, branch policy, independent review, security assurance and final verification;
- worker must operate in disposable/sandboxed environments with repository-scoped credentials.

Integration mode:
- side-car worker called through a Sigma adapter;
- first benchmark against existing Sigma/GitHub development workflow before portfolio-wide enablement.

### 4. Agent-S — SIDE-CAR COMPUTER-USE WORKER

Upstream: https://github.com/simular-ai/Agent-S
Licence: Apache-2.0, verified from upstream LICENSE.

Useful capabilities:
- GUI interaction using screen perception, clicking, typing and scrolling;
- Linux/macOS/Windows support;
- vLLM-compatible model path;
- explicit computer-use benchmark orientation.

Sigma fit:
- candidate exploratory/computer-use backend for Sigma User Tester where Playwright is insufficient;
- useful for applications whose critical journeys require real GUI interaction.

Security finding:
- upstream warns that optional local coding executes arbitrary Python/Bash with the privileges of the running user.
- this capability must be disabled by default and only enabled inside isolated disposable test environments.

Integration mode:
- isolated side-car only;
- never run with production host privileges;
- Playwright remains deterministic first-line web certification.

### 5. Deep Agents — ADAPT LONG-HORIZON EXECUTION PATTERNS

Upstream: https://github.com/langchain-ai/deepagents
Licence: MIT, verified from upstream LICENSE.

Useful capabilities:
- subagents with isolated contexts;
- filesystem backends;
- long-context management/offloading;
- shell/sandbox integration;
- persistent stores;
- human-in-the-loop tool approvals;
- skills and MCP tools;
- local/open-weight model compatibility including Ollama, vLLM and llama.cpp.

Sigma fit:
- strong reference for long-horizon mission execution and context control;
- may supply reusable worker primitives.

Security finding:
- upstream documents a "trust the LLM" model and says boundaries must be enforced at the tool/sandbox layer.
- Sigma therefore cannot expose unrestricted production tools to a Deep Agents worker.

Integration mode:
- adapt context/subagent/storage interfaces or run a bounded worker side-car;
- Sigma policy engine and capability firewall remain outside the worker.

### 6. Agent Zero — REFERENCE / OPTIONAL ISOLATED WORKER

Upstream: https://github.com/agent0ai/agent-zero
Licence: MIT, verified directly from upstream LICENSE. GitHub repository metadata currently reports NOASSERTION, so Sigma must rely on the checked LICENSE content and re-verify before adoption.

Useful capabilities:
- Dockerized Linux desktop;
- browser control and DOM annotation;
- project-isolated files/memory/secrets;
- multi-agent delegation;
- plugin, MCP and A2A extension points;
- host-machine bridge;
- snapshot/time-travel concepts.

Sigma fit:
- valuable reference for recoverable autonomous workspaces, tool/plugin surfaces and browser/desktop cowork;
- overlaps substantially with OpenHands + Agent-S + Sigma native orchestration.

Risk/complexity:
- broad plugin ecosystem, host bridge, browser, desktop and secret handling create a large attack surface;
- importing it wholesale would duplicate major Sigma responsibilities.

Integration mode:
- do not make it Sigma core;
- selectively reproduce/adapt workspace snapshot, project isolation and plugin-interface patterns, or evaluate it later as a sandboxed worker.

## Integration priority

1. Build Sigma Worker Adapter Contract and capability firewall.
2. Connect one software-engineering worker benchmark (OpenHands).
3. Add controlled persistent-memory interface using Letta-inspired versioned memory semantics.
4. Add dynamic specialist-construction improvements inspired by AOrchestra.
5. Add isolated Agent-S computer-use backend for exploratory Sigma User Tester.
6. Evaluate Deep Agents long-horizon/context primitives against Sigma native runtime.
7. Keep Agent Zero as reference/optional sandbox until overlap and attack surface justify it.

## Worker Adapter Contract

Every worker invocation must include:
- mission_id;
- parent Sigma agent;
- repository/project;
- exact objective and acceptance criteria;
- allowed tools/actions;
- prohibited actions;
- filesystem/repository scope;
- network scope;
- credential scope;
- model/provider;
- spend ceiling (zero unless separately authorised);
- wall-clock/task budget;
- data classification;
- evidence outputs;
- termination conditions.

Every worker result must return:
- status: PLANNED / RUNNING / CHANGED / TESTED / BLOCKED;
- changes made;
- commands/tests actually executed;
- evidence/artifact references;
- unresolved failures;
- security-sensitive actions attempted;
- exact next action.

A worker can never directly return VERIFIED or RELEASED. Those states require Sigma's independent gates.

## First implementation slice

Create a native `sigma_runtime/workers/` abstraction with:
- `WorkerAdapter` protocol/base class;
- `WorkerMission` and `WorkerResult` schemas;
- explicit capability allowlist/denylist;
- timeout and zero-spend defaults;
- audit-event persistence;
- deterministic test adapter;
- no external worker enabled by default.

Then implement a proof adapter for ONE candidate only, initially OpenHands, behind an opt-in configuration flag. Execute it only in an isolated test repository/container. Compare:
- task completion;
- correctness;
- regression rate;
- test evidence;
- token/model cost;
- wall time;
- security boundary violations;
- human/Sigma repair required.

Only after that benchmark should additional workers be commissioned.

## Security and supply-chain gates before executing upstream code

- pin commit/release;
- dependency lock/SBOM where practical;
- inspect install scripts, containerfiles and CI actions;
- secret scan;
- dependency vulnerability scan;
- run as non-root where possible;
- read-only root filesystem where practical;
- no host Docker socket;
- restricted network egress;
- ephemeral workspace;
- repository-scoped token with least privilege;
- no production credentials;
- explicit CPU/RAM/process/time limits;
- preserve stdout/stderr/tool/audit evidence;
- destroy test environment after evaluation.

## Relationship to current Sigma blockers

This work does not remove the current owner-gated requirement to commission the live private model endpoint/runtime.

It also does not substitute for the portfolio runner. The worker adapter layer is a reusable execution primitive that the runner can call once the runner is operational.

## Exit criteria for Issue #59 phase 1

- [x] Existing Sigma architecture and authority inspected.
- [x] Candidate upstream licences verified from source.
- [x] Integration modes assigned.
- [x] Security boundaries identified.
- [x] First implementation slice defined.
- [ ] Implement Worker Adapter Contract.
- [ ] Add deterministic adapter tests.
- [ ] Run exact-head Sigma validation.
- [ ] Add OpenHands sandbox proof adapter/benchmark.
- [ ] Independent Security Gatekeeper review.
