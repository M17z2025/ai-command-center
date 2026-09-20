#!/usr/bin/env python3
"""Validate core Sigma control-plane files and the repository registry."""

from pathlib import Path
import sys
import yaml
import jsonschema

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "SECURITY.md",
    "projects/registry.yaml",
    "templates/project.yaml",
    "schemas/project-manifest.schema.json",
    "docs/OPERATING_MODEL.md",
    "docs/DEVELOPMENT_LOOP.md",
    "docs/CHATGPT_HANDOFF.md",
    "docs/SECURITY_BASELINE.md",
    "docs/DEFINITION_OF_DONE.md",
]

errors = []

for rel in REQUIRED:
    if not (ROOT / rel).exists():
        errors.append(f"Missing required file: {rel}")

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

manifest_path = ROOT / "templates/project.yaml"
schema_path = ROOT / "schemas/project-manifest.schema.json"
if manifest_path.exists() and schema_path.exists():
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    import json
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(manifest, schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"Project manifest template invalid: {exc.message}")

if errors:
    print("Sigma control-plane validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Sigma control-plane validation PASSED")
