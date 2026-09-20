# Security Baseline

This is the minimum engineering baseline. Product-specific controls may be stricter.

## Secrets

- No secrets in source, issues, PRs, logs or screenshots.
- Commit only variable names in `.env.example`.
- Rotate any credential that is accidentally committed.
- Separate development, staging and production credentials.

## Authentication and authorization

- Enforce authorization server-side.
- Never trust hidden UI controls as access control.
- Privileged/admin actions require explicit role checks.
- Sensitive role changes and authentication events should be auditable.

## Multi-tenancy and databases

For tenant systems:
- every tenant-owned table must have an explicit tenant key or an equivalent secure ownership model;
- database-level RLS is preferred when Supabase/Postgres is used;
- deny-by-default policies;
- service-role use must remain server-side;
- test cross-tenant reads, writes, updates, deletes and storage access;
- unique constraints and foreign keys must not allow cross-tenant association.

## Input and output safety

- validate untrusted input;
- parameterize database queries;
- encode output appropriately;
- restrict file type/size/path for uploads;
- protect against SSRF for server-side URL fetches;
- rate-limit abuse-sensitive endpoints.

## Payments and finance

- verify webhook signatures;
- use idempotency;
- do not store raw card data;
- maintain immutable/auditable financial identifiers where required.

## Logging

- log security-relevant events without logging secrets;
- include correlation IDs where practical;
- preserve audit history for destructive or financial operations.

## Dependencies and CI

- lock dependencies;
- run dependency/security scanning where supported;
- keep runtime/framework versions maintained;
- block merge on failed required checks.

## Backups and recovery

Products with persistent data require documented backup and restoration procedures. A backup that has never been restoration-tested is not considered a complete recovery control.

## Production changes

Destructive production actions, irreversible migrations and security-control reductions require explicit owner approval.
