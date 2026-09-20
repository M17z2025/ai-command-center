# Sigma → ChatGPT Handoff Contract

Sigma should hand work to ChatGPT in a form that can be executed without reconstructing context.

## Minimum handoff

Every handoff must specify:

1. **Repository** — exact `owner/repo`.
2. **Objective** — measurable result, not “continue development”.
3. **Current state** — what already works and what is broken/missing.
4. **Acceptance criteria** — observable completion conditions.
5. **Constraints** — stack, hosting, compliance, compatibility and product rules.
6. **Relevant paths** — known files/modules or state “discover from repo”.
7. **Environment contract** — variable names required, never secret values.
8. **Test commands** — or permission to discover them from the repo.
9. **Deployment target** — if deployment is in scope.
10. **Known blockers** — external access, credentials, legal/business decisions.
11. **Definition of done** — product-specific additions to the global standard.

## Preferred handoff format

```yaml
repository: owner/repo
task_id: ISSUE-123
objective: "..."
current_state: "..."
acceptance_criteria:
  - "..."
constraints:
  - "..."
relevant_paths:
  - "discover"
environment_variables:
  - NAME_ONLY
test_commands:
  - "npm test"
deployment:
  in_scope: false
  target: ""
known_blockers: []
security_notes: []
```

## Handoff back to Sigma

ChatGPT should return durable state through GitHub:
- commits/branch/PR;
- test results;
- changed behaviour;
- new environment requirements;
- migrations;
- remaining work;
- updated `PROJECT_STATUS.md`.

## What Sigma should never send

- passwords;
- API keys;
- private keys;
- full production database dumps;
- customer secrets;
- vague instructions such as “finish everything” without first translating them into repository-backed work items.

If the product owner gives a broad instruction such as “continue until finished”, Sigma should convert the repository's outstanding work into an ordered execution queue and keep the queue in GitHub.
