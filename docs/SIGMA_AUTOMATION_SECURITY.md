# Sigma automation independent cybersecurity review
> Latest reviewed implementation: `8db1f82c245681daf2963cc00e3246df2c4edfea`, PR #98. The worker-isolation follow-up below supersedes the original source findings AUTO-SEC-01 and AUTO-SEC-05: their design defects are repaired in the candidate. Live enforcement remains NOT VERIFIED until OVH commissioning evidence passes. Earlier sections preserve the original audit history and evidence limitations.

## Review identity

- Product/repository: Sigma, `M17z2025/ai-command-center`.
- Date: 29 September 2026.
- Reviewer: independent security review agent, separate from implementation.
- Reviewed baseline: `8339e20f67a0e4ba4cdc815a50b046a43218871f` (upstream ZIP source), plus the automation candidate. Published implementation head: `3719228204ee83debaa442bec16a49f7239197e9`, PR #98. The initial local Git snapshot was unrelated to upstream history.
- Environment: local Windows source review. No live OVH access, deployment, credential provisioning or external penetration tests were performed.
- Verdict: **BLOCKED / NOT VERIFIED for unattended live execution**. An execution-disabled source candidate may proceed through PR review; this report does not certify production readiness.

## Trust boundaries and data

GitHub sends signed events into an intake service. Verified events only wake an allowlisted project; they do not supply commands or permissions. A private SQLite queue coordinates the scheduler, isolated child process and existing portfolio runner. The runner reads live product policy and issues before dispatching to a separate coding worker. The coding worker, model provider, GitHub credentials, private SQLite volume, proxy and host are distinct trust boundaries.

The queue summary omits issue bodies and model text. Existing runner and mission tables still retain private prompts, issue text and model output. Backups and status exports must treat the complete database as private. This is a single-owner control plane; database row-level tenant isolation is not applicable. Cross-repository execution scope remains applicable.

## Findings and commissioning gates

| ID | Severity | Evidence and impact | Required remediation / status |
| --- | --- | --- | --- |
| AUTO-SEC-01 | HIGH, existing execution prerequisite | `scripts/sigma_openhands_worker_service.py` runs OpenHands `LocalWorkspace` and `TerminalTool` in the service containing `SIGMA_GITHUB_TOKEN`; verification executes agent-editable project code using the credential-bearing environment. Payload authority booleans and prompt instructions cannot enforce least privilege against malicious issue/repository content. | Keep autonomous execution disabled until a credential-free sandbox and independently controlled branch/PR broker are evidenced. Prove prohibited credentials, host paths, Docker socket, network destinations and protected branches are inaccessible from agent tools and verification subprocesses. |
| AUTO-SEC-02 | MEDIUM, candidate recovery | Initial `worker()` calls stale recovery only at startup. A restart within 120 seconds leaves the previous RUNNING row fresh; subsequent claims continually refuse it, and recovery never runs again. | Reconcile previous jobs after obtaining exclusive supervisor ownership, preserving UNKNOWN holds for dispatch ambiguity; add immediate-restart regression. REPAIRED in candidate: implementation owner reports regression coverage passing; independent reviewer inspected the corresponding source repair before final publication. |
| AUTO-SEC-03 | MEDIUM, candidate replay | Initial delivery deduplication uses only unsigned `X-GitHub-Delivery`. Reusing a captured signed body under fresh delivery IDs creates new work and consumes retention capacity. | Deduplicate signed-body digest independently of delivery IDs; test changed-ID replay after terminal job completion. REPAIRED in candidate: implementation owner reports regression coverage passing; independent reviewer inspected the corresponding source repair before final publication. |
| AUTO-SEC-04 | HIGH before concurrent execution | Initial `LiveRunnerStore` lease heartbeat has no exception handler. A storage exception terminates the daemon thread while the job continues; the runner lease can expire and permit competing work. | Fail-stop the child on heartbeat/renewal failure and test the failure path. REPAIRED in candidate: implementation owner reports regression coverage passing; independent reviewer inspected the corresponding source repair before final publication. |
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

1. Preserve repaired candidate findings AUTO-SEC-02/03/04 in regression coverage. Signed-body digest replay rejection, recurring recovery with transactional stale-heartbeat recheck, and lease-heartbeat fail-stop were inspected independently. Explicit SQLite connection closure was also repaired.
2. Keep project `execute: false` and global execution/write switches disabled while qualifying the new queue and read-only planning cycle.
3. Render and inspect the OVH Compose overlay; test restart, slow/forged/replayed webhooks, disk/storage faults and database restoration in an authorised non-production container environment.
4. Independently remediate the credential-bearing coding-worker boundary and exact-source checkout before changing any execution switch. Prove repository restrictions and protected-branch checks with hostile tests.
5. Provision any missing owner-held webhook/worker/GitHub secrets through the approved secret channel. Record only names and confirmation, never values, in GitHub.
6. Record host, exact image/source commit, test commands, exit statuses, redacted evidence and remaining gates in the implementation PR. Run a single opted-in staging issue through dispatch, independent exact-head CI/security and applicable user testing before expanding the project allowlist.

No owner risk exception, protected-branch bypass or production authority is granted by this report. The reviewer cannot certify a deployment that has not been observed.

## Final source review update — PR #98

Candidate findings AUTO-SEC-02, AUTO-SEC-03 and AUTO-SEC-04 are repaired in source. The corresponding rows and matrix above describe the original finding and live qualification requirements; they are not remaining unfixed source blockers. The independent reviewer inspected digest-based replay deduplication and lease fail-stop repairs; the implementation owner reports the recurring recovery/staleness recheck and explicit database connection closure are covered by the passing suite. No live deployment verdict is inferred from those repairs.

Evidence supplied by the implementation owner, not independently executed by this reviewer:

- Exact implementation commit: `3719228204ee83debaa442bec16a49f7239197e9`, [PR #98](https://github.com/M17z2025/ai-command-center/pull/98).
- Local suite: 123 tests passed, one Linux supervisor test skipped on Windows; three reporting tests passed separately. Actual local HTTP-process testing and control-plane validation passed.
- GitHub automation checks: [run 36555229441](https://github.com/M17z2025/ai-command-center/actions/runs/36555229441), reported SUCCESS, including Docker build, Linux process tests, non-root gstack access and Compose validation.
- GitHub control-plane checks: [run 36555229342](https://github.com/M17z2025/ai-command-center/actions/runs/36555229342), reported SUCCESS.
- GitHub mesh checks: [run 36555229460](https://github.com/M17z2025/ai-command-center/actions/runs/36555229460), reported SUCCESS.
- Independent gstack specialist reported eight tests passing and a verified actual pinned-file installation. Those results are delegated evidence; this reviewer did not run the successful installer.

The separate independent test attempt using installed dependencies encountered sandbox read restrictions and Windows SQLite cleanup failures before the connection-closure repair. An escalated rerun was interrupted without a result; it contributes no passing evidence.

The new GitHub status outbox is reported to publish only job/repository identity, state and attempt metadata using a separate issue-only token, with retries and reconciliation independent from job execution. Its final implementation received separate architecture/test review; this reviewer did not independently inspect or execute the final outbox code. Public reporting must continue to exclude mission text, model output, credentials and exception details; repository names may themselves be sensitive if the allowlist is expanded to private products.

**Final independent security disposition:** source candidate may proceed through the execution-disabled PR workflow with the recorded evidence and limitations. **Unattended live execution remains BLOCKED / NOT VERIFIED.** AUTO-SEC-01 and AUTO-SEC-05 remain mandatory coding-worker activation gates; AUTO-SEC-06 requires deployed edge verification. The runbook explicitly keeps the existing credential-bearing worker disabled until isolation and exact-source enforcement are proven. Live secrets, host/network configuration, external alerts, restore evidence and an actual unattended project journey remain unverified. Successful CI does not certify those controls.

## Independent worker-isolation follow-up — `8db1f82c245681daf2963cc00e3246df2c4edfea`

Reviewed source: `sigma_worker_isolation.py`, `sigma_worker_sandbox.py`, `sigma_openhands_worker_service.py`, the production inference gateway, worker Dockerfiles/Compose overlay, source-SHA dispatch fields and runtime API execution checks. This review was read-only except for this report.

### Findings resolved in source

- **AUTO-SEC-01, credential boundary:** the trusted broker performs Git transport and Docker operations. Repository scripts, model terminal tools and verification run in disposable non-root containers with no host mounts, Docker socket or broker credential environment. Only bounded, validated regular-file bytes return; a second exact-source checkout receives them. Verification uses a separate network-disabled container and its mutations are discarded. This repairs the previous LocalWorkspace-in-credential-process design.
- **AUTO-SEC-05, source identity:** a full `source_sha` is required; Git fetch resolves and verifies that exact commit before materialising source. Both runner dispatch paths now supply that field. Source links/submodules are rejected, and Git hooks, ambient configuration, credential helpers and local/ext transports are disabled for trusted Git operations.
- **Inference abuse:** the gateway serialises requests, bounds request/header/body reads, rejects malformed framing and non-object JSON, fixes the permitted model, replaces model options with context/output limits, and bounds model retention. The sandbox reaches only the pinned gateway on an internal isolated network. Redirects, ambient proxies and Ollama model-management routes are unavailable.
- **Broker request exhaustion:** request parsing has a ten-second socket timeout from handler setup; pre-authentication threads are bounded to 16. Bearer authentication uses constant-time comparison. Framing rejects transfer encoding and duplicate content length.
- **Orphan recovery:** disposable containers receive the validated broker identity label. Startup removes only that broker's labelled containers before accepting work, failing closed when cleanup fails. Deploy exactly one broker per identity; other brokers require distinct identities.
- **Execution switch:** the runtime API validates the execute field as boolean and requires explicit server execution configuration and write authority. This is source inspection, not a live-host authorization test.

### Independently executed local evidence

Commands run against the reviewed shared checkout using local Python:

| Command | Observed result |
| --- | --- |
| `python -m unittest discover -s tests -p test_sigma_worker_gateway.py -v` | 4 passed, including real HTTP malformed-request, option replacement, incomplete-body and incomplete-header cases |
| `python -m unittest discover -s tests -p test_sigma_worker_isolation.py -v` | 4 passed; 5 real-Docker cases explicitly skipped because no fixture image was configured |
| `python -m unittest discover -s tests -p test_sigma_private_worker.py -v` | 6 passed |

Total independently executed in this follow-up: **14 passed, 5 skipped**. The Docker skips include credential/network isolation and orphan cleanup; they are not passing deployed evidence. No additional confirmed source escape from the regular-file transfer boundary was identified in this review.

### Live disposition and next gate

**BLOCKED / NOT VERIFIED for live unattended writes.** The implementation owner reports a fresh OVH audit found no configured GitHub token, worker endpoint or worker token, and the GitHub runner cannot read the protected `/opt/ai-command-center/deploy/sigma-stack/.env`. This reviewer did not access that host or the protected file. Missing credentials and restricted provisioning access are actual deployment blockers, not a reason to weaken access controls.

The original source-level HIGH findings are now repaired in the candidate; their live enforcement is still an activation gate. Before activation, record exact broker/sandbox/gateway image IDs, approved Docker Engine/network configuration, all five real-Docker hostile tests on OVH, credential scope and branch restrictions, cleanup/restart proof, and one bounded actual model mission. The Docker socket gives the broker host-level authority, so its immutable reviewed code and private authenticated endpoint are mandatory trust assumptions. Keep the existing execution/write switches disabled until those controls are evidenced and missing owner-held configuration is provisioned through the authorised channel.

This disposition permits continued execution-disabled testing and commissioning work. It grants no production release, secret provisioning or security-control reduction authority.

## Commissioning-helper independent source review

Reviewed `scripts/sigma_automation_commission.sh`, its commissioning guide, and the watchdog selection logic. The material finding that ignored local files could enter an allegedly exact-source image is **resolved in source**: builds now receive a tar archive of the supplied Git commit through standard input instead of the working directory. Protected configuration and commissioning state must remain outside the reviewed checkout. No ignored local secret or artifact is included by that build-context mechanism.

The helper defaults to preflight, requires explicit `--apply`, and exposes only planning and worker-readonly modes. It forces execution, worker writes and status publishing off. Selected-service updates use `--no-deps`; no stack teardown, orphan removal or volume deletion is performed. Existing runtime, memory and Ollama services are retained. Captured command output is withheld on failures; the generated credential-bearing manifest is private and must never be attached as evidence.

Worker mode requires the fourth exact-SHA successful workflow (`Sigma worker isolation`) and a recorded independent source-review attestation. It does not impose a different-GitHub-account requirement. Docker Engine 28+, bridge support and any existing worker network's internal isolated configuration are checked before replacement. Actual host connectivity/isolation tests remain required; a version/configuration check cannot replace them.

The watchdog selects only exact Compose project/service labels and restarts a unique matching container only when it is already running and unhealthy. It neither reads the protected environment file nor activates missing/stopped services.

**Source disposition:** the reported commissioning-helper material finding is repaired; no additional source blocker identified in this focused review. **Live commissioning remains NOT VERIFIED.** This addendum records source inspection only and adds no claim of helper execution, host mutation, credential provisioning or deployed test success. Preserve existing host access controls and record the actual selected-service apply, image IDs, queue persistence, restart and applicable worker isolation evidence after authorised provisioning.
