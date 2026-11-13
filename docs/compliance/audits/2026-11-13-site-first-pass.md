# Mi7z / Lycia / Sigma website compliance audit — first pass

**Assessment date:** 13 November 2026 (UTC)  
**Scope:** 28 Base44 app records + public-facing custom domains + GitHub source of 3 reviewed products.  
**Status:** PARTIAL / NOT CERTIFIED. This is initial discovery and evidence collection, not a penetration test, privacy opinion, ISO certification or production acceptance.  
**Owner issue:** [#165](https://github.com/M17z2025/ai-command-center/issues/165). Domain issue [#166](https://github.com/M17z2025/ai-command-center/issues/166).

## What was actually checked
1. Connected Base44 account: `list_user_apps` returned 28 apps on 13 Nov 2026.
2. Called provider published-URL endpoint for every app: 20 published, 8 unpublished.
3. Queried custom-domain entries for every published app. Verification fields for most were historical snapshots, **not** new checks.
4. Rechecked four previously unverified domains against the Base44 provider at ~06:47 UTC; all remained `unverified`.
5. Requested a new Base44 security scan for each of 28 applications; **do not** confuse `scanning`, `scan_failed` or `out_of_date` with a completed assessment.
6. Public page crawl (not authenticated browser/JS execution) of Humanit, BodyFit and Lycia corporate. SAH public page returned metadata but no readable content. Many other domains were inaccessible to the crawler, which **does not** establish an outage.
7. Source-code review of Humanit (`accountIntegrity.ts`, `Legal.jsx`, `communicationsCore`), BodyFit (`PolicyPage.jsx`, `RegistrationCompliance.jsx`, `processInactiveAccounts`) and Lycia (`PrivacyPolicy.jsx`, `shuftiProWebhook`) plus Invoiceit security-sensitive backend functions.

## Base44 portfolio — published URLs and mapped domains
**Key:** `verified (historic)` means Base44's latest saved verification at query time, not an independent live DNS/TLS test; `unverified (13 Nov)` was freshly checked at the provider. A published Base44 slug does not establish an operational custom domain.

| Product | Published Base44 URL | Custom domain(s) | First-pass status |
| --- | --- | --- | --- |
| Winkday — official site | https://winkday-official-website-36bfbdee.base44.app | winkday.app **unverified (13 Nov)** | **P0 domain / security review** |
| Alphamita | https://alphamita.base44.app | alphamita.com verified (historic) | Pending site/browser review |
| Invoiceit | https://invoiceit-by-mi7z.base44.app | invoiceit.mi7z.com verified (historic) | **P0 independent auth/security verification** |
| Lycia Zambia | https://lycia-zambia-gateway.base44.app | lycia.co.zm verified (historic); zambia.lycia.co.uk **unverified (13 Nov)** | P0 domain, privacy/KYC scope |
| Humanit | https://humanit-by-mi7z.base44.app | ihumanit.com; humanit.mi7z.com verified (historic) | **P0 HMAC secret, privacy and policy accessibility** |
| CSK Mega Structures | https://csk-build-pro.base44.app | msgroup.mi7z.com verified (historic) | Pending |
| Synergy Alliance Holdings | https://synergy-alliance-hold.base44.app | sah.co.zm verified (historic) | Public crawler returned no readable body |
| Lycia Limited | https://lycia-limited.base44.app | lycia.co.uk verified (historic) | **P1 legal/subprocessor table correction** |
| Vinci Gateway | https://vinci-gateway-pro.base44.app | vinci.mi7z.com verified (historic) | Pending |
| Total Mining Intelligence | https://total-mining-intelligence.base44.app | tmi.lycia.co.uk verified (historic) | P1 pricing/financial-claims review |
| Synarula | https://synarula.base44.app | synarula.com verified (historic) | P1 privacy/entity identity |
| SyncBase | https://sync-base-core.base44.app | none attached | Security scan failed; retry and investigate |
| Secure DX Zambia B | https://secure-dx-link.base44.app | none attached | Pending regulated-processing review |
| Friday AI website | https://friday-ai-5c6d319b.base44.app | friday.mi7z.com **unverified (13 Nov)** | P0 domain, voice/AI transparency |
| Tattooit | https://vague-ink-vision-flow.base44.app | itattooit.com; tattooit.mi7z.com verified (historic) | Privacy/RLS review |
| Mi7z | https://mi7z-core-lab.base44.app | mi7z.com verified (historic) | Pending |
| Signit | https://signit-by-mi7z.base44.app | signit.mi7z.com verified (historic); signitly.com **unverified (13 Nov)** | P0 domain, document security/RLS review |
| Legalit | https://legalit-nexus-pro.base44.app | legalit.mi7z.com verified (historic) | P1 confidentiality/professional claims |
| BodyFit | https://mi7z-body-flow.base44.app | mybodyfit.ai; bodyfit.mi7z.com verified (historic) | **P0 retention and minors risk** |
| Marketit | https://marketit-ai-flow.base44.app | umarketit.com; marketit.mi7z.com verified (historic) | P1 marketing/consent review |

**Unpublished on provider (8):** Imoition, NexusHosting, Synergy AI Pay, CryptoPay Exchange MVP, Secure DX Zambia A, My Culinary Lab, TaskFlow, InvestTrack. Not publicly published via a Base44 slug does not mean no other hosting or domain exists. Account records and product sources still require assessment.

## Findings to remediate

### A. Humanit (P0)
- **Confirmed code concern:** `base44/shared/accountIntegrity.ts` uses a public fixed fallback `"fallback-hash-key"` when `GUEST_IP_HASH_SECRET` is absent for HMAC hashing of email. No claim this happened in production; remove fallback and prove live configuration/rotation as appropriate. [Product issue #54](https://github.com/M17z2025/ihumanit/issues/54).
- The public legal hub at https://ihumanit.com/legal lists specific policies and makes a blanket “UK GDPR and EU GDPR compliant” claim. Require substantiation and legal sign-off rather than taking a website label as proof.
- A non-JS crawler requesting direct legal document URLs received a generic link index; React source defines actual document views. Independently test browser accessibility, SSR and crawl behaviour. The data deletion page is substantive and acknowledges limits around provider/storage backup removal.
- Older security scan claimed unprotected `communicationsCore` endpoints; current main source contains public/self/admin action classification and checks. Do not label the stale result a current exploit without retest.

### B. BodyFit (P0)
- Public homepage https://bodyfit.mi7z.com advertises 45-day inactivity warning and 60-day data deletion, AI coaching and younger-user safety.
- **Confirmed code concern:** `base44/functions/processInactiveAccounts/entry.ts` calls `User.list('-created_date', 500)` once with no pagination; processes no more than that first page per invocation. Some deletion errors are swallowed. Needs >500 account and provider/storage tests. [Product issue #3](https://github.com/M17z2025/mybodyfit/issues/3).
- Registration acceptance checkbox states 16+ or 13+ with parental acknowledgement. Verify age verification, UK Children's Code, health-related privacy and appropriate medical purpose classification.
- Public legal links exist but crawler returned generic site index for policy subroutes; policy source is loaded from a backend function. Confirm unauthenticated policy visibility in real browser.

### C. Lycia Limited (P1)
- https://lycia.co.uk has extensive policy, cookie, data subject rights and security centre pages.
- Public https://lycia.co.uk/privacy-policy section 9 **Location** column includes “Per approved retention schedule” for vendor processing location. Fix inaccurate labels and verify real DPA/transfer geography. [Product issue #2](https://github.com/M17z2025/lycia-limited/issues/2).
- Website states legal/data protection/solicitor review complete, but audit evidence was not provided; qualify pending substantiation.
- Stale security scan flagged Shufti webhook; current source **rejects** absent secret/signature. Do not rely on stale flagged text or assume this is exploitable without negative-path tests.

### D. Invoiceit (P0 review)
- Stored stale scan highlighted `sendTemplatedEmail` and `seedEmailTemplates` as missing authentication, but `main` code currently checks `base44.auth.me()`, tenant membership, permissions or tenant-admin role. Re-run and independently test malicious cross-tenant IDs instead of accepting a scanner false positive as truth.
- Because the app handles invoice/payment communications, test actual tenant isolation, consent, email secrets, replay, financial record integrity and complaint/erasure paths.

### E. Winkday / Friday website (P0 review)
- Fresh **up-to-date** security scans detected 7 dependency advisories in each website (zod/Vite advisories; same dependency set), needing version, dev-only exposure, exploitability and vendor advisories review. They also found no backend function or hardcoded-secret issue in the website code. The scan **does not** test Friday's Android voice stack or Winkday mobile backend.
- Winkday scan suggested one RLS review for `CelebrationGreetingPack`: public read might be intentional; confirm creation/update/delete restricted to authorized catalogue administrators. Do not blindly close public catalogue read.
- Their attached custom domains are unverified at the hosting provider on 13 November, though the Base44 URLs are published.

### F. Signit, Tattooit and other products
- Older, **not yet fresh-completed** scans show potentially serious RLS or backend findings (e.g., Signit and Tattooit). Reassess exact current source, real RLS policy and negative-path tests. This report does not assert they are currently exploitable.
- All other 28 app records have been enrolled in fresh scans; product-specific issue triage must follow scan completion and manual review.

## Release gates / next evidence
- Do not declare any site GDPR/AI Act/ISO compliant yet.
- Match each published custom domain to correct legal entity and hosting runtime, especially during Base44 → Leaseweb/OVH migration.
- For each app, record approved compliance manifest, lawful bases and transfer map; children/health/financial/AI transparency where applicable.
- Test cookies before/after reject/accept/withdraw with a real browser's network and storage panels, public policy access without authentication, accessibility, admin separation, DSAR/deletion requests, known-key and cross-tenant abuse, direct-origin and custom domain HTTPS, and mobile flows.
- Retain exact-code revision, provider scan date/status, browser evidence, independent review and deployment record. Missing evidence is **NOT VERIFIED**.
- Cross-link fixes to master [#165](https://github.com/M17z2025/ai-command-center/issues/165) and domain [#166](https://github.com/M17z2025/ai-command-center/issues/166).

**Tool access limitation:** the public web crawler cannot execute authenticated application flows or always render JavaScript content. Local container DNS requests were not available. Provider published URL/verification status and GitHub code are independent evidence classes; a custom domain displaying `unverified` at Base44 is not proof of total public outage.
