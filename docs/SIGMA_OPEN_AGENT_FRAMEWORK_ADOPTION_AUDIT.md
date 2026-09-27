# Sigma Open-Source General-Agent Framework Adoption Audit

Issue: #57  
Audit date: 2026-09-27  
Scope: source-level adoption review for Sigma; this document does **not** claim that any reviewed project is AGI.

## Executive decision

Sigma should **not replace its governor, mission router, critic, evidence verifier, security gatekeeper, authority model, or repository truth model with a third-party agent framework**.

The strongest architecture is:

1. **Sigma remains the authority/orchestration control plane.**
2. Add a versioned `WorkerAdapter` boundary for external execution engines.
3. Use **Deep Agents** as the first reusable execution-harness candidate behind that boundary.
4. Use **OpenHands Agent Server/SDK** as the primary isolated software-engineering worker.
5. Use **Agent-S** only for native/desktop GUI journeys that Playwright/browser testing cannot cover.
6. Reuse **Letta Code** memory concepts selectively; do not make its cloud-coupled product surface the Sigma memory authority.
7. Reuse **AOrchestra** dynamic-delegation ideas; do not make its benchmark-oriented runtime a Sigma dependency.
8. Keep **Agent Zero** available as an isolated general-purpose worker/reference implementation, not as Sigma root authority.

All side-effecting foreign workers must run in disposable/restricted containers or equivalent sandboxes. No reviewed framework may receive implicit access to the Sigma host, owner secrets, production credentials or unrestricted portfolio repositories.

## Evidence summary

| Candidate | Verified licence | Activity observed | Sigma classification | Adopted role |
| --- | --- | --- | --- | --- |
| agent0ai/agent-zero | MIT from repository `LICENSE` (GitHub metadata incorrectly reports NOASSERTION) | pushed 2026-09-23 | ACCEPT | isolated general-purpose worker / implementation reference |
| letta-ai/letta-code | Apache-2.0 | pushed 2026-09-27 | FORK_CANDIDATE | memory/identity/experience design source; optional local worker later |
| FoundationAgents/AOrchestra | Apache-2.0 | pushed 2026-05-25 | FORK_CANDIDATE | dynamic delegation/team-construction design source |
| OpenHands/OpenHands + software-agent-sdk + automation | MIT across reviewed repositories | pushed through 2026-09-27 | ACCEPT | sandboxed software-engineering worker |
| simular-ai/Agent-S | Apache-2.0 | pushed 2026-09-05 | FORK_CANDIDATE | isolated native/desktop GUI worker |
| langchain-ai/deepagents | MIT | pushed 2026-09-26 | ACCEPT | first execution-harness candidate behind Sigma adapter |

Classification follows `headquarters/scouter/policy.yaml`. ACCEPT means the open code and licence satisfy the current Scouter admission rules for the stated use; it is not a security certification or an instruction to deploy without review.

## Candidate findings

### 1. Deep Agents — first execution-harness candidate

Upstream: https://github.com/langchain-ai/deepagents

Why it fits:
- Python, matching the current Sigma runtime.
- `create_deep_agent()` composes model, tools, middleware, subagents, backends, memory, permissions and persistence.
- LangGraph provides resumability/checkpoints while backends own files/memory/shell execution.
- Current source contains explicit filesystem permission controls and separate threat models.
- The codebase distinguishes safe backend capability from tool visibility rather than assuming that a visible tool is authorised.
- It supports durable sessions and a headless coding-agent reference implementation.

Important boundary:
- `LocalShellBackend` is not a security sandbox. Sigma must not expose it to untrusted workloads.
- Deep Agents remains an execution harness. Sigma governance remains above it.

Sigma integration:
```
Sigma Mission
  -> Sigma routing / authority / evidence gates
  -> WorkerAdapter
  -> DeepAgentsWorker
  -> sandbox backend
  -> model endpoint (self-hosted first)
  -> structured WorkerResult
  -> Sigma critic / verifier / security gates
```

### 2. OpenHands — software-engineering worker

Upstreams:
- https://github.com/OpenHands/OpenHands
- https://github.com/OpenHands/software-agent-sdk
- https://github.com/OpenHands/automation

Findings:
- The modern OpenHands repository is primarily Agent Canvas/control UI.
- Agent execution is owned by the separate OpenHands Agent Server / software-agent-sdk.
- The SDK and automation repositories reviewed are also MIT licensed.
- OpenHands can self-host Agent Server backends and can bring a model endpoint.
- Upstream explicitly warns that direct host operation gives the agent full filesystem access and recommends sandboxed operation.

Sigma integration:
- Do not fork the Canvas as Sigma's core.
- Integrate the Agent Server/SDK behind `WorkerAdapter`.
- Allocate one restricted workspace/repository per job.
- Capture event stream, patch/diff, commands, tests and final output as Sigma evidence.
- Deny production credentials and owner-held secrets.
- Require Sigma independent code review/security/User Tester after the worker's changes.

### 3. Agent Zero — general-purpose worker/reference

Upstream: https://github.com/agent0ai/agent-zero

Findings:
- Repository `LICENSE` is MIT even though GitHub metadata currently reports NOASSERTION.
- Python runtime with subagents, plugin loading, project-scoped agents, browser/code execution, scheduler and tool-policy components.
- Current dependency file includes explicit security-floor pins for several known vulnerable dependency families.
- Architecture is broad and powerful, which also creates a large capability/security surface.

Sigma integration:
- Keep as an optional isolated worker for research/general-computer tasks.
- Reuse plugin/subagent/tool-policy patterns where superior to Sigma's implementation.
- Never promote Agent Zero's internal hierarchy above Sigma authority.
- Never expose its code-execution/browser capabilities on the Sigma control host.

### 4. Letta Code — persistent-memory design source

Upstream: https://github.com/letta-ai/letta-code

Findings:
- Apache-2.0, actively developed TypeScript codebase.
- Strong concepts for long-lived identity, recall, memory blocks, skills, subagents, schedules and context stored in a git-backed memory filesystem.
- Local backend operation is supported.
- Some product capabilities, including remote computers and managed secrets, explicitly require signing in with Letta.
- Cloud is a product path; Sigma should not make cloud identity or paid services a prerequisite.

Sigma integration:
- Port/adapt the useful memory semantics into Sigma's private knowledge/workforce infrastructure:
  - immutable experience/recall history;
  - mutable versioned memory blocks;
  - skill memory;
  - periodic reflection/dreaming as candidate lessons;
  - provenance and rollback.
- Do not allow agents to self-promote memory changes directly into governance. Existing Sigma candidate/evaluation/promotion controls remain mandatory.

### 5. AOrchestra — dynamic delegation design source

Upstream: https://github.com/FoundationAgents/AOrchestra

Findings:
- Apache-2.0.
- Main agent dynamically delegates tasks to subagents and can choose from multiple models.
- Source contains benchmark-oriented implementations for GAIA/SWE-bench/TerminalBench and explicit hosted-model pricing tables.
- Considerably smaller and less recently updated than the other primary candidates.

Sigma integration:
- Reuse the delegation concept: construct a task-specific specialist with bounded instructions, tools and model choice.
- Do not import AOrchestra as Sigma's root runtime.
- Port ideas into Sigma's existing Mission Router / temporary-specialist model so authority, audit and evidence rules remain intact.

### 6. Agent-S — native GUI worker

Upstream: https://github.com/simular-ai/Agent-S

Findings:
- Apache-2.0.
- Agent-S3 is a comparatively simple worker + grounding-agent structure.
- It can target configurable model/base URLs.
- Its optional local environment executes arbitrary Python and Bash; upstream explicitly warns about this.

Sigma integration:
- Do not replace Sigma User Tester's Playwright-first web testing.
- Add only as an isolated native/desktop GUI worker for journeys that require operating-system GUI interaction.
- Disable local code execution by default.
- Run in disposable VM/container/desktop test environments with no production secrets.

## Required Sigma interfaces

### WorkerAdapter

Every external engine must conform to a Sigma-owned contract rather than leaking framework-specific state into governance.

Minimum request:
```python
WorkerRequest(
    mission_id,
    task_id,
    worker_type,
    repository,
    base_commit,
    workspace_policy,
    allowed_tools,
    evidence_inputs,
    model_policy,
    timeout_seconds,
)
```

Minimum result:
```python
WorkerResult(
    status,
    summary,
    actions,
    artifacts,
    patches,
    commands,
    tests,
    citations,
    warnings,
    security_events,
    usage,
)
```

The adapter must not accept an external framework's claim of "success" as Sigma completion evidence.

### Capability policy

Each worker receives an explicit capability manifest:
- allowed repository/workspace;
- allowed network destinations;
- allowed tools;
- read/write boundaries;
- shell policy;
- model endpoint;
- time/resource budget;
- secret handles, normally none;
- prohibited production/financial/destructive actions.

Unknown capability = deny.

### Sandbox policy

Foreign agent execution must be separated from the Sigma control process.

Minimum initial policy:
- disposable container or dedicated VM;
- non-root user;
- one mounted job workspace;
- no Docker socket;
- no host home directory;
- no SSH agent forwarding;
- no production environment files;
- outbound network allow-list where practical;
- CPU/RAM/time/process limits;
- command/event audit capture;
- workspace destruction or quarantine after evidence extraction.

## Overlap and de-duplication

Do **not** run six overlapping orchestration systems.

| Sigma capability | Owner |
| --- | --- |
| Authority / owner gates | Sigma only |
| Mission routing | Sigma only |
| Expert taxonomy | Sigma only |
| Critic / evidence verifier | Sigma only |
| Security gate | Sigma only |
| Portfolio truth / GitHub state | Sigma only |
| General execution harness | Deep Agents candidate |
| Coding execution | OpenHands worker |
| General computer/research worker | Agent Zero optional |
| Native desktop GUI | Agent-S optional |
| Persistent-memory design patterns | Letta-derived, Sigma-owned implementation |
| Dynamic specialist/delegation patterns | AOrchestra-derived, Sigma-owned implementation |

## First implementation slice

The next code change should be deliberately small and testable:

1. Add `sigma_runtime/workers/base.py` containing `WorkerRequest`, `WorkerResult` and the `WorkerAdapter` protocol.
2. Add a deterministic `TestWorkerAdapter` for CI.
3. Add a capability-policy validator that fails closed on undeclared tools/workspaces/network/secret access.
4. Add an adapter registry that does not instantiate any third-party worker unless explicitly enabled.
5. Add structured worker events/artifacts to the existing SQLite audit trail.
6. Add unit tests proving:
   - unknown worker types are denied;
   - undeclared capabilities are denied;
   - a worker cannot mark a Sigma mission complete;
   - worker output is treated as untrusted evidence;
   - the deterministic adapter produces auditable results;
   - current Sigma routing/critic/verifier behavior remains unchanged.
7. Only after this interface passes CI, implement a sandboxed Deep Agents proof adapter.
8. Then implement OpenHands Agent Server as the first real code worker.
9. Agent-S and Agent Zero remain later optional adapters.
10. Letta/AOrchestra begin as pattern ports, not runtime dependencies.

## Model policy

No reviewed repository supplies AGI by itself. Model inference remains a separate dependency.

Sigma policy remains:
- self-hosted/open-weight inference first;
- Ollama for simple local serving;
- vLLM for higher-concurrency GPU serving;
- llama.cpp where portability/CPU/edge use matters;
- model-weight licences verified separately;
- no paid inference commitment without owner approval.

## Security gate before first live foreign worker

Before enabling a real external worker:
- dependency/SBOM scan;
- container/base-image review;
- prompt/tool-injection tests;
- command and filesystem escape tests;
- network egress tests;
- secret-exfiltration tests;
- malicious repository-content tests;
- resource-exhaustion tests;
- audit completeness tests;
- independent Sigma Security Gatekeeper review.

## Conclusion

There is no verified open-source AGI in this audit. The useful path is to make Sigma a stronger governed general-purpose autonomous system by composing proven open-source execution components behind Sigma-owned contracts.

The immediate engineering move is **WorkerAdapter + capability/sandbox policy**, followed by a **Deep Agents proof adapter** and then a **sandboxed OpenHands coding worker**.
