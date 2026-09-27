# OpenHands Sigma Proof Runner

Issue: #59

## Purpose

Sigma uses OpenHands only as a bounded software-engineering worker. Sigma remains the governor, mission router, authority layer, security gate, independent reviewer and verifier.

The proof integration targets the OpenHands **Software Agent SDK** and its **DockerWorkspace**, not Agent Canvas as a second control plane.

## Upstream evidence

- OpenHands Software Agent SDK exposes Python/TypeScript/REST APIs for software-engineering agents.
- Upstream documents local or ephemeral Docker/Kubernetes workspaces.
- The official DockerWorkspace supports explicit volume mounts into the sandbox.
- OpenHands SDK is MIT licensed.
- OpenHands Agent Server supports optional API authentication and has telemetry disabled by default unless explicitly enabled.

## Sigma proof constraints

The runner:
- is disabled unless the parent OpenHands adapter is explicitly enabled;
- requires `sandbox_execution`;
- rejects production-release authority;
- rejects credentials during the initial proof phase;
- requires exactly one explicit filesystem scope;
- mounts only that path at `/workspace`;
- requires an explicitly pinned OpenHands agent-server image;
- refuses `:latest` images;
- requires a loopback/private inference endpoint;
- defaults the authorised model spend to zero;
- returns at most `CHANGED`, never `TESTED`, `VERIFIED` or `RELEASED`;
- requires Sigma to inspect the diff and independently run build/tests/security checks.

## Commissioning inputs (runtime only)

These are configuration inputs, not values to commit:
- pinned OpenHands agent-server image;
- local/private OpenAI-compatible inference base URL;
- model identifier;
- optional local endpoint API token if the endpoint requires one;
- disposable checked-out benchmark repository path.

No paid model/provider is authorised by this proof design.

## Benchmark sequence

1. Prepare a disposable repository with known failing tests and a bounded repair task.
2. Snapshot baseline commit and test output.
3. Run OpenHands in DockerWorkspace with only the benchmark repository mounted.
4. Capture wall time, reported model cost, OpenHands event count and resulting git diff.
5. Run tests independently outside the agent conversation.
6. Run Sigma security checks against the diff.
7. Record regressions and any repair actions required.
8. Compare with Sigma's existing worker path using the same task and acceptance criteria.
9. Do not promote OpenHands beyond proof status unless correctness and security hard gates pass.

## Current state

The adapter, SDK runner contract and benchmark data model exist in source. A real OpenHands execution is **NOT YET RUN** because the command-center runtime has no commissioned private inference endpoint/model configuration in repository-accessible evidence. That remains an owner-gated runtime commissioning dependency and must not be fabricated.
