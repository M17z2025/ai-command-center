# Owner-approved open-source pilots — 2026-11-01

**Authority:** owner approval in Sigma project conversation, 2026-11-01.
**Scope:** evaluation, fit checks and gated implementation; **not** blanket production deployment.
**Source of truth:** `headquarters/scouter/catalog.yaml` entries with `owner_shortlist`.
**Command:** `python scripts/sigma_scouter.py shortlist` (optional `--decision PILOT`).
**Decision classification:** owner acceptance of the integration direction does not change Scouter licence/admission state to ACCEPT, and does not prove service installation or use.

## Ordered work and acceptance conditions

| Priority | Candidate | Destination | First safe executable unit | Acceptance and non-goals |
| --- | --- | --- | --- | --- |
| P0 | Cloudflare security-audit-skill | Sigma security gate, then apps | Pin reviewed version, run isolated audit on authorised Sigma code, triage findings | Independent verification; finding → remediation → regression evidence; do not replace existing CI or audit production systems blindly |
| P0 | Moonshine | Friday (canonical `M17z2025/alisha-ai-platform`) | Offline benchmarking on consented test clips in British English, real telephony sample rate and noise conditions | Compare WER, proper-name accuracy, streaming end-of-turn delay, CPU/memory and barge-in to incumbent; preserve SIP and signed-Android release gates; check model licences |
| P0 | assistant-ui | Sigma owner frontend | Branch-only React PoC against existing mission and approval contracts | Demonstrate streaming, task state and denial-by-default owner approvals; no second runtime/DB or false task-completion labels |
| P1 | DeepTutor | Humanit `M17z2025/ihumanit` | Sandboxed mastery/question sequencing proof-of-concept | Correct 11+/GCSE exam-board coverage; 20min/day Mon–Sat, three subjects/session; incorrect-question remediation; parent/child boundaries, mobile performance |
| P1 | Unstract | Shared service for Invoiceit/Legalit/Investigation | Private non-production document extraction evaluation | Precision/recall and provenance on synthetic/consented files; signed permissions, RLS and private storage; AGPL compliance and cost reviewed; fail closed on uncertain fields |
| P1 | Morphic | Sigma research retrieval | Compare cited retrieval/search modules with existing Sigma retrieval | Measured source accuracy, freshness, latency, duplicate index avoided; no parallel Sigma brain |
| P1 | Hallmark | Developer UI review workflow | Pinned audit skill in isolated agent workspace | UI accessibility and responsive issues found/verified without overwriting approved logo/theme |
| P2 | VoiceStudio | Friday/Winkday audio production | Test local voice samples with permissions | Check commercial voice/model rights and AGPL; no assumption of real-time phone suitability |
| P2 | Public APIs | Sigma Scouter | Use list as *untrusted discovery input* | Individually verify API quota/terms, provenance and resilience before consumption; no assumption that directory is a provider |
| Benchmark | Abacus DeepAgent | Agent engineering comparison only | Repeat Sigma reference coding-agent task on synthetic data | Compare quality/cost/privacy; no second agent runtime or paid commitment |
| Optional | Zero Breach | Endpoint investigation only | Document specialist incident-response use | No general security-platform deployment |

## Implementation gates for each pilot

1. Inspect canonical repository `AGENTS.md`, `.sigma/project.yaml`, `PROJECT_STATUS.md`, current open issues/PRs, actual code and existing pipelines before changes.
2. Verify latest upstream commit/release, exact SPDX/licence and transitive/model/voice dataset rights. Pin a reproducible version, examine install scripts and supply-chain exposure.
3. Create a product-owned issue, a separate feature branch and objective acceptance criteria. Integrate **one** component at a time; do not wholesale-clone competing services.
4. Run local tests, CI, hostile auth/tenant checks when relevant, latency/resource benchmark, independent security gate and regression checks.
5. Release only through the existing product-specific staging/release process. Never claim an operational integration from a README, issue, branch or CI-only proof.
6. Update the candidate `owner_shortlist.implementation_status` and `PROJECT_STATUS.md` **only** from evidence of installation, test and live commissioning, keeping traceable links and environment identity.
7. If blocked, record objective blocker and take the next safe unit without duplicating work.

## Infrastructure and spending

Use current OVH/VPS and existing dev resources only within safe capacity. Do not schedule autonomous installs on a production host or make new paid commitments. Any Moonshine/Unstract/VoiceStudio compute requirement must be measured before choosing Hetzner/GPU capacity.

## Duplicate controls

- Sigma owns the autonomous agent core and Mitz PA; Friday owns telephone/voice/mobile I/O only.
- Morphic provides selectable research components, not a second RAG/memory backend.
- DeepTutor provides study techniques/components, not a replacement Humanit app.
- Unstract provides a bounded document service, not a second end-user product.
- assistant-ui is presentation only and cannot become an approval/security authority.
- Cloudflare security-audit-skill cannot independently certify its own code changes.
