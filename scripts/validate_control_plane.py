#!/usr/bin/env python3
"""Validate core Sigma control-plane files, manifests and project registry."""

from pathlib import Path
import json
import sys

import jsonschema
import yaml

from validate_sigma_mesh import validate_mesh

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "SECURITY.md",
    ".env.example",
    ".sigma/project.yaml",
    "PROJECT_STATUS.md",
    "projects/registry.yaml",
    "templates/project.yaml",
    "templates/SIGMA_USER_TEST_REPORT.md",
    "schemas/project-manifest.schema.json",
    "docs/OPERATING_MODEL.md",
    "docs/DEVELOPMENT_LOOP.md",
    "docs/CHATGPT_HANDOFF.md",
    "docs/SECURITY_BASELINE.md",
    "docs/DEFINITION_OF_DONE.md",
    "docs/PROJECT_REPOSITORY_CONTRACT.md",
    "docs/SIGMA_USER_TESTER.md",
    "docs/architecture.md",
    "docs/deployment.md",
    ".github/workflows/sigma-control-plane.yml",
    ".github/workflows/sigma-full-user-test.yml",
    "headquarters/mesh/README.md",
    "headquarters/mesh/taxonomy.yaml",
    "headquarters/mesh/leaders.yaml",
    "headquarters/mesh/pipeline.yaml",
    "headquarters/mesh/evidence.yaml",
    "headquarters/mesh/evolution.yaml",
    "headquarters/mesh/cognitive-methods.yaml",
    "headquarters/mesh/thinkers.yaml",
    "schemas/sigma-expert.schema.json",
    "templates/sigma-expert.yaml",
    "scripts/validate_sigma_mesh.py",
]

errors = []

for rel in REQUIRED:
    if not (ROOT / rel).exists():
        errors.append(f"Missing required file: {rel}")

registry = None
registry_path = ROOT / "projects/registry.yaml"
if registry_path.exists():
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    projects = registry.get("projects", [])
    seen = set()
    for idx, project in enumerate(projects):
        repo = project.get("repository")
        if not repo or "/" not in repo:
            errors.append(f"projects[{idx}] has invalid repository: {repo!r}")
        if repo in seen:
            errors.append(f"Duplicate repository in registry: {repo}")
        seen.add(repo)

schema_path = ROOT / "schemas/project-manifest.schema.json"
schema = None
if schema_path.exists():
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

for rel in ("templates/project.yaml", ".sigma/project.yaml"):
    manifest_path = ROOT / rel
    if not manifest_path.exists() or schema is None:
        continue

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(manifest, schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"{rel} invalid: {exc.message}")

if registry is not None:
    command_center = registry.get("command_center", {})
    expected_repo = command_center.get("repository")
    self_manifest_path = ROOT / ".sigma/project.yaml"

    if self_manifest_path.exists():
        self_manifest = yaml.safe_load(self_manifest_path.read_text(encoding="utf-8"))
        actual_repo = self_manifest.get("project", {}).get("repository")
        if expected_repo != actual_repo:
            errors.append(
                "Command-center repository mismatch: "
                f"registry={expected_repo!r}, self_manifest={actual_repo!r}"
            )

    project_repositories = {
        project.get("repository")
        for project in registry.get("projects", [])
        if project.get("repository")
    }
    if expected_repo and expected_repo not in project_repositories:
        errors.append(
            f"Command-center repository {expected_repo!r} is not registered in projects"
        )

errors.extend(validate_mesh(ROOT))

if errors:
    print("Sigma control-plane validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Sigma control-plane validation PASSED")
