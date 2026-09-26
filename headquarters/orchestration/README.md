# Sigma Portfolio Evidence Orchestrator

This layer turns Sigma from chat-triggered governance into a portfolio evidence ledger.

## Non-negotiable rule

**NO EVIDENCE = NO PROGRESS.**

A project can be Planned, Running, Changed, Tested, Verified in production, or Blocked. An instruction to an agent is not a change. A source change is not a test. A passing source test is not production verification.

## Per-project cycle record

Each registered project may expose `headquarters/orchestration/projects/<slug>.yaml` containing:

- last Sigma cycle;
- current production version/identity when proven;
- GitHub commit;
- automated test pass/fail counts;
- mobile/browser journey evidence;
- named capability health such as AI Assist and PDF Chat;
- research findings;
- implemented improvements;
- before/after benchmark evidence;
- next cycle/action;
- evidence links/identifiers;
- lifecycle state and derived freshness.

`scripts/sigma_portfolio_status.py` validates these records and derives STALE when the last evidenced cycle exceeds the configured threshold.

## Important boundary

The scheduled workflow refreshes and validates central evidence. It does **not** fabricate product execution. Cross-repository implementation remains Issue #2 until the autonomous runner can actually select work, mutate product repositories, observe CI, repair, deploy to authorised environments, run independent user tests, and write the resulting evidence back here.
