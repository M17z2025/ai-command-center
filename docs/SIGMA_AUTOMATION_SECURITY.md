# Sigma automation independent cybersecurity review

## Review identity

- Product/repository: Sigma, `M17z2025/ai-command-center`.
- Date: 29 September 2026.
- Reviewer: independent security review agent, separate from implementation.
- Reviewed baseline: `c899c3bb2dfa99e9c4d83467e1bcff80f3282552`, plus the automation working-tree candidate. This is not an immutable final-head certification; the final PR must identify the exact tested head.
- Environment: local Windows source review. No live OVH access, deployment, credential provisioning or external penetration tests were performed.
- Verdict: **BLOCKED / NOT VERIFIED for unattended live execution**. An execution-disabled source candidate may proceed through PR review; this report does not certify production readiness.

## Trust boundaries and data

GitHub sends signed events into an intake service. Verified events only wake an allowlisted project; they do not supply commands or permissions. A private SQLite queue coordinates the scheduler, isolated child process and existing portfolio runner. The runner reads live product policy and issues before dispatching to a separate coding worker. The coding worker, model provider, GitHub credentials, private SQLite volume, proxy and host are distinct trust boundaries.

The queue summary omits issue bodies and model text. Existing runner and mission tables still retain private prompts, issue text and model output. Backups and status exports must treat the complete database as private. This is a single-owner control plane; database row-level tenant isolation is not applicable. Cross-repository execution scope remains applicable.

## Findings and commissioning gates

| ID | Severity | Evidence and impact | Required remediation / status |
| --- | --- | --- | --- |
| AUTO-SEC-01 | HIGH, existing execution prerequisite | `scripts/sigma_openhands_worker_service.py` runs OpenHands `LocalWorkspace` and `TerminalTool` in the service containing `SIGMA_GITHUB_TOKEN`; verification executes agent-editable project code using the credential-bearing environment. Payload authority booleans and prompt instructions cannot enforce least privilege against malicious issue/repository content. | Keep autonomous execution disabled until a credential-free sandbox and independently controlled branch/PR broker are evidenced. Prove prohibited credentials, host paths, Docker socket, network destinations and protected branches are inaccessible from agent tools and verification subprocesses. |
| AUTO-SEC-02 | MEDIUM, candidate recovery | Initial `worker()` calls stale recovery only at startup. A restart within 120 seconds leaves the previous RUNNING row fresh; subsequent claims continually refuse it, and recovery never runs again. | Reconcile previous jobs after obtaining exclusive supervisor ownership, preserving UNKNOWN holds for dispatch ambiguity; add immediate-restart regression. Implementation owner notified. |
| AUTO-SEC-03 | MEDIUM, candidate replay | Initial delivery deduplication uses only unsigned `X-GitHub-Delivery`. Reusing a captured signed body under fresh delivery IDs creates new work and consumes retention capacity. | Deduplicate signed-body digest independently of delivery IDs; test changed-ID replay after terminal job completion. Implementation owner notified. |
| AUTO-SEC-04 | HIGH before concurrent execution | Initial `LiveRunnerStore` lease heartbeat has no exception handler. A storage exception terminates the daemon thread while the job continues; the runner lease can expire and permit competing work. | Fail-stop the child on heartbeat/renewal failure and test the failure path. Implementation owner notified. |
| AUTO-SEC-05 | HIGH, existing execution prerequisite | Existing coding worker ignores the supplied `source_commit` and clones the moving default branch. It does not enforce a brokered capability boundary; the repository token can exceed declared authority. | Pin and verify the exact authorised source SHA and repository before executing. Verify per-project token scope and branch protections independently. Keep execution disabled pending evidence. |
| AUTO-SEC-06 | MEDIUM, live ingress prerequisite | Intake uses a single-thread Python HTTP server with a ten-second socket timeout. Unauthenticated slow requests can occupy its sole handler; app body limits do not establish an edge rate limit or TLS. | Bind intake only to host loopback behind the approved TLS proxy with bounded request size, header/body timeouts, concurrency and request rate. Verify externally before public webhook commissioning. |

## Required control matrix

| Area | Result | Evidence / remaining requirement |
| --- | --- | --- |
| Threat boundaries | PASS, source scope | Intake, queue, model, coding worker, repository and host boundaries identified above. |
| Authentication / webhook signatures | NOT VERIFIED end to end | Source uses HMAC-SHA256 with constant-time comparison and minimum 32-character secret; reject missing/incorrect signatures. Live secret strength, storage, rotation and negative HTTP tests remain. |
| Authorization / repository isolation | NOT VERIFIED end to end | Local registry allowlist, project opt-in, product contract opt-in, issue label, explicit global execution/write switches and disabled defaults are present. Test cross-repo dispatch, label revocation, issue edits, contract changes and missing credentials on exact final head. Worker isolation remains blocked by AUTO-SEC-01/05. |
| API / replay / input limits | NOT VERIFIED final candidate | Body capped at 256 KiB, event/action allowlist and delivery capacity limit present. AUTO-SEC-03 needs regression verification. |
| Supply-chain / gstack provenance | PASS, design/source only | Four explicit advisory files; exact commit, SHA-256 and size pins; raw HTTPS origin, redirect rejection, link checks, no upstream executable skill installation. Cached bytes are rechecked at use. Upstream content is marked untrusted and cannot grant authority. Actual pinned-byte download and final tests need evidence. |
| Secrets / logs / privacy | NOT VERIFIED live | Intake avoids request logging and queue summary minimises text. Existing runner persists mission contents and error strings privately. Verify volume permissions, backup encryption/access and secret-safe export. No secret values were requested or printed by this review. |
| Static analysis / secret / dependency scan | NOT VERIFIED | Full final-head scanning/SCA evidence required; base runtime image is a mutable tag and requirements are not hash locked. Do not equate deterministic unit tests with a vulnerability audit. |
| Infrastructure / container / network | NOT VERIFIED | Final overlay, rendered Compose configuration, image digest, uid, capabilities, filesystem mounts, loopback ports, TLS and firewall require separate evidence. |
| Recovery / fencing / retry | NOT VERIFIED final candidate | Atomic SQLite claims, unique active project, dispatch-intent persistence, fencing and UNKNOWN holds are present. AUTO-SEC-02/04 require repair/retest. Remote dispatch may continue after local timeout: reconcile actual worker and GitHub state before clearing a hold. |
| Audit / health / watchdog | NOT VERIFIED live | Queue status and heartbeat exist. Verify watchdog restart and external alerting on stale worker, full disk, DB corruption, retention exhaustion and held project; a fresh heartbeat does not prove successful work. |
| Backup / restore / rollback | NOT VERIFIED | Demonstrate consistent SQLite backup/restore with WAL, persistent Docker volume, restart after abrupt termination, and non-destructive rollback on approved host. |
| AI prompt/tool injection | NOT VERIFIED execution | Advisory reference is bounded; new gateway refuses authority escalation fields. Hostile issue/repository content still reaches coding tools. AUTO-SEC-01 is a mandatory execution gate. |
| User sessions/MFA, mobile/OAuth, uploads, RLS | N/A | New service exposes signed event intake and minimal health only; no end-user sessions, mobile flow, file upload or multi-tenant database. |
| Authorised live adversarial test | NOT VERIFIED | No live environment was accessed by this reviewer. |

## Test evidence

The initial independent local invocation `python -m unittest discover -s tests -p 'test_sigma_gstack.py' -v` did not reach tests: default Python 3.14 lacks PyYAML (`ModuleNotFoundError: yaml`). This is an environment failure, not a passing or failing security assertion. Final-head CI and configured-runtime evidence must be recorded separately.

## Exact next gated actions

1. Repair/retest candidate findings AUTO-SEC-02/03/04, with an independent source retest on the final commit.
2. Keep project `execute: false` and global execution/write switches disabled while qualifying the new queue and read-only planning cycle.
3. Render and inspect the OVH Compose overlay; test restart, slow/forged/replayed webhooks, disk/storage faults and database restoration in an authorised non-production container environment.
4. Independently remediate the credential-bearing coding-worker boundary and exact-source checkout before changing any execution switch. Prove repository restrictions and protected-branch checks with hostile tests.
5. Provision any missing owner-held webhook/worker/GitHub secrets through the approved secret channel. Record only names and confirmation, never values, in GitHub.
6. Record host, exact image/source commit, test commands, exit statuses, redacted evidence and remaining gates in the implementation PR. Run a single opted-in staging issue through dispatch, independent exact-head CI/security and applicable user testing before expanding the project allowlist.

No owner risk exception, protected-branch bypass or production authority is granted by this report. The reviewer cannot certify a deployment that has not been observed.
