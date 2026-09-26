#!/usr/bin/env python3
"""CLI for Sigma Scouter."""

from __future__ import annotations

import argparse
import json

from sigma_runtime.scouter import ScouterPolicy, SearXNGClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Sigma Scouter")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Validate the catalogue against strict free/unlimited rules")

    list_parser = sub.add_parser("list", help="List curated candidates")
    list_parser.add_argument("--state", choices=["ACCEPT", "FORK_CANDIDATE", "REVIEW", "REJECT"])

    sub.add_parser("queries", help="Print portfolio discovery queries")

    search_parser = sub.add_parser("search", help="Search through a configured private SearXNG endpoint")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    policy = ScouterPolicy()

    if args.command == "validate":
        decisions = policy.validate_catalog()
        failures = [d for d in decisions if d.reasons]
        for d in decisions:
            status = "OK" if not d.reasons else "CHECK"
            print(f"{status:5} {d.candidate_id:32} {d.state}")
            for reason in d.reasons:
                print(f"      - {reason}")
        return 1 if failures else 0

    if args.command == "list":
        print(yaml_dump(policy.list_candidates(args.state)))
        return 0

    if args.command == "queries":
        for query in policy.portfolio_queries():
            print(query)
        return 0

    if args.command == "search":
        client = SearXNGClient()
        print(json.dumps(client.search(args.query, limit=args.limit), indent=2))
        return 0

    return 2


def yaml_dump(value):
    import yaml
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    raise SystemExit(main())
