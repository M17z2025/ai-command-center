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
