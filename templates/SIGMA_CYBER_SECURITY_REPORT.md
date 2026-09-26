# Sigma Cybersecurity Review Report

## Review identity
- Product:
- Repository:
- Issue / PR:
- Exact commit SHA:
- Environment / deployment tested:
- Review date:
- Implementing agent/team:
- Independent security reviewer/gatekeeper:

## Change and attack surface
- Change summary:
- Trust boundaries affected:
- Data classifications affected:
- Roles/tenants affected:
- External integrations affected:
- Infrastructure/deployment affected:
- AI/agent/tool authority affected:

## Required control matrix

| Area | Applicable? | Evidence / command / test | Result | Finding IDs |
| --- | --- | --- | --- | --- |
| Threat model / trust boundaries | | | | |
| Authentication / sessions / MFA | | | | |
| Authorization / privilege boundaries | | | | |
| Tenant / organisation isolation | | | | |
| Database / RLS / storage isolation | | | | |
| Input/output / injection / SSRF / uploads | | | | |
| API / webhook / replay / signatures | | | | |
| Mobile / OAuth / token storage / deep links | | | | |
| Secrets / keys / signing / crypto | | | | |
| Dependency / supply-chain / provenance | | | | |
| Static analysis / secret scan | | | | |
| Infrastructure / container / IaC | | | | |
| Network / TLS / DNS / edge | | | | |
| Logging / audit / detection | | | | |
| Backup / restore / rollback / resilience | | | | |
| Privacy / sensitive-data exposure | | | | |
| AI / prompt-tool injection / exfiltration | | | | |
| Authorised adversarial / DAST testing | | | | |

For every required row, use PASS / FAIL / NOT VERIFIED / N/A. N/A requires a short justification.

## Hostile-path tests
Record direct negative tests, not only happy-path UI evidence.

- Cross-role:
- Cross-tenant / cross-organisation:
- Direct API/function calls:
- ID/object substitution:
- Token/session/replay:
- Forged webhook/integration input:
- File/URL/input abuse:
- Rate/abuse controls:
- Other:

## Findings

| ID | Severity | Description | Exploit/impact | Evidence | Remediation | Status |
| --- | --- | --- | --- | --- | --- | --- |

Severity: BLOCKER / CRITICAL / HIGH / MEDIUM / LOW / OBSERVATION.

## Release decision

Security verdict:
- [ ] PASS
- [ ] PASS WITH RECORDED NON-BLOCKING FINDINGS
- [ ] FAIL
- [ ] BLOCKED / NOT VERIFIED

Release-blocking findings open:
Required controls not verified:
Risk exceptions / owner approvals (link only; never secrets):
Retest evidence:

## Gatekeeper statement

The final verdict is independent from the implementation agent. A build, lint pass, source review or user-facing smoke test does not substitute for the applicable security evidence above.
