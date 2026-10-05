# Sigma Generator Factory

**Controller:** \`sigma-generator-factory-controller\`  
**Issue:** #103  
**Scope:** portfolio-wide governed specialist micro-tool creation

Sigma Generator Factory turns recurring small generator needs into reusable Sigma-owned tools without depending on external generator websites.

The factory is intentionally **declarative**. A generator is YAML data describing one approved operation. It is not Python source, JavaScript, shell, a prompt with hidden authority, or a remote-service call.

## Why it exists

Sigma repeatedly needs small tools for:
- QA personas and scenario matrices;
- synthetic test records;
- research/query packs;
- curriculum/question permutations;
- content structures;
- names, options and weighted simulations;
- controlled text templates;
- department-specific checklists and fixtures.

Before this subsystem, each request risked becoming a one-off script or a dependency on a third-party site. Generator Factory provides one bounded runtime and a governed registry instead.

## Flow

\`\`\`text
Sigma team request / Sigma Scouter discovery
                 |
                 v
            DRAFT spec
                 |
                 v
       Factory validation gate
                 |
                 v
   Engineering tests + Solution Judge
                 |
                 v
       Cybersecurity review
                 |
                 v
             APPROVED
                 |
                 v
        Registered + observable
                 |
          revise / disable
\`\`\`

Scouter discovers reusable ideas and open-source foundations. Generator Factory does **not** automatically copy or call a discovered service. It converts a justified requirement into a Sigma-owned declarative tool.

## V1 safe operations

| Operation | Purpose |
| --- | --- |
| \`template\` | Replace explicit \`{{field}}\` placeholders with scalar inputs. |
| \`choice\` | Seeded selection from an input list, with bounded count. |
| \`weighted_choice\` | Seeded weighted selection from validated value/weight objects. |
| \`combine\` | Bounded Cartesian product for scenario/test matrices. |
| \`synthetic_records\` | Bounded synthetic records using literal/input/sequence/choice/template field primitives. |

No V1 operation can execute arbitrary source code.

## Execution authority

Only definitions whose repository state is \`APPROVED\` **and** whose current definition passes validation can execute.

\`DRAFT\` and \`DISABLED\` definitions cannot execute.

A requesting Sigma agent does not gain additional authority by asking the factory to create a tool. Generator definitions have no network, secret, shell, subprocess, dynamic-import, eval/exec, production-write or arbitrary-filesystem capability.

## CLI

Validate the registry:

\`\`\`bash
python scripts/sigma_generator_factory.py validate
\`\`\`

List approved generators:

\`\`\`bash
python scripts/sigma_generator_factory.py list --state APPROVED
\`\`\`

Run a seeded picker:

\`\`\`bash
python scripts/sigma_generator_factory.py run sigma-random-picker \
  --input '{"items":["mobile","desktop","tablet"],"count":2}' \
  --seed 42
\`\`\`

Create a draft definition:

\`\`\`bash
python scripts/sigma_generator_factory.py draft \
  --id legal-review-scenarios \
  --name "Legal Review Scenarios" \
  --department legal \
  --description "Generate bounded review scenarios." \
  --operation combine \
  --output /tmp/legal-review-scenarios.yaml
\`\`\`

A generated draft is **not approved**. It must be edited, tested and reviewed before being added to \`registry.yaml\`.

Validate a standalone draft:

\`\`\`bash
python scripts/sigma_generator_factory.py check-spec /tmp/legal-review-scenarios.yaml
\`\`\`

## Owner-supplied GitHub source registry

`user-github-sources.yaml` is the durable owner-supplied GitHub source index.

Current baseline: **40 exact GitHub URLs recovered from owner messages** across prior Sigma/project conversations. Of the 29 external entries, the current licence screen identifies **13 permissive candidates for deeper review, 6 copyleft candidates requiring a deliberate fork/service boundary, 3 reference-only sources, 3 restricted-licence sources, 1 licence-unverified repository and 3 discovery-only surfaces**.

Rules:
- exact URLs are deduplicated;
- external repositories/topics/organisations enter `REVIEW`, never automatic install or execution;
- M17z2025 repository/PR/issue/action URLs are preserved as `EVIDENCE`;
- links introduced only by an assistant are not represented as owner-supplied unless the owner also sent them;
- external repositories must pass Sigma Scouter licence/commercial-use/maintenance/security/integration review before adoption;
- useful patterns can be converted into Sigma-owned Generator Factory definitions without inheriting external runtime authority;
- future GitHub links supplied by the owner in Sigma-connected work must be appended/deduplicated into this registry as durable project knowledge.

## Perchance boundary

Perchance can be used by humans as inspiration/research where its terms permit. Sigma Generator Factory does not automate Perchance, scrape it, treat it as a production dependency, or send confidential Sigma information to public generators.

If Perchance or another external generator publishes an explicitly authorised API in future, that integration would still require its own Scouter, legal/licence, security and engineering review.

## Files

- \`policy.yaml\` — authority, limits, safe operation set and security boundary.
- \`registry.yaml\` — approved/draft/disabled generator definitions.
- \`sigma_runtime/generator_factory.py\` — validator/executor.
- \`scripts/sigma_generator_factory.py\` — operator/agent CLI.
- \`tests/test_sigma_generator_factory.py\` — regression/security-boundary tests.

## V1 truth boundary

V1 is a governed local runtime for declarative generators. It is **not** a general no-code app builder, an arbitrary-code agent, or permission to auto-deploy generated functionality into product repositories. Product integration continues through the normal Sigma development, security and user-testing gates.
