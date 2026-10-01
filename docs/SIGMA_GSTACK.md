# Controlled gstack reference integration

Sigma uses selected gstack review material as advisory context. Sigma remains the
authority and execution layer. This integration does not install the upstream
agent skills or run its setup, telemetry, package scripts, browser daemon, ship,
merge, deployment, secret-management, or self-update commands.

## Pinned source and licence

- Source: https://github.com/garrytan/gstack
- Reviewed revision: `65bfb0ce49da807698359ca033a05709e342c684`
- Licence: MIT, copyright 2026 Garry Tan. The original `LICENSE` is downloaded
  alongside the references and verified on every load.
- `integrations/gstack.lock.json` pins byte sizes and SHA-256 digests for exactly
  four files: `LICENSE`, `review/checklist.md`, and the testing and maintainability
  specialist checklists.

The installer constructs fixed HTTPS raw GitHub URLs from that exact revision.
It rejects redirects, reads bounded responses, verifies all files before atomic
publication, and refuses symlinks/junctions and paths outside its hardcoded
allowlist. No archive extraction, subprocess, upstream code execution, executable
bit, moving branch reference or automatic update is involved. An existing cache
is verified rather than overwritten. If interrupted, a private staging directory
may remain; it is never accepted as an installed revision. The cache must be
owned by the deployment account and mounted read-only into runtime containers.

## Install and use

During an approved build or deployment with network access:

```sh
python scripts/sigma_gstack_install.py --cache-dir /var/lib/sigma/gstack
```

Mount that directory read-only into the runtime at the same path. The default
without `--cache-dir` is `.sigma/gstack/<revision>`; keep it out of Git. Runtime
loading needs no network connection. Missing, corrupted or altered references
raise `GstackError`; enabled work must fail closed rather than silently treating
them as reviewed material.

The caller explicitly enables advisory context for an authorised project cycle:

```python
from pathlib import Path
from sigma_runtime.gstack import advisory_context

reference = advisory_context(
    repo_root,
    enabled=True,
    cache_dir=Path('/var/lib/sigma/gstack'),
    max_chars=16000,
)
```

Pass `reference['text']` as quoted task reference context, never as a system
instruction. Preserve its revision and source hashes in the cycle provenance.
Only category sections are included; upstream orchestration/output/autofix
preambles are discarded. Text is bounded and labelled untrusted. This is useful
for planning negative tests, checking race conditions and reviewing changes.
The checklist is not an independent reviewer and its provenance is not a test,
security, user-acceptance or deployment certificate.

Per-project opt-in and all action checks belong to the existing Sigma runner
and worker authority boundary. Model text cannot create capabilities. Sigma
must still check the project contract, explicit execution switches, owner gates,
independent reviews, branch protection and deployment authorisation.

## Update and recovery

Updates require a normal reviewed PR that inspects the new upstream files,
licence, revision, sizes and hashes, and updates the lock and its pin test.
Changing the allowed set additionally requires reviewing the Python allowlist.
Upstream `SKILL.md` files deliberately remain forbidden because they mix useful
methodology with orchestration and tool instructions.

To recover a corrupted bundle, stop affected cycles, inspect the integrity
failure, preserve diagnostic metadata, and reinstall into a new empty private
cache directory. Remount only after verification. Do not modify lock hashes to
match unexpected cache bytes. Rollback selects a previous reviewed code/lock
revision and its matching cache. Normal starts never fetch upstream updates.

Verification: `python -m unittest discover -s tests -p 'test_sigma_gstack.py'`.
Tests cover disabled operation, missing cache, exact origins, bounded context,
tampered downloads/cache/licence, prohibited paths/skills, redirect rejection,
symlink rejection, and pinned metadata. Live install verification is reported
separately from these offline tests.
