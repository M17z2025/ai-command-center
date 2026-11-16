# Sigma Group-Wide Regulatory & AI Compliance Standard

**Status:** Proposed governance baseline, not a certification or statement that any application is compliant.  
**Effective scope after approval:** all production and pre-production Sigma-managed products, AI agents, websites, mobile apps, integrations and infrastructure in the active portfolio. Archived/consolidated repositories are inventoried but not independently certified.

## Principle
Build once; assess each product and jurisdiction individually. **No evidence = no compliance pass.** An ISO framework, Vanta subscription, successful CI job, or signed checklist does not itself establish legal compliance. Product owners, a suitably qualified independent reviewer and, for regulated questions, legal/domain specialists retain responsibility for decisions.

## Baseline controls (one common control library)
1. Inventory legal entities, deployed products, controllers/processors, countries, user groups, AI systems, models, external processors and data flows.
2. Classify the *actual intended use*, AI provider/deployer role, jurisdiction, foreseeable misuse and EU AI Act category. A product's internally assigned priority is **not** an EU AI Act legal risk category.
3. Map applicable obligations: UK GDPR/Data Protection Act, EU GDPR, PECR/ePrivacy, EU AI Act, children's privacy rules, consumer/marketing/online-safety rules and sector-specific law where relevant. Document non-applicability with reasoning.
4. Maintain lawful bases, special-category processing conditions where needed, processor agreements, international transfer assessments, privacy notices, cookie/marketing choices, records of processing and DPIAs where required.
5. Apply security baseline in `docs/SECURITY_BASELINE.md`: asset/access management, RLS, encryption, secrets, pen/security tests, logging, dependency controls, backup and recovery, incident response.
6. Govern AI model sources, intended purpose, data provenance/licences, accuracy/reliability, safety evaluation, prompt injection, data leakage, human escalation, autonomous-tool permissions and change monitoring.
7. Implement applicable Article 50 obligations: disclose AI interaction when required; assess machine-readable identification of synthetic output and user-facing deepfake/public-interest disclosure as applicable. Do not assume a generic “AI-generated” label solves all duties.
8. Apply privacy-by-default, age-appropriate design, content moderation/abuse controls and safeguarding where minors may reasonably access a product. Assess the UK Online Safety Act separately for relevant user-to-user/search services.
9. For financial/payment products, obtain formal regulatory perimeter analysis (FCA or relevant regulator, payments/crypto, AML/KYC, sanctions and fraud); for health, medical-device/claims and special-category-data analysis; for education, high-risk AI and children's rights review; for legal-tech, professional/consumer-protection analysis.
10. Perform supplier due diligence (e.g. OpenAI, Anthropic, Supabase, Cloudflare, telephony and hosting): contracts, subprocessors, geographic locations, retention/training, data access, security attestations and incident response.
11. Track control owner, evidence, date, exceptions, action deadlines, reviewer and remediation. Retest after substantial change or incident. Do not publish “certified” or “compliant” claims without substantiation.
12. Maintain customer-facing privacy/terms/AI notices, incident and data-subject request contact paths, and truthful trust-centre evidence only where verified.

## Evidence and release gates
Each active product must eventually contain `compliance/PRODUCT_COMPLIANCE.json` matching `templates/PRODUCT_COMPLIANCE.json` and must run `scripts/compliance_gate.py` (copied or properly reused) in its PR and release checks.

The manifest is a **register**, not proof. Every PASS needs a traceable evidence reference plus named independent reviewer. Every NOT APPLICABLE needs a documented explanation plus independent review. Pending, prohibited/unknown legal classification, missing evidence, and blocked controls fail closed. Neither the implementing developer nor an AI agent may self-certify regulated or material security findings.

Control outcome vocabulary: `pass`, `not_applicable`, `not_verified`, `blocked`. Risk classifications and approval are independent from operational priority.

Release sequence:
1. Product owner creates or updates the compliance manifest and assessment.
2. Qualified reviewer validates scope, underlying evidence and obligations; security reviewer validates security evidence.
3. Product CI runs deterministic gate + tests and retains exact-head build artefacts.
4. An independent reviewer authorises deployment (including regional/sector conditions). A green gate alone does not authorise release.
5. Deployments, incidents and substantial model/data/scope changes trigger reassessment.

## Portfolio implementation order (risk-based *review priority*, not statutory classifications)
- **P0:** Sigma autonomous agents; Friday/Alysha AI platform; Synergy AI Pay and crypto/payment products; private hosting/operations.
- **P1:** Winkday; Humanit; BodyFit; Legalit; Signit; Invoiceit; mining/gold/copper pricing and trading systems.
- **P2:** Tattooit; Marketit; Designit; corporate sites and other user-facing apps.
- Apply the baseline to **all** projects, including discoveries before promotion to production. Do not assume each listed product is currently deployed or in regulatory scope.

## Coverage and artefacts
- Group: legal-entity/product/AI/vendor inventory; policies, training records, incident process, exception log, evidence index, scheduled review.
- Per product: `compliance/PRODUCT_COMPLIANCE.json`; model/use-case cards, data map, DPIA/AI impact assessment when needed, legal/sector scoping decision, notices, security evidence, test results, release record.
- In CI: structured validator for **completeness only**; scanners and functional tests must be integrated per product. Independent legal/security reviews cannot be simulated by software.
- Exceptions: documented by risk owner, expiry and compensating controls; never waive legal prohibitions or represent unverified controls as PASS.

## Reference sources (checked 12 November 2026)
- European Commission AI Act implementation: https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline
- Official consolidated Regulation (EU) 2024/1689: https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng
- EU AI Act Article 50 transparency: https://digital-strategy.ec.europa.eu/en/library/guidelines-transparency-obligations-providers-and-deployers-ai-systems
- ICO Children's Code: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/introduction-to-the-childrens-code/
- ISO/IEC 42001 overview: https://www.iso.org/standard/42001
- NIST voluntary AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- Vanta benchmark (not an endorsement): https://www.vanta.com/products/eu-ai-act

## Implementation acceptance
This programme is **not COMPLETE** until each active product is inventoried, classified, independently assessed, contains verified controls/evidence, has mandatory CI/release enforcement, and deployed controls have actually been tested. Open findings must remain visible in project status and tracking issues.
