# Sigma automation: independent advisory and engineering design

Date: 29 September 2026. Reviewed source snapshot: `8339e20` (checkout name; exact full GitHub commit belongs in implementation evidence).
Role: independent architecture/advisory reviewer, separate from implementation. This report defines acceptance criteria; it does not certify deployment, security PASS or tests not run.

## Mission and accountability

Implement durable unattended Sigma project cycles on the existing private OVH Docker host. The accountable project is Sigma Development Command Center, resolved through `headquarters/chat-ownership/teams.yaml`; engineering, integration, database, reliability, AI-agent and security specialists apply. Sigma remains the authority; gstack contributes versioned workflow material.

## Verified facts

- Python runtime already has SQLite WAL mission, cycle and lease persistence. The daemon calls a synchronous portfolio cycle repeatedly.
- Base Compose deploys the runtime; the Ollama overlay adds the existing runner and worker with restart policies, a private network and persistent volumes.
- Existing GitHub worker mutation and runner execution require explicit environment switches. Worker statuses deliberately exclude VERIFIED and RELEASED.
- Existing selection checks contract file presence, then issue text heuristics; it does not parse manifest authority. Highest-priority sorting can repeatedly select the same project.
- Lease heartbeats occur between blocking calls. A long model call can exceed a lease before renewal; existing stale recovery therefore needs care when reused for unattended dispatch.
- `PROJECT_STATUS.md` explicitly records that live unattended completion is not proven. Work packages #89-#93 already own PR supervision, worker profiles, contracts, deployment adapters and selection repair.
- Existing architecture/deployment introductions predate the private runtime and contradict later runtime sections. Update these when publishing new operational instructions.

## Assumptions and proposals

Assume one OVH host and one local persistent SQLite volume initially. Host availability, secrets, real model capacity, external ingress and backup restore are not established by source inspection. Do not claim them verified.

Propose a durable intake/scheduler queue feeding bounded existing runner/worker interfaces. Keep the legacy runner API compatible. Only explicitly enabled active projects may execute. A source-controlled schedule is an operator policy, while product manifests and central authority restrict what the project may do.

## Expert council recommendations

| Domain | Recommendation | Material dependency or uncertainty |
| --- | --- | --- |
| Architecture/integration | Reuse existing worker and mission evidence, add durable queue and scoped dispatch; do not build a second PR supervisor. | Reconcile open PR #96 and #89-#93 before touching their files. |
| Database/reliability | Atomic claim transactions, durable scheduling cursor, fenced completions, bounded backoff and persistent dead/blocked states. | SQLite is suitable for a single host; not a shared network-filesystem database. |
| AI-agent security | Treat issues, webhook fields and gstack text as untrusted task data. Deterministic enforcement owns permissions. | An authority prompt alone is insufficient sandboxing. |
| Supply chain/legal | Pin full upstream commit and content hashes; retain licence attribution. No automatic upstream update/install script execution. | Verify selected upstream licence and exact files at the pinned revision. |
| Operations/UX | Expose health, queue counts, last success, exact blocked reason and next action without prompts/secrets. | Docker reports unhealthy containers but does not automatically restart them solely because they are unhealthy. |
| Finance/business | Reuse existing host and approved inference; prevent paid fallback and enforce bounded attempts/concurrency. | Host capacity and model throughput require measured commissioning evidence. |
| Privacy | Keep prompts, raw webhook bodies, worker output and credentials in private runtime state; publish only sanitized evidence references. | Define retention and backup ownership before live enablement. |
| HR/marketing/sales/creative | No new user interface, staffing or commercial campaign required. Preserve existing accountable team and human escalation route. | No separate deliverables for these domains in this infrastructure change. |

## Candidate tournament

1. **GitHub Actions schedules alone:** simple, but provides neither continuous workers nor reliable low-latency timing and cannot substitute for private durable job state. Keep Actions for validation and approved deployment.
2. **Redis/Celery or managed queue:** viable future multi-host option, but adds a service, migration and operational burden without demonstrated need. Reject for the initial single-host scope.
3. **SQLite queue plus private Docker service:** preferred because the existing runtime already depends on SQLite and one persistent host. Explicitly serialize claims, heartbeat long operations and bound recovery. This is a design selection, not a benchmark claim.
4. **Install gstack globally as the control layer:** reject; upstream skill instructions and shipping commands must not acquire Sigma root, release or secret authority.

## Required invariants

- Intake returns success only after its durable transaction commits. Duplicate GitHub delivery IDs never create a second job.
- Verify `X-Hub-Signature-256` over exact raw bytes with constant-time comparison, before parsing JSON. Reject missing secret/signature, oversized bodies, unsupported events and repositories outside the registry/operator allowlist.
- Webhook authentication proves origin, not permission for issue authors to execute commands. Payload URLs, shell text, workflow names and claimed owner identities cannot select executable code or grant authority.
- Re-read project lifecycle, current contract and execution policy immediately before dispatch; queued permission is not permanent permission. Missing/malformed policy fails closed.
- A scheduled slot creates at most one job per project; missed slots coalesce instead of flooding recovery. Active work is bounded per project and globally.
- Claims and attempts are transactional. Completion requires the current claim token. A stale worker cannot overwrite a newer owner's state.
- Heartbeats run while blocking model/worker calls run. When authority or lease ownership is lost, stop dispatching further effects.
- Stable job/mission IDs reach the external worker. If remote execution might have happened but acknowledgement is lost, reconcile by ID or mark BLOCKED/UNKNOWN; never blindly re-dispatch a mutation.
- Distinguish retryable infrastructure errors, terminal invalid inputs, owner gates, and successful source changes. Bounded retry exhaustion remains actionable durable state.
- gstack is explicitly enabled, pinned and integrity checked; allowlisted workflows only. It cannot self-update, silently install hooks or authorize ship/merge/deploy.
- Worker success is a claim. Preserve branch/PR/commit evidence and pending independent checks; queue success cannot mean production-ready.
- Logs and public evidence never echo raw exception bodies or task/model output containing secrets. Status endpoints require authentication except a minimal liveness response.
- Existing owner gates for credentials, spend, destructive production actions, root authority and security reductions remain unchanged.

## Acceptance evidence required

1. Restart process against same database: pending and retry jobs survive with original identity and attempts.
2. Concurrent queue claimers: exactly one active claim; per-project serialization; stale token cannot complete a newer claim.
3. Long running dispatch: heartbeat renews before expiry; stale recovery cannot launch a duplicate; uncertain remote outcome is retained for reconciliation.
4. Signed webhook accepted; bad signature, modified body, missing secret, invalid JSON, oversized body and unregistered repository rejected without dispatch. Repeated delivery ID is idempotent.
5. Two projects with differing intervals: only due slots enqueue, both progress, restart does not replay old slots, paused/disabled projects remain idle.
6. Retryable failure uses bounded delayed retries; terminal/authority failures do not spin. Exhausted jobs and worker death expose an exact next action.
7. gstack hash mismatch, unpinned revision, forbidden workflow and disabled configuration fail closed. Reviewed allowed content reaches worker with provenance and Sigma restrictions.
8. Existing runtime and runner regression suite plus control-plane validation pass. Exact CI head must match the published implementation head.
9. Private Docker commissioning: signed intake to queue to real model/worker to repository evidence, then container restart/persistence, worker recovery and backup restore. No desktop session involved.
10. Independent security review covers ingress, authorization, AI injection, dependency pinning, credentials, logs, network, persistent data and recovery. Missing live evidence remains NOT VERIFIED.

## Ordered delivery and gates

1. Inspect open PR #96 and existing work packages; establish additive ownership and record related issue.
2. Implement queue schema, state transitions, idempotent intake, project scheduling, fenced retry/recovery and failure tests.
3. Integrate pinned gstack material with existing bounded worker contract and authority checks; retain off-by-default mutation.
4. Add Docker service health and operator runbook, explicit secret names, backup/recovery and rollback instructions. Avoid Vercel.
5. Run local regression/hostile tests and exact-head GitHub CI; obtain independent engineering/security verdicts.
6. Commission on authorized OVH environment using existing secrets/access only. Where unavailable, record the exact owner-gated credential/configuration step in GitHub and preserve deployment as NOT VERIFIED.
7. Prove one unattended task and next scheduled task. Merge/deploy/closure supervision remains subject to #89/#92 and its own evidence gates.

Rollback: disable new intake/scheduling/execution, allow or halt active work under the mission policy, preserve queue database and evidence, restore reviewed prior application image. Prefer additive database migrations; never delete the private volume as rollback. Rehearse backup/restore before live mutation.

Next review action: challenge the actual implementation against each invariant above and link exact test names/results. This report alone is not a release approval.

## Independent implementation review — first test pass

The independent reviewer added `tests/test_sigma_automation.py` with 23 tests covering signed intake/replay/cross-project rejection, concurrent claiming, restart persistence, bounded backoff, unknown-outcome holds, fencing, schedule fairness, current product authority, issue changes and existing-PR exclusion. The first local execution did not pass: the dependency directory exposed an unreadable/incomplete `yaml` import, and SQLite connections remained open until garbage collection, causing Windows temporary-database cleanup failures. This is failed/blocked evidence, not a successful test claim.

Implementation findings sent to the implementer:

1. Recovery executed only once at worker startup. A recently interrupted RUNNING job could escape initial stale detection, then block every claim forever. Recheck recovery during idle scheduling.
2. Stale recovery selected candidates then failed them in another transaction, allowing a fresh heartbeat between those steps to be ignored. Recheck staleness atomically with the transition.
3. SQLite connection context managers commit or roll back but do not close connections. Explicitly close connections after each transaction to avoid long-running resource leakage and database-file locks.

Follow-up evidence must record the rerun after repairs and actual dependency availability. Docker process supervision, live model execution, OVH persistence/restart and backup restore remain unverified by these unit tests.

## Final independent engineering review

Implementation candidate: `3719228204ee83debaa442bec16a49f7239197e9`, PR #98. This review is independent of the implementation; the final execution results below were observed and supplied by the lead implementing agent, rather than rerun by this reviewer.

The lead reports repairs for all three engineering findings above: QueueStore, RunnerStore and MissionStore now close their connections; stale recovery rechecks staleness atomically; the worker repeats recovery so recently interrupted jobs cannot permanently block later claims. The test helper was updated for the connection context-manager API. These supersede the first-pass failures; the initial failed evidence is retained above for traceability.

Reported verification on the implementation candidate:

- Local suite: 123 tests passed, with one Linux-only supervisor test skipped on Windows.
- Additional reporting tests: 3 passed.
- GitHub automation workflow run `36555229441`: SUCCESS, including Docker build, Linux supervisor checks, read-only/non-root gstack checks and Compose configuration validation.
- GitHub control-plane workflow run `36555229342`: SUCCESS.
- GitHub mesh runtime workflow run `36555229460`: SUCCESS.

The lead verified PR #96's overlap: changes to `sigma_runtime/portfolio_runner.py` and its existing tests, plus new `pr_supervisor.py` and supervisor tests. This implementation uses a separate ProjectRunner adapter and leaves PR supervision with that workstream; its existing-runner change closes database connections. Reconcile the actual combined diff before merging either overlapping branch.

Engineering conclusion: the reviewed design and independent acceptance tests support the bounded source implementation, with the discovered recovery and connection defects reported repaired and CI evidence supplied on the exact candidate above. This is not an independent security PASS or a live deployment certification. This reviewer did not personally execute the final repaired suite because its requested elevated dependency access was interrupted; the attribution above is intentional.

Remaining acceptance gates: approved OVH deployment; real signed delivery through a real model/worker to repository evidence; restart and backup-restore evidence on the private persistent volume; independent security verdict; product-specific authority and release gates; and coordination with the existing PR supervisor before autonomous merge/deployment claims. Keep these steps and their exact evidence in GitHub. Source tests and Docker CI do not establish that unattended project completion is already live.
