# Sigma Generator Factory — Development Advisory Plan

Issue: #103  
Date: 2026-10-01  
Status: IMPLEMENTATION IN PROGRESS ON FEATURE BRANCH

## Objective

Create a reusable Sigma subsystem that can rapidly produce small specialist generators for any department while preserving the command center's no-guessing, evidence, security and authority rules.

## Verified facts

- Sigma already has Scouter for discovering reusable open-source/self-hosted capability.
- Sigma already has an expert mesh, algorithmic engineering gate, independent security gate and agent factory.
- The command center runtime is Python 3.12 and already depends on PyYAML.
- The command center has no end-user UI; this change is a runtime/CLI control-plane feature.
- Perchance-style generators demonstrate a useful interaction pattern, but Sigma should not depend on automated access to Perchance under the terms reviewed for this mission.

## Key design decisions

1. Build a Sigma-owned generator runtime instead of wrapping an external generator site.
2. Use declarative YAML definitions rather than generated arbitrary source code.
3. Keep the V1 operation set deliberately small and composable.
4. Separate creation from authority: new specs are DRAFT by default.
5. Require reproducible seeds for random operations.
6. Apply hard input/output limits to stop accidental combinatorial explosions.
7. Keep product deployment and external-service integration outside factory authority.

## Relevant expert lenses

### Architecture / engineering
Use one registry + one validator/executor. Avoid a plugin loader or arbitrary dynamic import in V1 because it widens the trust boundary substantially.

### Security
Deny network, secrets, shell/subprocess, eval/exec, dynamic imports, arbitrary filesystem access and production writes. Unknown capabilities/operations fail closed.

### Legal / licensing
Treat external generator sites as inspiration/evidence sources only unless explicit rights permit automated API use. Do not copy proprietary implementation code or confidential public-generator content.

### QA
Require deterministic tests for seeded randomness, malformed inputs, output limits, unsafe capability requests and unknown operations.

### Product / operations
Start with high-frequency primitives that can serve QA, research, education, content and synthetic-data needs. Add new operations only when multiple generator definitions cannot express a justified use case.

## Delivery phases

### Phase 1 — Runtime foundation
- policy;
- registry;
- fixed operations;
- CLI;
- unit tests;
- documentation.

### Phase 2 — Mesh integration
- route generator creation requests to the controller;
- allow Sigma teams to propose DRAFT specs;
- add durable generator usage/audit events to the private runtime store.

### Phase 3 — Product adapters
Only after evidence justifies them, add explicit adapters that let approved generators supply safe inputs to product-specific development/test workflows.

### Phase 4 — Visual Generator Factory
Expose registry, status, department, usage, test evidence and creation workflow in the future Sigma Command Center visual UI.

## Acceptance criteria

- registry validates with no findings;
- approved generators execute through fixed safe operations;
- draft/disabled/invalid definitions cannot execute;
- deterministic seeded generation is reproducible;
- output hard limits are tested;
- no external service is required;
- CI/control-plane validation pass on the exact PR head;
- independent security/evidence gates remain explicit before merge/release.

## Next executable actions

1. Complete source files and tests.
2. Open PR from \`feat/103-sigma-generator-factory\`.
3. Inspect exact-head GitHub Actions.
4. Repair any failure.
5. Record independent security/evidence status accurately.
