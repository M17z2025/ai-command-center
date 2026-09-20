#!/usr/bin/env python3
"""Create the minimum Sigma contract files in a product repository working tree."""

from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_TEMPLATE = """schema_version: 1
project:
  name: "{name}"
  repository: "{repository}"
  product_owner: ""
  lifecycle: "active"
  priority: "normal"

product:
  purpose: ""
  users: []
  critical_flows: []

stack:
  frontend: ""
  backend: ""
  database: ""
  auth: ""
  storage: ""
  hosting: ""
  package_manager: ""

commands:
  install: ""
  dev: ""
  build: ""
  lint: ""
  typecheck: ""
  test: ""
  test_integration: ""

deployment:
  provider: ""
  production_url: ""
  production_branch: "main"
  instructions: "docs/deployment.md"

security:
  multi_tenant: false
  rls_required: false
  financial_data: false
  health_data: false
  legal_data: false
  pii: false

documentation:
  architecture: "docs/architecture.md"
  status: "PROJECT_STATUS.md"

integrations: []
environment_variables: []
constraints: []
definition_of_done_additions: []
"""

STATUS_TEMPLATE = """# Project Status

Last updated:
Status owner:

## Current release state
- Production:
- Staging:
- Current branch:
- Latest verified commit:

## Working
-

## In progress
-

## Broken / blocked
-

## Security / data risks
-

## External dependencies
-

## Recent completed work
-

## Next three actions
1.
2.
3.

## Verification
- Build:
- Tests:
- Security checks:
- Manual smoke test:
"""

AGENTS_TEMPLATE = """# Product Agent Instructions

This repository is managed by the Sigma Development Command Center.

Before making changes:
1. Read .sigma/project.yaml.
2. Read PROJECT_STATUS.md.
3. Read README.md and referenced architecture/deployment docs.
4. Inspect relevant issues, recent commits and tests.
5. Follow the central Sigma AGENTS.md contract.

Record durable project state in GitHub rather than relying on chat history.
"""

ARCH_TEMPLATE = """# Architecture

## System purpose

## Runtime/components

## Data model and tenancy

## Authentication/authorization

## Storage

## External integrations

## Critical flows

## Architectural decisions
"""

DEPLOY_TEMPLATE = """# Deployment

## Environments

## Build

## Database migrations

## Deployment process

## Required environment variable names

## Smoke checks

## Rollback/recovery
"""

ENV_TEMPLATE = """# Add variable NAMES only. Never commit secrets.
"""


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Product repository working tree")
    parser.add_argument("--name", required=True)
    parser.add_argument("--repository", required=True, help="owner/repo")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    created = []

    candidates = {
        root / ".sigma/project.yaml": PROJECT_TEMPLATE.format(name=args.name, repository=args.repository),
        root / "PROJECT_STATUS.md": STATUS_TEMPLATE,
        root / "AGENTS.md": AGENTS_TEMPLATE,
        root / "docs/architecture.md": ARCH_TEMPLATE,
        root / "docs/deployment.md": DEPLOY_TEMPLATE,
        root / ".env.example": ENV_TEMPLATE,
    }

    for path, content in candidates.items():
        if write_if_missing(path, content):
            created.append(str(path.relative_to(root)))

    if created:
        print("Created:")
        for path in created:
            print(f"  - {path}")
    else:
        print("No files created; contract files already exist.")

    print("\nNext: replace blank fields with facts discovered from the repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
