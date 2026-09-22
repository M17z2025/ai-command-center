# Sigma Development Command Center Status

Last updated: 2026-09-22
Repository: `M17z2025/ai-command-center`
Default branch: `main`

## Control-plane rules

Repository evidence overrides chat history. Product code stays in product repositories. Material development uses issue/branch/PR review, secrets are never committed, security controls are not weakened to make tests pass, multi-tenant products require hostile isolation evidence, and destructive/production-impacting actions remain owner-gated. Material user-facing READY claims additionally require the independent Sigma Full User Tester on an approved deployed preview/staging candidate.

## Active portfolio

| Project | Sigma classification | Highest-priority executable next task |
| --- | --- | --- |
| Sigma Development Command Center | READY for supervisory use; runner phase 1 **CHANGES REQUIRED** | Rebase/synchronise PR #10 with current `main`, preserve GET-only discovery, rerun unit/control-plane CI on the new exact head, then require mergeable + green before READY. |
| Mi7z Web | **CHANGES REQUIRED / SECURITY REMEDIATION REQUIRED** | Fix PR #2's two TypeScript errors, upgrade vulnerable `next@15.5.3`, then obtain exact-head dependency audit + typecheck + build + Playwright. |
| Alysha AI Platform | RC2 source **READY**; trusted release **BLOCKED**; Supabase source evidence **COMPLETE**; final DB reconciliation **BLOCKED ON PREVIEW** | Continue safe executable app-layer hardening under issue #694 while owner/spend decision #661 commissions a distinct Supabase Preview. Do not touch production migration history or PR #390 lineage. |
| Invoiceit by Mi7z | **CHANGES REQUIRED / P0 SECURITY HARDENING ADVANCED** | Create safe Tenant A/Tenant B + restricted-user fixtures, prove hostile direct-call read/write authorization, finish read-side capability audit, and add exact-head CI. |
| Lycia Zambia | **CHANGES REQUIRED / CONTENT-COMPLIANCE + CONTRACT/CI RISK** | Stop adding unsourced factual market claims, build claim-level source/date evidence, add `.sigma/project.yaml` + `PROJECT_STATUS.md` + CI/tests, then perform deployed user/security verification. |
| Marketit | **CHANGES REQUIRED / SECURITY MIGRATION REQUIRED** | Protect `PlatformConnections`/`CredentialSetupSessions`, continue entity-native RLS migration, hostile-test service-role paths, and reduce 168 isolation findings to zero/approved exceptions with exact-head CI. |
| Total Mining Intelligence | **CHANGES REQUIRED** | Complete issue #1 contract/status/data-provenance/security baseline and establish exact-head quality evidence. |
| BodyFit | **CHANGES REQUIRED** | Complete issue #1 contract/status/privacy/health-integration baseline and exact-head verification. |
| Tattooit | **CHANGES REQUIRED** | Complete issue #1 contract/status/role/ownership/upload baseline and exact-head verification. |
| Legalit | **CHANGES REQUIRED / SECURITY WORK IN PROGRESS** | Add `.sigma/project.yaml` and CI/tests, then prove cross-organisation OrgMember/conflict-scope isolation and safe return navigation. |
| Signit by Mi7z | **CHANGES REQUIRED** | Complete issue #1 contract/status/document-signature/audit authorization baseline and exact-head verification. |
| Humanit | Voice source candidate **READY FOR MERGE REVIEW**; production Voice **BLOCKED** | Merge PR #17 through normal review, then prove a connected-account GA `gpt-realtime` session before enabling/publishing Voice and running mobile user acceptance. |
| Designit AI Platform | **CHANGES REQUIRED for Sigma state**; reviewed CI green | Complete issue #93 fact-based contract/status baseline without regressing the current quality evidence. |
| Lycia Limited | **CHANGES REQUIRED** | Clear typecheck debt, add tests/CI + negative authorization proof, then verify HMRC/Shufti/SMTP and governance evidence. |

## Material review — 22 September 2026

### Alysha — source-history evidence completed; safe Preview is now the hard gate

Issue #577 now records the Supabase source-evidence phase **complete**: all 23 same-name mismatches reviewed, all 13 originally remote-only migrations reconstructed from durable production/source evidence, all 21 baseline local-only migrations conservatively classified, and aggregate reconciliation contract PR #663 merged green. Historical application remains unresolved where evidence does not prove it; no production DDL, replay, repair/reset/merge or history mutation occurred.

Final migration-chain reconciliation is now **BLOCKED ON SAFE SUPABASE PREVIEW**. Issue #661 confirms only production `main` currently exists and branch creation can incur cost, so creation of a distinct non-production Preview requires an explicit owner/spend decision. Production `main` must not be used as substitute Preview evidence.

Three forward security candidates remain safely staged outside the active migration chain and have green exact-head Web Quality evidence: PR #664 (trigger-function EXECUTE ACL least privilege), PR #667 (task/job authority immutability), and PR #668 (current-model decision/runtime scope integrity). They are source-prepared only and are not apply-ready until Preview proves them and a separate production owner/admin gate is satisfied.

Application/mobile-call hardening has also continued. PR #693 merged after exact-head Mobile API Type Safety and Web Quality both passed; it bounds authenticated task-scoped MCP request envelopes before call-task lookup/persistence. The next executable P1 is issue #694: bound authenticated `POST /api/mobile/v1/calls` request parsing and persisted call constraints without weakening mobile auth/lifecycle/provider authority.

RC2 remains separately blocked: PR #390 source candidate is still READY, but trusted signing/publication requires the commissioned Cloudflare→VPS HTTPS mobile API origin. `main` branch protection remains owner/admin-blocked under issue #470.

### Lycia Zambia — public factual expansion increased the release risk

Latest `main` is `fa744e1661cd15cbac720e23f38ee46f1501ea3`. New country/Dubai content adds specific mining, trade-volume, tax/free-zone, FATF/AML, logistics, economic, risk-grade and Lycia operational-status claims. The repository still has no `.sigma/project.yaml`, no `PROJECT_STATUS.md`, and the exact latest head has zero GitHub workflow runs. A generic disclaimer is not claim-level evidence. Issue #1 has been updated to require a source/date claim register, verification of Lycia-specific operational claims, contract/status/CI/tests and independent user acceptance before READY.

### Marketit — meaningful boundary hardening, but the dominant isolation blocker remains

Latest status commit `6316f49f00b0c6f9bf8bc997f4be4004710bb50a` records security-tested functional head `051c03732102d20738a6f420cd586b289f9f9e9e`: local tests 15/15, typecheck, lint, production build and high/critical dependency audit pass. All direct frontend `PublishingQueue` reads are now routed through protected controls; API authorisation visibility/creation is more tightly capability-scoped; placeholder production callback domains were removed.

However, exact-head GitHub Actions evidence for `051c037...` is absent and the strict security audit still reports **168 tenant-isolation findings**. Issue #1 has been updated; Marketit remains **CHANGES REQUIRED / SECURITY MIGRATION REQUIRED**.

### Invoiceit — further source hardening landed, runtime proof still blocks READY

Latest status head `2b6586ecceb73f82c7c2406ec4359fb18d4b524b` records new escaping for identified core invoice/quote/statement/receipt/reminder email/document HTML, protected `documents.view` audit-history reads, safer currency fallback and more jurisdiction-neutral labels. Exact latest-head GitHub workflow lookup still returns zero runs. Safe runtime still lacks two independent tenants/restricted users, so hostile authorization cannot yet be proven. Issue #3 has been refreshed and remains **CHANGES REQUIRED**.

### Humanit

PR #17 remains open, non-draft and mergeable at exact head `01b2a940930a5c8d0cf81061c92eba9220fccc81`; its Humanit Quality Gate is green. Source candidate is READY FOR MERGE REVIEW. Production Voice remains BLOCKED until the connected production-approved OpenAI account proves GA `gpt-realtime` session creation, followed by controlled Base44 enable/publish and mobile acceptance.

### Sigma runner

PR #10 remains open/non-draft/mergeable at exact head `2f829b032170ee2391aa1665e3e1609631ab94f2`, but it is still diverged from `main` (9 commits ahead / 7 behind at this review point). Historical exact-head CI is not sufficient for the current merge result. Issue #9 remains **CHANGES REQUIRED — CURRENT-MAIN SYNCHRONISATION + FRESH CI**. Its GET/read-only authority boundary must remain unchanged.

## Unchanged owner / infrastructure gates

1. Alysha issue #661 — explicit owner/spend approval to commission a distinct Supabase Preview branch.
2. Alysha issue #470 — repository-admin branch protection/ruleset activation for `main`.
3. Alysha RC2 — commissioned Cloudflare→VPS public HTTPS origin before trusted Android signing/publication.
4. Sigma issue #4 — command-center public/private visibility decision; public metadata exposure remains a governance risk even though no secret is recorded.
5. AutoHedge — dedicated private product repository required; do not merge its production branch into Mi7z corporate `main`.
6. Secure DX — dedicated product repository/registry entry and independent role fixtures remain required before durable Sigma certification.
7. Humanit Voice — connected-account GA realtime proof and publish/device test gate.

## Security / data risk summary

- Marketit's 168 tenant-isolation findings remain the largest confirmed portfolio data-separation backlog.
- Invoiceit has strong source hardening but still lacks hostile two-tenant/restricted-user runtime proof and exact-head CI.
- Lycia Zambia now carries increased legal/reputational content risk from unsourced public tax/regulatory/trade/mining/business-status claims.
- Mi7z Web's vulnerable Next.js release remains a release blocker.
- Alysha production migration/history mutation remains prohibited without Preview evidence and explicit owner/admin approval.
- Legalit still lacks hostile cross-organisation/conflict-scope proof.
- User/browser smoke never substitutes for direct hostile authorization/security testing.

## Adoption state

Verified contract/status baseline: Mi7z Web, Alysha, Invoiceit, Marketit and Humanit.

Legalit and Lycia Limited have durable status but incomplete Sigma adoption. Lycia Zambia, TMI, BodyFit, Tattooit, Signit and Designit retain repository-local onboarding orders. No evidence found in this review changes those classifications.

## Verification boundary

READY/CHANGES REQUIRED/BLOCKED applies only to the exact repository/task evidence stated here. It does not imply production deployment, live-account success, physical-device acceptance, legal/compliance approval or complete end-user acceptance unless those gates are explicitly evidenced.