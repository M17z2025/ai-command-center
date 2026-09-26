# Security Baseline

This is the minimum engineering baseline for every Sigma-managed product. Product-specific controls may be stricter.

The permanent independent assurance function is the [Sigma Cybersecurity Division](../headquarters/security/README.md). Material development and release candidates use [the Sigma Cybersecurity Review Report](../templates/SIGMA_CYBER_SECURITY_REPORT.md).

## Security assurance rule

- Security is a release gate, not a post-release checklist.
- The implementing agent cannot self-certify the final security verdict for its own material change.
- Required controls must be evidenced against the exact commit/environment.
- A required control that is not tested is **BLOCKED / NOT VERIFIED**, not PASS.
- BLOCKER, CRITICAL and HIGH findings block release by default.
- Adversarial testing is limited to owned/authorised code and environments.

## Secrets and cryptography

- No secrets in source, issues, PRs, logs, screenshots, test fixtures or committed environment files.
- Commit only variable names in `.env.example`.
- Rotate any credential that is accidentally exposed.
- Separate development, staging and production credentials.
- Keep privileged/service keys server-side and scope them to least privilege.
- Document signing/encryption/key-rotation boundaries where cryptography is material.
- Never invent or silently substitute production credentials.

## Authentication, sessions and authorization

- Enforce authorization server-side on every privileged/data-sensitive operation.
- Never treat hidden UI controls as access control.
- Privileged/admin actions require explicit role/permission checks.
- Sensitive role changes and authentication events must be auditable where applicable.
- Session/token expiry, revocation, replay and recovery paths must be tested where material.
- Default to deny when identity/role/tenant context is missing or ambiguous.

## Multi-tenancy, databases and storage

For tenant/organisation systems:
- every tenant-owned record must have an explicit secure ownership model;
- database-level RLS is preferred for Supabase/Postgres;
- policies are deny-by-default;
- service-role use remains server-side and cannot become a blanket authorization bypass;
- test hostile cross-tenant reads, writes, updates, deletes, object-ID substitution and storage access;
- unique constraints, joins, foreign keys and RPC/functions must not permit cross-tenant association;
- files, exports, background jobs and admin/reporting paths receive the same isolation review.

## Application and API security

- Validate untrusted input at trust boundaries.
- Parameterize database queries.
- Encode output appropriately.
- Restrict file type, size, path and content handling for uploads.
- Protect server-side URL fetches against SSRF.
- Protect state-changing web flows against applicable CSRF/replay risks.
- Verify authorization independently of client-provided IDs/roles.
- Rate-limit abuse-sensitive endpoints and expensive operations.
- Fail closed on malformed, expired or unverifiable security tokens.
- Do not expose stack traces, secrets or sensitive internals to end users.

## Integrations, webhooks and payments

- Verify webhook signatures and timestamps/replay protections where supported.
- Use idempotency for retried financial or consequential operations.
- Validate OAuth/OIDC state, redirect and token boundaries.
- Do not store raw card data.
- Maintain immutable/auditable financial identifiers where required.
- Treat third-party responses and model/tool outputs as untrusted until validated.

## AI and agent security

For AI/agent/tool systems:
- scope tools and data access to least privilege;
- treat prompts, retrieved documents and external content as untrusted input;
- test prompt/tool injection and data-exfiltration paths;
- prevent model output from directly granting authority;
- separate user instruction, system policy, credentials and tool permissions;
- bound autonomous actions and preserve an auditable action trail;
- test memory/RAG poisoning and cross-user/tenant leakage where applicable.

## Dependencies and software supply chain

- Lock dependencies and avoid unpinned production dependency resolution.
- Run dependency/security scanning where supported.
- Review high-impact runtime/framework upgrades for security regressions.
- Pin or otherwise control CI actions/build tooling where practical.
- Prefer reproducible builds and maintain package/build provenance evidence where practical.
- Record and remediate known exploitable dependency findings before release.

## Infrastructure, containers, network and edge

- Minimise exposed services and ports.
- Use least-privilege service/runtime identities.
- Keep operating systems, runtimes and base images maintained.
- Review Docker/container privilege, filesystem, secret mounts and network exposure.
- Require TLS for externally exposed authenticated/sensitive traffic.
- Review DNS, proxy/ingress, firewall/WAF/rate-limit and origin exposure where applicable.
- Infrastructure-as-code and deployment configuration receive security review like application code.

## Logging, detection and incident response

- Log security-relevant events without logging secrets or unnecessary sensitive data.
- Include correlation/request IDs where practical.
- Preserve audit history for destructive, privileged or financial operations.
- Critical products require a documented incident-response path and evidence sources needed to investigate an event.
- Security alerts should be actionable and linked to an owner/process, not collected without response.

## Privacy and sensitive data

- Minimise collection and retention.
- Restrict exports, admin/reporting and deletion paths.
- Prevent sensitive values from appearing in logs, analytics or screenshots.
- Apply product/jurisdiction-specific privacy and regulated-data requirements in addition to this baseline.

## Backups, recovery and resilience

Products with persistent material data require documented backup and restoration procedures.
- A backup that has never been restoration-tested is not a complete recovery control.
- Record recovery point/recovery-time expectations where material.
- Test rollback/recovery for risky migrations.
- Reduce ransomware/blast radius by separating backup authority and production write authority where practical.

## Security evidence

Applicable release evidence should include:
- exact commit/environment;
- threat/trust-boundary review;
- security-sensitive diff review;
- secret scan;
- dependency/security audit;
- hostile authorization/tenant tests;
- database/RLS/storage tests;
- API/webhook replay/signature tests;
- safe DAST/adversarial tests against authorised non-production targets where applicable;
- infrastructure/container/IaC review;
- logging/audit evidence;
- backup/restore evidence for persistent critical data;
- AI security tests where applicable;
- open findings and retest status.

## Production changes

Destructive production actions, irreversible migrations, secret/signing-key provisioning, external attack activity outside already-authorised targets and material security-control reductions require explicit owner/external authority.
