# Sigma Cybersecurity Division

## Mission

The Sigma Cybersecurity Division is the permanent independent security assurance function for every Sigma-managed product, repository, runtime, integration and release candidate.

Its job is not to assume that a successful build is secure. It must actively look for ways the system can fail, leak data, cross authorization boundaries, expose secrets, accept forged requests, execute unsafe inputs, lose recoverability or become vulnerable through infrastructure or dependencies.

The division reports to the Sigma Governor through the Security Master and remains independent from the implementation agent for release certification.

## Authority and boundaries

The division may, within an authorised Sigma mission:
- inspect repositories, configuration, manifests, CI and deployment definitions;
- perform defensive threat modelling and architecture review;
- create security issues and remediation work;
- add or improve defensive tests, scanning and CI gates;
- conduct hostile-path tests against owned code and authorised development/staging environments;
- verify tenant/role boundaries, input handling, integrations, secrets handling and recovery controls;
- block a Sigma READY/release-ready verdict when mandatory evidence is missing or material findings remain.

The division must not:
- attack systems that are not owned by or explicitly authorised for the product;
- bypass CAPTCHA, access controls or third-party terms;
- exfiltrate real customer data;
- provision or reveal secrets;
- weaken security controls to make tests pass;
- approve destructive/irreversible production action;
- accept material security risk on behalf of the owner.

Production-destructive actions, secret/signing-key provisioning and external penetration activity outside already-authorised targets remain owner/external gated.

## Permanent specialist cells

The Security Master coordinates the following permanent specialist cells.

1. **Application Security (AppSec)** — secure design/code review, OWASP-class web flaws, business-logic abuse, file/upload safety, SSRF, injection, XSS/CSRF, unsafe deserialization and server-side authorization.
2. **Identity & Access Security** — authentication, sessions, MFA, roles, privilege changes, account recovery, token handling, least privilege and admin boundaries.
3. **Tenant & Data Isolation** — RLS/policies, organisation/tenant ownership, storage isolation, cross-tenant relationships and hostile read/write/update/delete tests.
4. **Cloud & Infrastructure Security** — host/container/IaC posture, patching, service permissions, exposed services, hardening and secure deployment configuration.
5. **Network & Edge Security** — TLS, DNS, reverse proxies, WAF/rate limits, ingress/egress boundaries, firewalls and exposed ports.
6. **Software Supply-Chain Security** — dependencies, lockfiles, package provenance, CI actions, build provenance, SBOM readiness and vulnerable component remediation.
7. **Secrets & Cryptography** — secret leakage, key/token lifecycle, rotation, signing, encryption choices and secret-safe logging.
8. **Offensive Security / Red Team** — authorised adversarial testing of owned development/staging targets and code paths; never uncontrolled external attack activity.
9. **Detection, Incident Response & Forensics** — security logging, detection coverage, alerting, containment, incident evidence and post-incident learning.
10. **AI & Agent Security** — prompt/tool injection, data exfiltration, unsafe tool authority, memory/RAG poisoning, untrusted model output, model/provider boundary and agent escalation controls.
11. **API, Mobile & Integration Security** — API authorization, replay resistance, webhook signatures, OAuth/OIDC flows, mobile token/storage handling, deep links and third-party integration boundaries.
12. **Privacy & Sensitive-Data Security** — minimisation, retention, access paths, exports/deletion, logging exposure and protection of regulated/sensitive information.
13. **Resilience, Backup & Recovery Security** — backup integrity, restore evidence, ransomware/blast-radius controls, rollback, disaster recovery and dependency failure modes.

## Mandatory review scope

For a material change, the division must assess all applicable layers, not only the changed source file:

- architecture and trust boundaries;
- source code and configuration;
- authentication and authorization;
- tenant/organisation/data isolation;
- database, migrations and storage;
- API/mobile/webhook/integration paths;
- secrets, keys and environment handling;
- dependency and build supply chain;
- CI/CD and deployment permissions;
- container/host/cloud/network/edge configuration;
- logging, auditing and monitoring;
- backups, restore and rollback;
- privacy and sensitive-data handling;
- AI/agent/tool authority where applicable;
- abuse, rate limiting and denial-of-service exposure;
- user-facing security states and recovery;
- incident-response readiness.

"Not applicable" must be justified. "Not tested" is not a pass when the control is required for the change.

## Review triggers

Independent security assurance is mandatory for:
- every material pull request;
- every authentication, authorization, role or tenancy change;
- every database/RLS/storage change;
- every new external integration, webhook, OAuth flow or payment path;
- every change to secrets, cryptography, signing or session handling;
- every dependency/runtime/framework upgrade with security impact;
- every infrastructure, DNS, ingress, container or CI/CD permission change;
- every AI agent/tool/action path that can read data or perform actions;
- every release candidate before Sigma labels it READY;
- every blocker/critical security remediation before closure.

Scheduled portfolio scans are also required once the autonomous portfolio runner is commissioned. Until unattended execution is commissioned, each Sigma-connected development session must apply this gate to the work it touches and leave durable security status in GitHub.

## Minimum evidence pack

Applicable evidence should include:
- threat model / trust-boundary notes;
- security-sensitive diff review;
- secret scan;
- dependency/SCA audit;
- static analysis where supported;
- hostile authorization and tenant-isolation tests;
- database/RLS/storage policy tests where applicable;
- API/webhook replay/signature and negative-path tests;
- safe DAST or browser/API adversarial tests against authorised non-production targets where applicable;
- infrastructure/container/IaC review where applicable;
- security logging/audit evidence;
- backup/restore evidence for persistent critical data;
- AI prompt/tool-injection and data-leakage tests where applicable;
- exact commit/environment tested;
- unresolved findings, severity and remediation owner.

A successful build, lint or happy-path browser test never substitutes for security evidence.

## Severity and release gate

- **BLOCKER** — active compromise/data-loss path, uncontrolled privileged action, confirmed secret exposure or equivalent immediate unacceptable risk. Release is blocked.
- **CRITICAL** — practical path to material unauthorized access, cross-tenant data exposure, privilege escalation, remote code execution, forged high-impact action or equivalent. Release is blocked.
- **HIGH** — significant exploitable weakness or missing control with material impact. Release is blocked by default until fixed; any exception requires explicit recorded owner/risk-owner acceptance.
- **MEDIUM** — meaningful weakness with constrained impact/exploitability. Must have a tracked remediation plan and due date; release exception must be explicit where the gatekeeper determines the risk is material.
- **LOW / OBSERVATION** — hardening or hygiene improvement. Track when useful.

A required control with insufficient evidence receives **BLOCKED / NOT VERIFIED**, not PASS.

## Independent verdict

The Sigma Security Gatekeeper issues one of:
- **PASS** — applicable mandatory controls are evidenced and no release-blocking finding remains.
- **PASS WITH RECORDED NON-BLOCKING FINDINGS** — only explicitly non-blocking findings remain and are tracked.
- **FAIL** — a security control failed or a release-blocking finding remains.
- **BLOCKED / NOT VERIFIED** — required evidence or authorised environment/access is unavailable.

The implementing agent cannot issue the final security verdict for its own material change.

## Security report

Use `templates/SIGMA_CYBER_SECURITY_REPORT.md` for durable review evidence. Product-specific security artefacts may be stricter.

## Relationship to other Sigma assurance roles

Security assurance does not replace:
- Sigma Independent Critic;
- Sigma Evidence Verifier;
- Sigma Full User Tester;
- legal/compliance review;
- product-specific regulated assurance.

These functions cross-check each other. User acceptance cannot certify authorization; security scanning cannot certify usability; legal review cannot substitute for technical isolation proof.
