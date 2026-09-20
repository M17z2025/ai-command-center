# Global Sigma Development Directive

This directive applies to every managed development repository.

## Mandatory startup

Before development begins, the implementation agent must:

1. Read the Sigma Development Command Center at `M17z2025/ai-command-center`.
2. Read its `AGENTS.md`, `projects/registry.yaml`, development loop, handoff contract, security baseline and definition of done.
3. Read the local repository's `.sigma/project.yaml`, `PROJECT_STATUS.md`, `AGENTS.md`, README, architecture/deployment docs, open issues/PRs, recent commits and relevant tests.
4. Establish current state from repository evidence, not chat memory.
5. Work from the highest-priority executable Sigma order unless the product owner explicitly overrides priority.

## Sigma order cycle

Sigma should continually:
- inspect project status, issues, PRs, CI and recent commits;
- identify the highest-value executable next task;
- create or update a GitHub issue containing objective, acceptance criteria, constraints, security notes and verification requirements;
- mark blocked work only when owner/external input is truly required;
- review implementation output and issue READY / CHANGES REQUIRED / BLOCKED;
- keep `PROJECT_STATUS.md` current;
- move to the next executable task after completion.

## Development-agent obligation

Implementation agents should:
- execute Sigma orders from GitHub;
- create branches/commits/PRs as appropriate;
- test and security-review the work;
- update durable GitHub state;
- never depend on an open chat as the sole record of work.

## Cross-chat rule

Any new ChatGPT development chat should begin by reading Sigma and the product repository. Old chat history is supplementary only.

## Production boundary

Sigma may continuously prepare, test, review and queue code changes. Destructive production actions, secret provisioning, irreversible migrations and other high-risk changes require the applicable approval gate.
