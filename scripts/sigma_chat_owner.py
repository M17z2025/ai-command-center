#!/usr/bin/env python3
"""Resolve a development chat to its persistent Sigma Build Steward Team."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "headquarters" / "chat-ownership" / "teams.yaml"


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def load_config() -> dict:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise RuntimeError("Invalid Sigma chat ownership config")
    return data


def resolve(title: str, message: str = "", repository: str = "") -> dict:
    cfg = load_config()
    combined = f"{title} {message}".lower()

    if repository:
        for item in cfg.get("projects", []):
            if item.get("repository", "").lower() == repository.lower():
                return assignment(cfg, item, "repository")

    candidates = []
    for section in ("projects", "intake_projects"):
        for item in cfg.get(section, []):
            score = 0
            matched = []
            names = [item.get("project", ""), *item.get("aliases", [])]
            for alias in names:
                alias_l = str(alias).lower().strip()
                if not alias_l:
                    continue
                if alias_l in combined:
                    score += max(10, len(_tokens(alias_l)) * 5)
                    matched.append(alias)
                else:
                    overlap = len(_tokens(alias_l) & _tokens(combined))
                    score += overlap
            if score:
                candidates.append((score, item.get("repository") is not None, item, matched))

    if not candidates:
        return {
            "state": "UNMAPPED_CHAT",
            "project": None,
            "repository": None,
            "accountable_build_steward": cfg["intake_team"]["accountable_build_steward"],
            "team": cfg["intake_team"]["core_team"],
            "rule": cfg["intake_team"]["rule"],
        }

    candidates.sort(key=lambda x: (-x[0], -int(x[1]), x[2]["project"]))
    score, _, item, matched = candidates[0]
    result = assignment(cfg, item, "alias")
    result["match_score"] = score
    result["matched_aliases"] = matched
    return result


def assignment(cfg: dict, item: dict, matched_by: str) -> dict:
    default = cfg["defaults"]
    core = list(default["core_team"])
    domain = list(item.get("domain_team", []))
    team = list(dict.fromkeys(core + domain))
    return {
        "state": item.get("state", "ASSIGNED"),
        "project": item.get("project"),
        "repository": item.get("repository"),
        "matched_by": matched_by,
        "accountable_build_steward": default["accountable_build_steward"],
        "team": team,
        "completion_rule": default["completion_rule"],
        "truth_rule": default["truth_rule"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sigma Chat Build Ownership")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")

    r = sub.add_parser("resolve")
    r.add_argument("--title", required=True)
    r.add_argument("--message", default="")
    r.add_argument("--repository", default="")

    args = parser.parse_args()
    cfg = load_config()
    if args.command == "list":
        for item in cfg.get("projects", []):
            print(f'{item["project"]}: {item["repository"]}')
        for item in cfg.get("intake_projects", []):
            print(f'{item["project"]}: PROJECT_REPOSITORY_REQUIRED')
        return 0

    print(yaml.safe_dump(resolve(args.title, args.message, args.repository), sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
