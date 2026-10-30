# Decision 1 — Friday AI / Sigma consolidation
**Authorised 2026-10-30 — Option A**

## Canonical repositories
- **Friday AI**: `M17z2025/alisha-ai-platform` (retains existing native Android/Next/SIP and signed-release flow).
- **Sigma Mesh**: `M17z2025/ai-command-center` (owns portfolio automation, agent routing, CI evidence, security and developer workers).

## Audited legacy repositories
| Source | Inspection | Treatment |
| --- | --- | --- |
| `M17z2025/alisha-os` | Next.js Bolt prototype screen with inert workspace/blueprint/media controls, UI components, static JSON tool catalogues, planning documents, historical SQL migration; no separately proven telephone or development execution service. | Preserve selected capability and governance documents; **do not** copy legacy frontend, credentials, database migration or competing deployment stack. Redirect GitHub development ownership to Friday. |
| `M17z2025/alisha-repository-automation` | README plus generic `.sigma/CONTROL.md`; **no standalone automation scripts, workflows, workers, or source code** in the current default branch. | Preserve original README. Route all work to Sigma's existing portfolio runner, OpenHands worker, GitHub CI and review machinery. No new automation service is necessary. |

The repository lists remain available as historical records until administrators confirm there are no external deployments, GitHub Apps, branch-protection requirements, webhooks, secrets, downstream dependencies, or active unmerged work tied to their identities. This change **does not archive, delete or disable** either remote repository.

## Material migrated from Alysha OS
Preserved unchanged, reference-only:
- `software-factory-stack.json`: proposed Symphony/OpenHands/Goose/Cline worker stack, design patterns for reusable blueprints, automated repair and quality gates. **Not evidence those workers were installed.**
- `ALISHA_SOFTWARE_FACTORY_AND_SELF_HEALING.md`: proposed repair loop, independent challenge, event bus and blueprint catalogue.
- `ALISHA_BACKEND_LOGIC_AND_GOVERNANCE_MAP.md`: legacy prompt/domain routing and vendor-selection rules.

Excluded from active Sigma runtime: standalone Next.js UI, unused Bolt/Netlify/Vercel configuration, copy/pasted UI primitives, proposed AI stacks as live declarations and stale third-party approvals. Other historical designs (games, animation, creative tools) stay accessible in the legacy repository; adopt them only when a particular application needs them and current licensing/security is verified.

## Executable consolidation
1. `projects/registry.yaml` no longer lists the two old repos as active independent products.
2. `headquarters/chat-ownership/teams.yaml` maps their legacy names to canonical owners.
3. `scripts/sigma_chat_owner.py` maps even an explicit old repository path to its canonical owner, instead of creating a new team.
4. `tests/test_sigma_chat_owner.py` locks that behaviour with alias, explicit-repo and registry consistency tests.

## Acceptance / follow-up
- Exact-head Sigma control-plane validation and chat ownership tests pass.
- Friday's original functionality has **not** been modified; source-only reference import must not be treated as an Android release or live test.
- Source repository README notices must be in place on the actual default branches before archival consideration.
- Check integrations/deployments that may still depend on the old repository identity.
- Github archive action, if appropriate, requires an authorised repository-admin operation. It is **pending**, not accomplished.
- Any legacy feature that later proves useful should be implemented as a scoped Friday or Sigma issue with executable tests and independent verification—not blindly imported.
