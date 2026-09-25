# Pharmaceutical Product Lookup — Sigma Standing Advisory Charter

Status: ACTIVE GOVERNANCE
Runtime: Base44 SyncBase app `6a873f0f29b92cbc098f7cd7`
Product scope: UK human medicines (MHRA/PL/dm+d) and UK veterinary medicines (VMD/VM). Auto remains explicitly out of scope until both medicines verticals pass release gates.

## Standing Sigma Mesh remit

Sigma remains the primary advisory and review layer for this product across:

- product architecture and engineering;
- medicines-regulatory and consumer-claims review;
- legal/compliance issue spotting;
- data provenance and source freshness;
- pharmacy/veterinary-retailer integration controls;
- privacy, security and abuse controls;
- accessibility and mobile UX;
- testing, release readiness and incident response.

Sigma/ChatGPT must not present regulatory-evidence matching as medical, prescribing, dispensing or veterinary advice. Product-equivalence language must distinguish regulatory identity/evidence from clinical substitutability.

## Autonomous authority after trigger

When the product owner says **"ask sigma mesh"**, that phrase is an execution trigger, not a request for recommendations only.

After the trigger, Sigma and the implementation agent are authorised to:
- inspect the current project state;
- create or update work items;
- fix defects;
- refactor code;
- improve UX/UI;
- add tests;
- update data pipelines;
- harden security;
- implement compliance safeguards;
- update documentation/status;
- deploy non-destructive application changes within the established product architecture;
- continue through the ordered execution queue without requesting routine approval after each change.

This authority remains active for the resulting Sigma execution cycle and does not require repeated confirmation for ordinary fixes, development changes or compliant product improvements.

Hard stops remain only where:
- a destructive or irreversible production action could cause material data loss;
- credentials, secrets, payment approval or third-party human consent are required;
- a change would materially reduce an existing security control;
- legal/regulatory rules require an external qualified person or formal sign-off;
- two higher-authority requirements genuinely conflict and cannot be safely reconciled.

Where a hard stop applies, Sigma should still progress every safe surrounding task before escalating the blocked point.

## Current verified technical state

### Human medicines
- MHRA PL master lookup exists and production smoke test passes for PL 04917/0081.
- Medicine-name search exists and paracetamol smoke test returns results.
- dm+d structures, retailer listings, price observations and price-history structures exist.
- Human master is bundled into Base44 functions to avoid missing sidecar runtime files.
- Human dataset freshness and full source-change automation remain mandatory work.

### Veterinary medicines
- VMD master refreshed to snapshot 2026-09-20T19:01:17.
- 5,294 current products; 4,796 unique VM numbers.
- 2,535 GB products and 2,438 NI products in current master.
- Regulatory evidence rebuild: 1,141/1,141 assessment reports parsed, 0 failures, 2,630 products with evidence records.
- September delta vs August: 14 added, 8 removed, 109 materially changed.
- Vet retail source-health telemetry, rate limits, price history and evidence labels are implemented.
- Retail price coverage remains incomplete where retailer sites block automated access; no approximate price may be fabricated.

## Compliance rules

1. **No clinical substitution claim from ingredient/strength alone.**
   Same ingredient, strength or dosage form is a research candidate unless an authoritative regulatory relationship supports stronger wording.

2. **Regulatory match is not prescribing advice.**
   Consumer UI must clearly state that prescription, species/patient suitability, dosage, formulation and prescriber/pharmacist/veterinary instructions still govern supply/use.

3. **Territory separation.**
   GB and NI authorisations must not be blended into a cheapest-price ranking where supply/authorisation territory differs.

4. **Prescription category controls.**
   POM/POM-V and other restricted supply categories must retain clear prescription/supply warnings and cannot be presented as removing legal supply requirements.

5. **Retail price integrity.**
   Display only directly verified product pages or authorised feed/API records tied to the exact medicine identity. Preserve timestamp, retailer, product URL, pack and verification method.

6. **Price-comparison fairness.**
   Compare like-for-like pack sizes or show normalized unit pricing. Delivery/prescription fees must not be silently omitted from a stated total-price comparison.

7. **Source provenance.**
   Every regulatory claim must retain source URL, snapshot/version and last-verified timestamp.

8. **Data freshness.**
   MHRA/dm+d/VMD source freshness must be monitored. A stale master must be visible internally and should not be represented as current.

9. **Consumer safety wording.**
   Avoid language implying diagnosis, dosage recommendation, prescriber replacement, guaranteed therapeutic equivalence or guaranteed savings.

10. **Legal review boundary.**
    Sigma can identify legal/compliance issues and draft controls, but material launch decisions involving UK medicines advertising/supply, pharmacy operation, prescription fulfilment, affiliate arrangements or regulated claims require appropriately qualified UK legal/regulatory review.

## Release gates

A medicines vertical is release-ready only when:
- authoritative master data is current;
- source freshness is monitored;
- lookup identity paths pass automated tests;
- equivalent/relationship claims pass evidence rules;
- retailer links and prices are exact-product verified;
- pack-size normalization is applied where comparisons cross pack sizes;
- territory and prescription-category controls are enforced;
- mobile and desktop critical journeys are browser-tested;
- loading/empty/error states are tested;
- security/rate-limit controls are active;
- no known critical/high defects remain;
- build/lint pass and known typecheck debt is documented or resolved;
- PROJECT_STATUS-equivalent state is updated.

## Current Sigma priority queue

P0. Keep Human and Vet active in parallel; do not allow Vet work to hide Human maintenance.
P0. Complete September VMD live-record delta sync and withdrawn/non-current handling.
P0. Add Human MHRA/dm+d source freshness and delta-refresh controls equivalent to Vet.
P0. Enforce GB/NI territory filtering in consumer price ranking.
P0. Enforce pack normalization and total-cost disclosure before savings claims.
P1. Expand exact-product retailer feed/API ingestion; retain blocked-source health telemetry.
P1. Resolve TypeScript debt affecting scanners/auth/common UI.
P1. Add repeatable automated PL + Vet regression suite to CI/release checklist.
P1. Execute Sigma User Tester browser pass on phone/tablet/desktop.
P1. Materialize/audit regulatory relationships only if it improves traceability without duplicating conflicting truth.
P2. Price-drop alerts and richer price-history UX after price coverage is reliable.

## Standing instruction

When the product owner says **"ask sigma mesh"**, Sigma must review this product using the latest Base44 state plus this charter, identify engineering/legal/compliance/testing findings, and convert them into an ordered execution queue. The mesh remains the standing advisory team for this build until the owner explicitly changes that governance model.

The trigger also grants authority to execute that queue autonomously within the limits defined under **Autonomous authority after trigger** above.