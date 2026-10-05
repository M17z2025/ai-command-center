# Sigma Critical awesome-ai-apps Integration

## Decision

Sigma adopts the **critical execution patterns** from
`Arindam200/awesome-ai-apps` as Sigma-owned controls. It does **not** install
the upstream examples as independent authorities, and it does not add Nebius,
E2B or other paid-provider dependencies.

Upstream evidence inspected from commit:
`276e635f3f2bf3212359d37709f09d1fab6ba313`.

Relevant upstream examples:

1. `advance_ai_agents/coding_agent_harness`
2. `starter_ai_agents/coding_harness_starter`
3. `advance_ai_agents/coding_harness_agent`
4. `mcp_ai_agents/e2b_docker_mcp_agent`
5. `mcp_ai_agents/github_mcp_agent`

The upstream repository is MIT licensed. Sigma adapts the architecture and
safety patterns; no paid provider is required for this implementation.

## Sigma mapping

| Upstream critical pattern | Sigma implementation |
| --- | --- |
| Multi-Agent Coding Harness | Sigma orchestrator creates the plan/mission; the bounded coding worker executes; the delivery supervisor owns test/repair/CI/merge progression. |
| Coding Harness Starter | Locked checkout, bounded repository context, mechanical path validation, deterministic manifest verification, bounded repair loop. |
| Local File-Editing Agent | OpenHands LocalWorkspace remains the editing engine, but changed files are mechanically validated before verification or GitHub write. |
| Sandboxed Code Execution MCP Agent | Sigma retains its private Docker worker and wrapper-owned verification; E2B is not required. |
| GitHub MCP Agent | Sigma's trusted GitHub control-plane client owns remote repository intelligence and mutations; the coding-model prompt receives bounded checkout context and the Sigma mission rather than a GitHub token. |

## Execution contract

The worker now receives an explicit five-stage contract:

`PLAN -> INSPECT -> EDIT -> SELF-REVIEW -> HANDOFF`

The model may edit only the mission checkout. The wrapper independently:

1. builds bounded context from the repository;
2. rejects absolute/traversal/symlink/sensitive/generated paths;
3. captures the exact model change set;
4. runs manifest-declared verification commands;
5. rejects verification that mutates additional tracked source;
6. stages only the previously validated model change set;
7. leaves PR/CI/security/merge/release authority with Sigma.

## Sensitive path policy

The harness rejects:

- absolute paths and `..` traversal;
- VCS internals such as `.git`;
- dependency/generated trees such as `node_modules`, `.venv`, `.next`,
  `dist`, `build` and coverage/cache directories;
- real `.env*` files while permitting template/example files;
- common private-key and credential material;
- symlink targets and paths resolving outside the locked checkout.

## Verification

Required evidence before this integration is classified VERIFIED:

- new deterministic harness unit tests pass;
- existing Sigma worker tests pass;
- full control-plane validation passes on the exact PR head;
- worker Docker image builds with the harness module;
- GitHub-hosted autonomous proof reaches `DONE`;
- self-hosted commissioning can consume the merged worker source without
  weakening existing owner/spend/production gates.

## Authority boundary

This integration does not grant the coding worker production release, secret
management, repository-admin, paid-spend or direct-main-push authority.
Worker output remains untrusted until Sigma's independent gates complete.
