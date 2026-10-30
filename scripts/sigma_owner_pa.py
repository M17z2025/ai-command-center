#!/usr/bin/env python3
"""Mitz PA operator entry point inside Sigma, not a separate agent service.

Example: printf '%s' 'Summarise my next steps' | python scripts/sigma_owner_pa.py --stdin
Requires the same private Sigma model configuration and store as the mesh.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sigma_runtime import MeshConfig, MissionRouter, MissionStore, SigmaOrchestrator
from sigma_runtime.provider import provider_from_env
from sigma_runtime.memory import memory_from_env
from sigma_runtime.owner_pa import SigmaMitzPA, MAX_OWNER_PROMPT_CHARS


def main(argv=None):
    p = argparse.ArgumentParser(description="Sigma Mitz PA (advisory only)")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--db", default=os.getenv("SIGMA_RUNTIME_DB", "runtime-data/sigma-runtime.db"))
    p.add_argument("--stdin", action="store_true", help="Read prompt from stdin (recommended for private prompts)")
    p.add_argument("prompt", nargs="?", help="Prompt text; avoid sensitive CLI arguments")
    args = p.parse_args(argv)
    if args.stdin:
        # Bounded read prevents filling memory with untrusted input.
        prompt = sys.stdin.read(MAX_OWNER_PROMPT_CHARS + 1)
    else:
        prompt = args.prompt
    if not prompt or not prompt.strip() or len(prompt) > MAX_OWNER_PROMPT_CHARS:
        p.error("Provide a non-empty prompt not exceeding 3000 characters")
    config = MeshConfig(args.root)
    store = MissionStore(args.db)
    router = MissionRouter(config)
    provider = provider_from_env(allow_test=False)
    memory = memory_from_env()
    mesh = SigmaOrchestrator(config, router, provider, store, memory)
    result = SigmaMitzPA(mesh).advise(prompt)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
