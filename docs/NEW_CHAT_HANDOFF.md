# New Chat Handoff — Sigma Development

Use the Sigma Development Command Center as the master source of truth.

Repository: M17z2025/ai-command-center

At the start of a new development chat:
1. Read README.md, AGENTS.md, projects/registry.yaml, docs/OPERATING_MODEL.md, docs/DEVELOPMENT_LOOP.md, docs/CHATGPT_HANDOFF.md, docs/SECURITY_BASELINE.md, docs/DEFINITION_OF_DONE.md and docs/SIGMA_USER_TESTER.md.
2. Identify the correct product repository from projects/registry.yaml.
3. Read the product's .sigma/project.yaml, PROJECT_STATUS.md, AGENTS.md, README, architecture/deployment docs, open issues/PRs, recent commits, code and tests.
4. Continue from repository truth, not chat recollection.
5. For every user-facing change, invoke the Sigma User Tester gate. It must test the deployed product through a real browser, cover all applicable roles and critical journeys, record evidence, report UX opinion and defects, and refuse a full PASS for partial testing.
6. Work autonomously as far as safely possible. Do not claim progress that is not evidenced in repositories, CI, deployments or test artefacts.
