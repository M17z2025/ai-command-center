# Commission Sigma automation on the existing OVH stack

This helper prepares the existing `sigma-stack` deployment on OVH. It does not
register a runner, acquire credentials, grant release authority, enable paid inference,
pull models, publish a webhook endpoint, or enable unattended repository writes.

## Verified deployment boundary

The read-only audit [run 36563998576](https://github.com/M17z2025/alisha-ai-platform/actions/runs/36563998576)
located the existing stack at `/opt/ai-command-center/deploy/sigma-stack`.
Runtime, runner, memory, FalkorDB and Ollama already run under Compose project
`sigma-stack`. The private environment file exists there but is not readable by
the `alisha` GitHub Actions runner. The scheduler has no GitHub credential,
worker endpoint or worker token. Installed models are `qwen3:4b-instruct` and
`qwen3-embedding:0.6b`.

These are observations from that audit, not a claim that the new automation is
commissioned. A privileged operator must provision the protected configuration
and execute the helper under an identity that can read it and operate Docker.
Do not relax the existing file permissions to make the GitHub runner read it.

## Planning first

Planning mode replaces only `sigma-runner` in the existing Compose project.
It uses the reviewed automation image, the existing private network and a new
durable `sigma-stack_sigma-automation-data` volume. Existing runtime, memory,
Ollama and their volumes are retained. The old scheduler's volume is retained;
its history is not silently imported into the new queue.

Provision privately, without committing or pasting values:

- `SIGMA_AUTOMATION_GITHUB_TOKEN`: a dedicated read credential for the registered
  repositories and the command-center commit/Actions evidence endpoints.
- `OLLAMA_MODEL=qwen3:4b-instruct`, if that remains the approved installed model.
- Keep `SIGMA_RUNNER_EXECUTE`, `SIGMA_RUNNER_ALLOW_WRITE`,
  `SIGMA_WORKER_ALLOW_WRITE`, and `SIGMA_AUTOMATION_REPORT_WRITE` disabled.

Planning mode does not require a worker token, writer credential, or webhook
secret. It does not parse the full deployment overlay, so absent credentials
for services it will not start cannot block planning configuration.

The protected file must be mode 0600 or stricter, must not be a symlink, and
must contain simple single-line `KEY=value` entries. Quoted values are supported;
shell commands, interpolation and duplicate names are rejected. The file is
read as data, never sourced as shell code.

## Exact-source acceptance

Use a clean Git checkout of the approved source in a separate directory. Do not
overwrite the live stack checkout or its private `.env` to prepare a release.
The protected environment file must stay outside the image build context.
Supply the exact 40-character commit SHA and successful GitHub run IDs for:

- `Sigma automation and container`
- `Sigma mesh runtime`
- `Sigma control-plane validation`

The helper checks each run against the supplied source SHA through GitHub's
authenticated API. A green run on another commit is rejected. The helper does
not infer permission to merge or deploy from CI alone: the operator must use the
existing Sigma release approval process before running `--apply`.

Preflight first, using real reviewed values in place of the angle-bracket entries:

```bash
bash scripts/sigma_automation_commission.sh \
  --mode plan --sha <reviewed-40-character-sha> \
  --ci-run <automation-run-id> \
  --ci-run <mesh-runtime-run-id> \
  --ci-run <control-plane-run-id>
```

The same command with `--apply` builds the exact checkout and replaces the
scheduler after preflight passes:

```bash
bash scripts/sigma_automation_commission.sh \
  --mode plan --sha <reviewed-40-character-sha> \
  --ci-run <automation-run-id> \
  --ci-run <mesh-runtime-run-id> \
  --ci-run <control-plane-run-id> --apply
```

The default private file is
`/opt/ai-command-center/deploy/sigma-stack/.env`. Override it only with
`--env-file <approved-private-path>`. The helper never edits it or generates
secrets.

## Add the worker and intake without enabling writes

Use `--mode worker-readonly` only after independent isolation review and private
provisioning. In addition to planning configuration, it requires:

- Existing runtime and memory tokens.
- A provisioned `SIGMA_WORKER_TOKEN` and `SIGMA_WEBHOOK_SECRET`.
- Explicit, already installed `OLLAMA_WORKER_MODEL` and
  `OLLAMA_EMBEDDING_MODEL`.
- Base Compose `SIGMA_LLM_ENDPOINT` and `SIGMA_LLM_MODEL` values.
- An additional `--ci-run <worker-isolation-run-id>` for the successful
  `Sigma worker isolation` workflow on the exact source SHA.
- `--security-source-reviewed <exact-source-sha>` and
  `--security-evidence <GitHub-source-review-report-URL>`. These record the
  operator's attestation that independent isolation source review covers this
  exact commit. The helper verifies the SHA match and records the report link;
  it does not claim to validate the report's contents or grant release authority.
  Existing Sigma authority gates still apply. Independence concerns the review,
  not whether the GitHub connector uses a different account.

The helper builds immutable image IDs for automation, worker broker, sandbox and
inference gateway from a Git archive of the exact reviewed commit, so ignored
local files cannot enter the build context. Worker preflight requires Docker
Engine 28 or later, bridge networking, and validates any already existing
worker inference network's isolation settings. It includes the reviewed
worker-isolation overlay, adds only
`sigma-worker`, `inference-gateway` and `sigma-intake`, and keeps execution and
all write paths disabled. The broker receives only the dedicated reader credential
for private repository checkout; the sandbox receives no GitHub credential.
No model downloads run. The worker may use the existing
`qwen3:4b-instruct` only after it is explicitly selected and accepted for the
bounded task.

The gateway and worker need a separately verified live isolation test before
enabling writes. Starting containers is not proof that an autonomous coding
mission completed. Later execution must retain a separate least-privilege worker
writer credential, project allowlist, independent verification, protected control
plane and existing release authority. This helper has no option to enable writes.

The webhook listener remains loopback-only. Registering the GitHub webhook and
an authenticated public delivery route is a separate existing infrastructure
gate. Planning schedules can run without that route.

## Install the persistent watchdog

After successful commissioning, run these commands from the same approved source
checkout using the approved privileged identity. The override points the unit at
a copied reviewed script instead of depending on the older live checkout:

```bash
sudo install -d -m 0700 /opt/sigma-automation-commission
sudo install -m 0700 scripts/sigma_automation_watchdog.sh /opt/sigma-automation-commission/sigma_automation_watchdog.sh
sudo install -m 0644 deploy/sigma-stack/sigma-automation-watchdog.service /etc/systemd/system/sigma-automation-watchdog.service
sudo install -m 0644 deploy/sigma-stack/sigma-automation-watchdog.timer /etc/systemd/system/sigma-automation-watchdog.timer
sudo install -d -m 0755 /etc/systemd/system/sigma-automation-watchdog.service.d
printf '%s\n' '[Service]' 'WorkingDirectory=/opt/sigma-automation-commission' 'ExecStart=' 'ExecStart=/bin/bash /opt/sigma-automation-commission/sigma_automation_watchdog.sh' | sudo tee /etc/systemd/system/sigma-automation-watchdog.service.d/source.conf >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now sigma-automation-watchdog.timer
sudo systemctl start sigma-automation-watchdog.service
sudo systemctl is-active sigma-automation-watchdog.timer
```

The watchdog inspects only existing containers labelled with Compose project
`sigma-stack` and service `sigma-runner` or `sigma-intake`. It restarts a service
only when it is already running and Docker reports it unhealthy. It does not
read the protected environment, create missing services or reactivate deliberately
stopped services. The timer runs without a desktop or browser.

## Evidence and recovery

Successful builds emit source SHA, immutable image IDs and verified CI links.
The selected-service Compose manifest is saved privately under
`/opt/sigma-automation-commission/<sha>-<mode>.json` with mode 0600.
It contains credentials; do not upload or print it. Preserve it privately for
recovery, with the old scheduler's image/configuration captured privately before
an approved replacement.

The helper waits for selected services to start and health checks to pass. A
failure leaves containers and all volumes intact; it does not run destructive
cleanup or automatically restore stale configuration. Review the failure
privately and rerun the approved command after correction. It never calls
`compose down`, `--remove-orphans`, or volume removal.

Record non-secret evidence in the owning GitHub issue:

1. Approved source SHA, CI links, independent review where applicable.
2. Emitted immutable image IDs and commissioned service names.
3. Queue status and one scheduled planning cycle on a registered repository.
4. A scheduler restart followed by the same durable queue/job IDs.
5. For worker mode: private worker health, the inference isolation smoke test,
   and a bounded read-only worker mission.
6. Webhook delivery validation only after its separate ingress gate is completed.

Do not describe planning commissioning or container health as proof of
end-to-end autonomous code changes.

## Local/CI validation

```bash
bash -n scripts/sigma_automation_commission.sh
bash scripts/sigma_automation_commission.sh --help
# Must exit nonzero before reading configuration or contacting Docker/GitHub:
bash scripts/sigma_automation_commission.sh --sha invalid --ci-run 1
```
