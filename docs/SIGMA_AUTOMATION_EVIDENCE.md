# Sigma automation evidence and handoff — 29 September 2026

Implementation: [PR #98](https://github.com/M17z2025/ai-command-center/pull/98).
Commissioning record: [issue #97](https://github.com/M17z2025/ai-command-center/issues/97).
Upstream baseline: `8339e20f67a0e4ba4cdc815a50b046a43218871f`.

## Verified source candidate

Commit `3719228204ee83debaa442bec16a49f7239197e9` passed:

| Check | Exact GitHub evidence |
|---|---|
| Control-plane validation and full regression suite | [run 36555229342](https://github.com/M17z2025/ai-command-center/actions/runs/36555229342) |
| Mesh runtime, full regression suite and deterministic smoke | [run 36555229460](https://github.com/M17z2025/ai-command-center/actions/runs/36555229460) |
| Automation tests, image build, Linux supervisor and Compose | [run 36555229441](https://github.com/M17z2025/ai-command-center/actions/runs/36555229441) |

Automation job `109362662828` logs explicitly show 25 automation tests passing,
8 gstack tests passing, 2 real-process tests passing inside the Linux container,
successful non-root access to installed reference data and successful composed
VPS configuration validation. CI image ID:
`sha256:04823a935cc411e37623a47f1f814656c6b4aa4d23ae8142f2828dc7ac7bd471`.
This image was built in CI, not published to or deployed on OVH.

Local Python 3.12.14: full suite 123 tests OK, 1 Linux-only supervisor skip,
15.148 seconds. Control-plane validation passed. Deterministic smoke returned
COMPLETE for mission `41ce6cc1-9f59-40f8-aadb-e31353b4651e`. This is test-provider
orchestration evidence, not proof of live inference. The real gstack installer
downloaded and hash-verified four files at pin
`65bfb0ce49da807698359ca033a05709e342c684`; its eight tests passed.

Follow-up reporting regression file adds three locally passing tests (0.925
seconds): lost GitHub POST response reconciliation without rerunning work,
separate report write/token gates, and changed-ID replay rejection after a job
has completed. Final follow-up commit/CI identity belongs in PR #98; earlier green
runs above certify their named commit only.

Initial local failures were investigated and corrected: installed dependency
permissions required the configured Python environment; queue test helpers were
adapted to explicit connection closing; existing runner/mission database
connections now close on transaction exit. The final successful runs above
supersede those initial failed attempts without hiding them.

## Implemented boundaries

The queue, signed intake, scheduled project cycles, process supervision, recovery
holds, health/watchdog configuration, private evidence, safe GitHub reporting and
pinned gstack reference integration are implemented. Mutating automation remains
disabled. Changed PRs stop at independent-supervision holds; merging, product
deployment and user certification remain in #89/#92, with PR #96 retained.

## Deployment status and exact next gates

**OVH deployment: NOT PERFORMED / NOT VERIFIED.** No approved host alias/repository
path or live credentials were supplied in this implementation session. Docker
source was exercised in GitHub Linux CI, not on the target VPS.

1. Review final PR head and independent reports. Source review findings about replay,
   stale recovery, heartbeat fail-stop and SQLite closure were repaired and tested.
2. Provide approved existing OVH access and owner-provisioned runtime secrets through
   the private channel. Do not place values in GitHub. No new paid service is needed.
3. Use `docs/SIGMA_AUTOMATION.md` to replace the old timer with planning-only services.
   Record exact deployed source/image digest, redacted container UID/mount/health
   evidence, valid/forged/replayed webhook outcomes and real scheduled cycle IDs.
4. Verify actual restart/UNKNOWN-hold behavior, host watchdog, edge rate/TLS controls,
   backup/restore and safe GitHub outbox publication. Keep execution disabled.
5. Remediate existing worker credential isolation and exact-source checkout under
   independent security review. This is an engineering gate, not a request for the
   owner to waive security. Then prove one harmless opted-in branch/PR task before
   expanding project execution.
6. Apply existing repository protections and independent CI/security/user-test gates
   before any merge or product-specific release. Do not close #97 as operational
   until the live evidence is attached.

Runbook: [SIGMA_AUTOMATION.md](SIGMA_AUTOMATION.md). Independent role reports:
[advisory](SIGMA_AUTOMATION_ADVISORY.md), [security](SIGMA_AUTOMATION_SECURITY.md).
