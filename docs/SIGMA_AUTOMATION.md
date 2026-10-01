# Sigma + gstack VPS automation

Implementation task: [#97](https://github.com/M17z2025/ai-command-center/issues/97).
Baseline inspected: `8339e20f67a0e4ba4cdc815a50b046a43218871f`.

## What runs without a desktop

On the existing OVH Linux Docker host, `sigma-intake` accepts signed GitHub
webhooks and `sigma-runner` schedules and processes durable project wake-ups.
Both restart with Docker. A host systemd timer restarts unhealthy containers.
There is no desktop, browser session, Vercel service, paid queue, or new model
provider dependency. Existing private Ollama supplies inference.

```text
GitHub signed event -> loopback intake <- TLS proxy
                              |
reviewed registry schedules -> SQLite queue on private Docker volume
                              |
single supervised worker -> scoped PortfolioRunner -> Sigma mesh
                              |                         + pinned gstack review references
                              + governed coding gateway (explicit opt-in only)
                              + private cycles / provenance / recovery holds
                              + optional safe GitHub status outbox
```

SQLite was selected over a new Redis/Postgres dependency for this existing
single-host deployment. This design is not a multi-host distributed worker.
Queue database, lock and WAL files must use local persistent disk, not NFS.
The automation volume is separate from the existing runtime volume: automation
cycle status is read with the automation CLI, not the existing API's runner list.

## Scope and truth states

- `QUEUED` / `RUNNING` / `RETRY`: queue lifecycle, not product status.
- `DONE`: the runner cycle returned; a planning-only result is not implementation.
- `BLOCKED`: policy gate or changed PR awaiting independent supervision.
- `UNKNOWN`: dispatch began but outcome is uncertain. Automatic replay is forbidden.
- `DEAD`: three pre-dispatch failures exhausted bounded retries; operator recovery needed.

Per-project holds prevent future scheduled events from bypassing an UNKNOWN,
DEAD or BLOCKED job. Other enabled projects continue. One pending job per project
coalesces bursts and queue order gives other projects a turn. Missed schedule
periods coalesce into one wake-up after downtime. A disabled project is rechecked
at processing and again before a write, including when its event was queued earlier.

The existing runner still stops at branch/PR evidence. PR #96 / issue #89 owns CI
supervision; #90 owns portfolio worker profiles, #91/#95 repository security and
protection, #92 deployed user tests, #93 richer lifecycle selection. This adapter
defers a project with any existing PR to avoid competing implementations. Those
dependencies must pass before claiming autonomous project completion (#77/#88).

## Authority and per-project setup

`projects/automation.yaml` is deployment configuration, reviewed through PRs.
Only active entries in `projects/registry.yaml` can be enabled. Current default:
command-center scheduled planning every 900 seconds; execution and gstack context
disabled. The pinned reference bundle is installed in the image and can be enabled
by setting `gstack: true`; the planner receives at most 4,000 characters and stores
revision/source hashes. No upstream setup, shell, ship, deploy, telemetry or auto-update
code is installed. See [gstack provenance](SIGMA_GSTACK.md).

To add another project, review its registry/contract/status, worker profile and
independent security evidence, then add a policy entry. Runtime execution requires
ALL of these, not merely a signed event:

1. Reviewed local policy `enabled: true`, `execute: true`.
2. Runtime `SIGMA_RUNNER_EXECUTE=1`, `SIGMA_RUNNER_ALLOW_WRITE=1` and a least-privilege
   runner credential. Existing worker allowlist/write controls also remain enforced.
3. Product default-head `.sigma/project.yaml` includes:

   ```yaml
   automation:
     enabled: true
     execution: branch_pr
     owner_gates: preserve
   ```

4. Matching project repository identity, present `AGENTS.md` and `PROJECT_STATUS.md`.
5. Current open issue labelled `sigma:autonomous`, unchanged since planning.
6. No existing open PR. Independent review and product release policy still apply.

Issue text/webhook action is untrusted input and cannot enable any permission.
Use repository permissions so only authorised maintainers can change the opt-in
label/contract. All dispatches explicitly deny production, destructive actions,
spend, secret management, direct-main push and security-control reduction.

**Execution commissioning blocker:** the existing OpenHands LocalWorkspace worker
can run repository tools in a credential-bearing process and does not enforce the
new `source_commit` input. Before enabling it, provide a disposable credential-free
execution sandbox, brokered branch/PR writes, pinned source checkout, network and
tool isolation, and independent hostile-path evidence. Authority fields in a JSON
payload do not contain a shell. The integration provides dispatch gates; it does
not claim to repair or certify that existing worker boundary.

## Deploy on the existing VPS

Run after candidate CI/review and owner-held secret/access provisioning. Commands
assume the existing checkout is `/opt/ai-command-center`; adjust the systemd unit
WorkingDirectory if the approved checkout differs. Do not install a second scheduler.

```bash
cd /opt/ai-command-center
# Fetch/check out the reviewed PR commit using existing repository credentials.
COMPOSE=(docker compose --env-file deploy/sigma-stack/.env
  -f deploy/sigma-stack/docker-compose.yml
  -f deploy/sigma-stack/docker-compose.ollama.yml
  -f deploy/sigma-stack/docker-compose.automation.yml)
"${COMPOSE[@]}" config --quiet
"${COMPOSE[@]}" stop sigma-runner
"${COMPOSE[@]}" build sigma-runner sigma-intake
"${COMPOSE[@]}" up -d --no-deps sigma-runner sigma-intake
"${COMPOSE[@]}" ps
"${COMPOSE[@]}" exec -T sigma-runner python scripts/sigma_automation.py status
```

The existing model/runtime must already be healthy. The dedicated image runs UID
10001, uses a read-only root, drops capabilities and has process/memory limits.
New named volume ownership is populated from image `/data`. Existing volumes with
different ownership require a reviewed host-side migration, not a blanket chmod.
No Docker socket is mounted inside containers.

Private `.env` names (do not commit values or paste them into GitHub):

| Variable | Purpose/default |
|---|---|
| `SIGMA_WEBHOOK_SECRET` | Required owner-provisioned random secret, at least 32 characters |
| `SIGMA_AUTOMATION_GITHUB_TOKEN` | Runner repository read/approved branch authority; distinct from worker token |
| `SIGMA_AUTOMATION_JOB_TIMEOUT` | Hard child-process watchdog deadline, default 3600 seconds |
| `SIGMA_AUTOMATION_REPORT_TOKEN` | Optional issue-comments-only token for command-center |
| `SIGMA_AUTOMATION_REPORT_WRITE` | `0`; explicitly enable safe status publication with `1` |
| `SIGMA_AUTOMATION_REPORT_ISSUE` | `97`; dedicated GitHub evidence thread |
| `SIGMA_INTAKE_PORT` | Loopback port, default 8092 |
| Existing `SIGMA_RUNNER_*`, `SIGMA_WORKER_*`, `OLLAMA_*` | Existing policy/model configuration; retain write/execute `0` until gated proof |

The report outbox publishes only job UUID, registry repository, queue state and
attempt count. Raw model text, event bodies, tokens and exception messages stay
private. A failed status POST is reconciled by its marker before retry; reporting
never reruns implementation. Reconciliation scans at most 1,000 comments; after
that horizon an ambiguous POST can create a duplicate status comment. Use dedicated
periodically rotated evidence issues. This is at-least-once reporting, not an
exactly-once GitHub transaction.

### GitHub ingress

Configure the existing host TLS proxy to forward ONLY `/github/events` to
`127.0.0.1:8092`. Enforce TLS, 256 KiB body limit, 5-second header/body timeouts,
10-second upstream timeout, and per-source/global request and connection limits.
Do not expose raw port 8092 or the runtime/worker/admin endpoints publicly.
Application intake is intentionally small and serial; edge limits are a required
external control before public registration. Configure GitHub JSON webhooks for
issues, pull requests, workflow runs and pushes with the same private secret.

The receiver verifies HMAC SHA-256 before parsing, allowlists event/action/repo,
and retains delivery ID plus signed-body digest. Changing an unsigned delivery ID
cannot replay a signed body. GitHub signatures carry no timestamp, so old signed
payloads cannot be distinguished from delayed legitimate deliveries after deleting
the dedup history. Keep it for the secret lifetime; rotate the secret before archival.
At 100,000 deliveries, intake refuses new records until supervised archival/rotation.
Scheduled cycles continue if the webhook is offline; GitHub redelivery recovers a
failed delivery. Identical event bodies are intentionally coalesced.

### Host watchdog

After reviewing host paths:

```bash
sudo install -m 0644 deploy/sigma-stack/sigma-automation-watchdog.service /etc/systemd/system/
sudo install -m 0644 deploy/sigma-stack/sigma-automation-watchdog.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sigma-automation-watchdog.timer
systemctl list-timers sigma-automation-watchdog.timer
```

Docker restart policies handle process exits; the timer handles unhealthy-but-alive
containers. It does not start deliberately stopped services. Existing host monitoring
must alert on disk pressure, unhealthy/dead queues, model outage, timer failure and
GitHub reporting failure. Docker health alone is not an alerting service.

## Recovery, backups and rollback

SIGTERM stops intake/worker; in-flight child work gets a bounded shutdown. The OS
lock prevents competing local supervisors. A heartbeat runs during synchronous
model calls; losing the runner lease terminates the child. The supervisor kills the
local process group at deadline; remote coding work might still run, so dispatch
intent is committed first and uncertain results are held, never automatically retried.
Pre-dispatch retries use 60/120-second backoff and stop after three attempts.
Recovery revisits fresh-at-restart RUNNING rows after their 120-second expiry.

For a held project, inspect its cycle and GitHub branches/PRs, stop/reconcile any
remote work, complete independent gates and record the outcome in an issue. Only
then, as the authorised host operator:

```bash
"${COMPOSE[@]}" exec -T sigma-runner python scripts/sigma_automation.py resume \
  --repository M17z2025/ai-command-center \
  --evidence https://github.com/M17z2025/ai-command-center/issues/97
```

This CLI records a reconciliation URL; it does not verify that a comment itself
grants authority. Host operator access is the control. Never clear a hold only to
force retries. Original queue evidence is preserved alongside the reconciliation.

Stop both services and use SQLite's backup API (or copy the entire closed volume)
before upgrades; keep backups encrypted/private and test restore. Schema creation
adds new automation tables without modifying existing runtime tables. Retain volume
on rollback: stop intake/runner, restore prior reviewed image/config, keep all
execution switches off and reconcile UNKNOWN jobs before reactivation. Do not run
the old scheduler alongside the new one or delete a volume to recover service.

## Exact commissioning evidence to attach to #97

1. Reviewed source commit, container image digest, gstack pin and passing CI run URLs.
2. Redacted `compose ps`, UID/mount/health output and effective write/execute modes.
3. Valid GitHub delivery accepted, altered signature rejected, identical delivery
   replay and changed-ID replay deduplicated; no private body in public logs.
4. One real model-backed scheduled project cycle plus private cycle ID and safe
   GitHub outbox comment; a closed desktop must not affect the next cycle.
5. Restart persistent queue, forced local worker exit and health watchdog restart;
   stale pre-dispatch retry and post-dispatch UNKNOWN hold evidence.
6. Backup restore into an isolated test volume and continued queue/hold identity.
7. Before write mode: independent worker isolation/source pin proof, then one
   harmless opted-in branch/PR task with matching source and result identity.
8. Independent security/CI/user-test/release evidence before merge or deploy.

No live VPS deployment is claimed by source tests. See independent
[advisory](SIGMA_AUTOMATION_ADVISORY.md) and [security review](SIGMA_AUTOMATION_SECURITY.md).
