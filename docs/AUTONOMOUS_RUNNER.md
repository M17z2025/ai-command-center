# Autonomous Execution Runner

The command center stores state and rules. Continuous autonomous execution requires a separate runner.

## Target architecture

```
GitHub events / schedule
        |
        v
Sigma Orchestrator
        |
        +--> loads headquarters/mesh taxonomy + leaders + pipeline
        +--> routes each mission to one or more expert leaders
        +--> requires critic + verifier + synthesis for material work
        +--> reads projects/registry.yaml
        +--> reads product .sigma/project.yaml + PROJECT_STATUS.md
        +--> selects next executable issue
        +--> prepares implementation handoff
        |
        v
Implementation Agent
        |
        +--> branch
        +--> code
        +--> tests
        +--> PR
        |
        v
CI checks
        |
        v
Sigma Review
        |
        +--> READY -> merge/deploy policy
        +--> CHANGES REQUIRED -> repair loop
        +--> BLOCKED -> issue/comment for owner input
```

## Event sources

Recommended triggers:
- new/updated implementation issue;
- pull-request opened/updated;
- CI failure;
- scheduled portfolio review;
- explicit owner priority change.

## State

Durable state must live in GitHub:
- issues;
- PRs;
- commits;
- `PROJECT_STATUS.md`;
- `.sigma/project.yaml`;
- command-center registry.

The runner must not depend on one chat session remaining open.

## Permissions

Prefer least privilege:
- read all managed repositories;
- create branches, commits, issues and PRs;
- read CI results;
- no unrestricted production secrets;
- no direct force-push to protected main;
- no destructive production database action without an explicit approval gate.

## Work selection

A task is executable when:
- objective and acceptance criteria exist;
- repository is accessible;
- required non-secret context exists;
- no owner-only decision is outstanding;
- prerequisites are complete.

Prefer one coherent task per project at a time unless the tasks are independent.

## Failure handling

If build/tests fail, the runner should:
1. inspect failure evidence;
2. attempt a bounded repair;
3. update the PR;
4. rerun verification;
5. mark BLOCKED only when external input/access is actually required.

## Audit trail

Each run should record:
- trigger;
- project/task;
- input commit;
- actions taken;
- output branch/PR/issue;
- verification result;
- final state.

## Production boundary

Automatic code preparation and review can be continuous. Production deployment should follow each project's deployment policy and explicit approval requirements for high-risk systems.
## Current implementation — issue #62

The current-main runner lives in `sigma_runtime/portfolio_runner.py` with:
- GitHub evidence discovery over the canonical registry;
- contract/status/issue/PR/latest-commit inspection;
- deterministic priority selection that skips explicit owner/external blockers;
- mesh-runtime planning for the selected issue;
- private SQLite runner-cycle persistence;
- generic governed worker dispatch over `SIGMA_WORKER_ENDPOINT`;
- write authority disabled by default;
- branch + pull-request evidence required before a worker result is accepted as a repository change;
- no worker may promote its own output to VERIFIED or RELEASED.

The runtime HTTP service exposes:
- `GET /runner/cycles`
- `GET /runner/cycles/{id}`
- `POST /runner/cycle`

The always-on loop is `scripts/sigma_runner_daemon.py`. Its minimum interval is five minutes and the default is fifteen minutes.

### Authority switches

`SIGMA_RUNNER_ALLOW_WRITE=0` is the default. GitHub non-GET calls are refused before network access unless write mode is explicitly enabled and a runtime token exists.

`SIGMA_RUNNER_EXECUTE=0` is the default. The runner may discover and plan work without dispatching implementation. Execution requires a configured governed worker endpoint.

These switches do not grant production release, destructive action, paid spend, direct-main push or secret-management authority.

### Truth states

The runner separates:
- `PLANNED` — issue selected and mesh plan persisted;
- `BLOCKED` — required worker/access/gate is absent;
- `WORKER_CHANGED` — worker returned branch + PR evidence, but independent verification remains;
- READY/VERIFIED/RELEASED — never issued solely by the runner worker path.

A material user-facing candidate still requires the independent Sigma Full User Tester on the exact deployed candidate.


## Singleton lease and stale-cycle recovery

The portfolio runner now uses a durable SQLite singleton lease named `portfolio`.

Rules:
- only one runner cycle may hold the lease at a time;
- a second cycle records `SKIPPED` with the active lease evidence instead of starting another mission;
- active cycles write heartbeats;
- `SIGMA_RUNNER_LEASE_TTL_SECONDS` controls lease expiry;
- `SIGMA_RUNNER_STALE_AFTER_SECONDS` controls stale RUNNING-cycle detection;
- stale cycles become `STALE` and remain in the audit history;
- stale lease ownership is released so later work can continue;
- leases are released in a `finally` path after success or failure.

Operational status is available at:

`GET /runner/status`

The response includes the current active lease, per-status cycle counts, and recent cycle records.
