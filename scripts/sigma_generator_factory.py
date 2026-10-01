#!/usr/bin/env python3
"""CLI for the Sigma Generator Factory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from sigma_runtime.generator_factory import GeneratorFactory, GeneratorFactoryError


def _json_object(value: str) -> dict:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("input JSON must be an object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sigma Generator Factory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Validate the registered generator catalogue")

    list_parser = sub.add_parser("list", help="List registered generators")
    list_parser.add_argument("--state", choices=["DRAFT", "APPROVED", "DISABLED"])

    show_parser = sub.add_parser("show", help="Show one generator definition")
    show_parser.add_argument("generator_id")

    run_parser = sub.add_parser("run", help="Execute an APPROVED generator")
    run_parser.add_argument("generator_id")
    run_parser.add_argument(
        "--input",
        type=_json_object,
        required=True,
        help='JSON object, for example: {"items":["a","b"],"count":1}',
    )
    run_parser.add_argument("--seed", type=int, default=0)

    draft_parser = sub.add_parser("draft", help="Create a DRAFT generator definition")
    draft_parser.add_argument("--id", required=True, dest="generator_id")
    draft_parser.add_argument("--name", required=True)
    draft_parser.add_argument("--department", required=True)
    draft_parser.add_argument("--description", required=True)
    draft_parser.add_argument(
        "--operation",
        required=True,
        choices=["template", "choice", "weighted_choice", "combine", "synthetic_records"],
    )
    draft_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Explicit output path for the draft YAML definition",
    )

    check_parser = sub.add_parser("check-spec", help="Validate a standalone generator spec")
    check_parser.add_argument("path", type=Path)

    args = parser.parse_args()
    factory = GeneratorFactory()

    if args.command == "validate":
        decisions = factory.validate_registry()
        failures = [decision for decision in decisions if decision.reasons]
        for decision in decisions:
            status = "OK" if not decision.reasons else "CHECK"
            print(f"{status:5} {decision.generator_id:32} {decision.state}")
            for reason in decision.reasons:
                print(f"      - {reason}")
        return 1 if failures else 0

    if args.command == "list":
        print(
            yaml.safe_dump(
                factory.list_generators(args.state),
                sort_keys=False,
                allow_unicode=True,
            )
        )
        return 0

    if args.command == "show":
        print(
            yaml.safe_dump(
                factory.get_definition(args.generator_id),
                sort_keys=False,
                allow_unicode=True,
            )
        )
        return 0

    if args.command == "run":
        try:
            result = factory.execute(
                args.generator_id,
                args.input,
                seed=args.seed,
            )
        except GeneratorFactoryError as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "draft":
        try:
            draft = factory.draft_definition(
                generator_id=args.generator_id,
                name=args.name,
                department=args.department,
                description=args.description,
                operation_type=args.operation,
            )
        except GeneratorFactoryError as exc:
            parser.error(str(exc))

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            yaml.safe_dump(draft, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(str(args.output))
        return 0

    if args.command == "check-spec":
        decision = factory.validate_spec_file(args.path)
        print(
            json.dumps(
                {
                    "id": decision.generator_id,
                    "state": decision.state,
                    "reasons": list(decision.reasons),
                },
                indent=2,
            )
        )
        return 1 if decision.reasons else 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
