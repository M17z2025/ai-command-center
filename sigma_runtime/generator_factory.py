"""Sigma Generator Factory: governed declarative micro-tool runtime.

The factory intentionally supports a small fixed operation set. Generator
definitions are data, never executable Python. Unknown/unsafe definitions fail
closed and DRAFT/DISABLED generators cannot execute.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any
import random
import re

import yaml


class GeneratorFactoryError(RuntimeError):
    """Raised when a generator definition or execution request is invalid."""


@dataclass(frozen=True)
class GeneratorDecision:
    generator_id: str
    state: str
    reasons: tuple[str, ...]


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")


class GeneratorFactory:
    """Load, validate and execute approved Sigma generator definitions."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.repo_root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.policy_path = self.repo_root / "headquarters" / "generator-factory" / "policy.yaml"
        self.registry_path = self.repo_root / "headquarters" / "generator-factory" / "registry.yaml"
        self.policy = self._load(self.policy_path)
        self.registry = self._load(self.registry_path)

        if self.policy.get("schema_version") != 1:
            raise GeneratorFactoryError("Unsupported Generator Factory policy schema")
        if self.registry.get("schema_version") != 1:
            raise GeneratorFactoryError("Unsupported Generator Factory registry schema")

        limits = self.policy.get("limits", {})
        self.max_output_items = int(limits.get("max_output_items", 1000))
        self.max_input_items = int(limits.get("max_input_items", 10000))
        self.max_template_chars = int(limits.get("max_template_chars", 10000))
        self.max_rendered_chars = int(limits.get("max_rendered_chars", 50000))
        self.allowed_operations = set(self.policy.get("allowed_operations", []))
        self.required_fields = set(self.policy.get("required_definition_fields", []))
        self.forbidden_capabilities = set(
            self.policy.get("security", {}).get("forbidden_capabilities", [])
        )

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise GeneratorFactoryError(f"Missing Generator Factory file: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise GeneratorFactoryError(f"Invalid YAML object: {path}")
        return data

    def validate_definition(self, item: dict[str, Any]) -> GeneratorDecision:
        generator_id = str(item.get("id", "<missing-id>"))
        reasons: list[str] = []

        missing = sorted(field for field in self.required_fields if field not in item)
        if missing:
            return GeneratorDecision(
                generator_id,
                "DRAFT",
                (f"missing fields: {', '.join(missing)}",),
            )

        state = str(item.get("state", "DRAFT"))
        if state not in {"DRAFT", "APPROVED", "DISABLED"}:
            reasons.append(f"invalid state {state!r}")

        if not _ID_RE.fullmatch(generator_id):
            reasons.append("id must match ^[a-z0-9][a-z0-9-]{2,63}$")

        required_inputs = item.get("required_inputs")
        if not isinstance(required_inputs, list) or any(
            not isinstance(field, str) or not _FIELD_RE.fullmatch(field)
            for field in required_inputs
        ):
            reasons.append("required_inputs must be a list of safe field names")

        capabilities = item.get("capabilities")
        if not isinstance(capabilities, list):
            reasons.append("capabilities must be a list")
        else:
            unknown_caps = sorted(set(str(cap) for cap in capabilities))
            forbidden = sorted(set(unknown_caps) & self.forbidden_capabilities)
            if forbidden:
                reasons.append(f"forbidden capabilities: {', '.join(forbidden)}")
            if unknown_caps:
                reasons.append(
                    "v1 generators cannot request capabilities; capabilities must be empty"
                )

        operation = item.get("operation")
        if not isinstance(operation, dict):
            reasons.append("operation must be an object")
        else:
            op_type = str(operation.get("type", ""))
            config = operation.get("config", {})
            if op_type not in self.allowed_operations:
                reasons.append(f"unknown operation {op_type!r}")
            if not isinstance(config, dict):
                reasons.append("operation.config must be an object")
            elif op_type in self.allowed_operations:
                reasons.extend(self._validate_operation_config(op_type, config))

        provenance = item.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            reasons.append("provenance must be a non-empty object")

        tests = item.get("tests")
        if not isinstance(tests, list) or not tests:
            reasons.append("tests must contain at least one declared test")

        effective_state = "DRAFT" if reasons and state == "APPROVED" else state
        return GeneratorDecision(generator_id, effective_state, tuple(reasons))

    def _validate_operation_config(self, op_type: str, config: dict[str, Any]) -> list[str]:
        reasons: list[str] = []

        if op_type == "template":
            template = config.get("template")
            if not isinstance(template, str) or not template:
                reasons.append("template operation requires non-empty config.template")
            elif len(template) > self.max_template_chars:
                reasons.append("template exceeds max_template_chars")

        elif op_type in {"choice", "weighted_choice"}:
            source_field = config.get("source_field", "items")
            if not isinstance(source_field, str) or not _FIELD_RE.fullmatch(source_field):
                reasons.append(f"{op_type} source_field is invalid")
            count_field = config.get("count_field", "count")
            if not isinstance(count_field, str) or not _FIELD_RE.fullmatch(count_field):
                reasons.append(f"{op_type} count_field is invalid")
            default_count = config.get("default_count", 1)
            if not isinstance(default_count, int) or isinstance(default_count, bool) or default_count < 1:
                reasons.append(f"{op_type} default_count must be a positive integer")
            if (
                op_type == "choice"
                and "with_replacement" in config
                and not isinstance(config["with_replacement"], bool)
            ):
                reasons.append("choice with_replacement must be a boolean")

        elif op_type == "combine":
            fields = config.get("fields")
            if not isinstance(fields, list) or not fields:
                reasons.append("combine requires a non-empty config.fields list")
            elif any(not isinstance(field, str) or not _FIELD_RE.fullmatch(field) for field in fields):
                reasons.append("combine fields must use safe field names")

        elif op_type == "synthetic_records":
            fields = config.get("fields")
            if not isinstance(fields, dict) or not fields:
                reasons.append("synthetic_records requires non-empty config.fields")
            else:
                for field_name, spec in fields.items():
                    if not isinstance(field_name, str) or not _FIELD_RE.fullmatch(field_name):
                        reasons.append(f"invalid synthetic field name {field_name!r}")
                        continue
                    if not isinstance(spec, dict):
                        reasons.append(f"synthetic field {field_name!r} must be an object")
                        continue
                    field_type = spec.get("type")
                    if field_type not in {"input", "sequence", "choice", "template", "literal"}:
                        reasons.append(
                            f"synthetic field {field_name!r} uses unsupported type {field_type!r}"
                        )
                    if field_type == "template":
                        template = spec.get("template")
                        if not isinstance(template, str) or not template:
                            reasons.append(
                                f"synthetic template field {field_name!r} needs template text"
                            )
                        elif len(template) > self.max_template_chars:
                            reasons.append(
                                f"synthetic template field {field_name!r} exceeds max_template_chars"
                            )
                    if field_type == "choice":
                        has_values = isinstance(spec.get("values"), list)
                        source_field = spec.get("source_field")
                        has_source = isinstance(source_field, str) and bool(
                            _FIELD_RE.fullmatch(source_field)
                        )
                        if has_values == has_source:
                            reasons.append(
                                f"synthetic choice field {field_name!r} requires exactly one of values or source_field"
                            )

        return reasons

    def validate_registry(self) -> list[GeneratorDecision]:
        generators = self.registry.get("generators", [])
        if not isinstance(generators, list):
            raise GeneratorFactoryError("registry generators must be a list")

        decisions: list[GeneratorDecision] = []
        seen: set[str] = set()
        for item in generators:
            if not isinstance(item, dict):
                decisions.append(
                    GeneratorDecision("<invalid>", "DRAFT", ("generator is not an object",))
                )
                continue
            generator_id = str(item.get("id", ""))
            if generator_id in seen:
                decisions.append(
                    GeneratorDecision(generator_id, "DRAFT", ("duplicate generator id",))
                )
                continue
            seen.add(generator_id)
            decisions.append(self.validate_definition(item))
        return decisions

    def list_generators(self, state: str | None = None) -> list[dict[str, Any]]:
        generators = [
            item for item in self.registry.get("generators", []) if isinstance(item, dict)
        ]
        if state:
            generators = [item for item in generators if item.get("state") == state]
        return generators

    def get_definition(self, generator_id: str) -> dict[str, Any]:
        matches = [item for item in self.list_generators() if item.get("id") == generator_id]
        if len(matches) != 1:
            raise GeneratorFactoryError(
                f"generator {generator_id!r} was not found exactly once"
            )
        return matches[0]

    def validate_spec_file(self, path: Path | str) -> GeneratorDecision:
        candidate_path = Path(path)
        limit = int(
            self.policy.get("limits", {}).get("max_definition_bytes", 131072)
        )
        try:
            encoded_size = candidate_path.stat().st_size
        except OSError as exc:
            raise GeneratorFactoryError(
                f"cannot inspect generator spec {candidate_path}: {exc}"
            ) from exc
        if encoded_size > limit:
            return GeneratorDecision(
                "<oversize>",
                "DRAFT",
                ("definition exceeds max_definition_bytes",),
            )
        data = self._load(candidate_path)
        return self.validate_definition(data)

    def draft_definition(
        self,
        *,
        generator_id: str,
        name: str,
        department: str,
        description: str,
        operation_type: str,
    ) -> dict[str, Any]:
        if operation_type not in self.allowed_operations:
            raise GeneratorFactoryError(f"unknown operation {operation_type!r}")

        starter_config: dict[str, Any]
        if operation_type == "template":
            starter_config = {"template": "{{text}}"}
        elif operation_type in {"choice", "weighted_choice"}:
            starter_config = {
                "source_field": "items",
                "count_field": "count",
                "default_count": 1,
            }
            if operation_type == "choice":
                starter_config["with_replacement"] = False
        elif operation_type == "combine":
            starter_config = {"fields": ["dimension_a", "dimension_b"]}
        else:
            starter_config = {
                "count_field": "count",
                "default_count": 1,
                "fields": {"record_id": {"type": "sequence", "start": 1, "step": 1}},
            }

        return {
            "id": generator_id,
            "name": name,
            "department": department,
            "description": description,
            "state": "DRAFT",
            "operation": {"type": operation_type, "config": starter_config},
            "required_inputs": [],
            "capabilities": [],
            "provenance": {
                "source": "Sigma Generator Factory draft",
                "rationale": "Draft generated from an explicit operator/Sigma request; approval pending.",
            },
            "tests": ["TODO: define deterministic acceptance test before approval"],
        }

    def execute(
        self,
        generator_id: str,
        inputs: dict[str, Any],
        *,
        seed: int = 0,
    ) -> Any:
        if not isinstance(inputs, dict):
            raise GeneratorFactoryError("inputs must be an object")

        definition = self.get_definition(generator_id)
        decision = self.validate_definition(definition)
        if decision.reasons:
            raise GeneratorFactoryError(
                f"generator {generator_id!r} failed validation: {'; '.join(decision.reasons)}"
            )
        if definition.get("state") != "APPROVED":
            raise GeneratorFactoryError(
                f"generator {generator_id!r} is not APPROVED and cannot execute"
            )

        required_inputs = definition.get("required_inputs", [])
        missing = [field for field in required_inputs if field not in inputs]
        if missing:
            raise GeneratorFactoryError(
                f"missing required inputs: {', '.join(sorted(missing))}"
            )

        operation = definition["operation"]
        op_type = operation["type"]
        config = operation.get("config", {})
        rng = random.Random(seed)

        if op_type == "template":
            return self._render_template(str(config["template"]), inputs)

        if op_type == "choice":
            items = self._input_list(inputs, str(config.get("source_field", "items")))
            count = self._resolve_count(config, inputs)
            with_replacement = bool(config.get("with_replacement", False))
            if with_replacement:
                return [rng.choice(items) for _ in range(count)]
            if count > len(items):
                raise GeneratorFactoryError(
                    "choice count exceeds available items without replacement"
                )
            return rng.sample(items, count)

        if op_type == "weighted_choice":
            raw = self._input_list(inputs, str(config.get("source_field", "items")))
            values: list[Any] = []
            weights: list[float] = []
            for index, item in enumerate(raw):
                if not isinstance(item, dict) or "value" not in item or "weight" not in item:
                    raise GeneratorFactoryError(
                        f"weighted item {index} must contain value and weight"
                    )
                weight = item["weight"]
                if (
                    not isinstance(weight, (int, float))
                    or isinstance(weight, bool)
                    or weight <= 0
                ):
                    raise GeneratorFactoryError(
                        f"weighted item {index} weight must be positive"
                    )
                values.append(item["value"])
                weights.append(float(weight))
            count = self._resolve_count(config, inputs)
            return rng.choices(values, weights=weights, k=count)

        if op_type == "combine":
            fields = list(config["fields"])
            dimensions = [self._input_list(inputs, field) for field in fields]
            output_count = 1
            for dimension in dimensions:
                output_count *= len(dimension)
                if output_count > self.max_output_items:
                    raise GeneratorFactoryError(
                        f"combine output exceeds max_output_items={self.max_output_items}"
                    )
            return [
                dict(zip(fields, values, strict=True))
                for values in product(*dimensions)
            ]

        if op_type == "synthetic_records":
            count = self._resolve_count(config, inputs)
            return [
                self._render_record(config["fields"], inputs, index + 1, rng)
                for index in range(count)
            ]

        raise GeneratorFactoryError(f"unsupported operation {op_type!r}")

    def _input_list(self, inputs: dict[str, Any], field: str) -> list[Any]:
        value = inputs.get(field)
        if not isinstance(value, list) or not value:
            raise GeneratorFactoryError(f"input {field!r} must be a non-empty list")
        if len(value) > self.max_input_items:
            raise GeneratorFactoryError(
                f"input {field!r} exceeds max_input_items={self.max_input_items}"
            )
        return value

    def _resolve_count(self, config: dict[str, Any], inputs: dict[str, Any]) -> int:
        count_field = str(config.get("count_field", "count"))
        value = inputs.get(count_field, config.get("default_count", 1))
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise GeneratorFactoryError(f"{count_field!r} must be a positive integer")
        if value > self.max_output_items:
            raise GeneratorFactoryError(
                f"requested output exceeds max_output_items={self.max_output_items}"
            )
        return value

    def _render_template(self, template: str, values: dict[str, Any]) -> str:
        if len(template) > self.max_template_chars:
            raise GeneratorFactoryError("template exceeds max_template_chars")

        unsupported = _PLACEHOLDER_RE.sub("", template)
        if "{{" in unsupported or "}}" in unsupported:
            raise GeneratorFactoryError("template contains unsupported placeholder syntax")

        fields = _PLACEHOLDER_RE.findall(template)
        missing = sorted({field for field in fields if field not in values})
        if missing:
            raise GeneratorFactoryError(
                f"missing template fields: {', '.join(missing)}"
            )

        def replace(match: re.Match[str]) -> str:
            value = values[match.group(1)]
            if isinstance(value, (dict, list, tuple, set)):
                raise GeneratorFactoryError(
                    f"template field {match.group(1)!r} must be scalar"
                )
            return str(value)

        rendered = _PLACEHOLDER_RE.sub(replace, template)
        if len(rendered) > self.max_rendered_chars:
            raise GeneratorFactoryError("rendered output exceeds max_rendered_chars")
        return rendered

    def _render_record(
        self,
        fields: dict[str, Any],
        inputs: dict[str, Any],
        index: int,
        rng: random.Random,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {}
        context = dict(inputs)
        context["_index"] = index

        for field_name, spec in fields.items():
            field_type = spec["type"]
            if field_type == "literal":
                value = spec.get("value")
            elif field_type == "input":
                source_field = str(spec.get("source_field", field_name))
                if source_field not in inputs:
                    raise GeneratorFactoryError(
                        f"synthetic input field {source_field!r} is missing"
                    )
                value = inputs[source_field]
            elif field_type == "sequence":
                start = spec.get("start", 1)
                step = spec.get("step", 1)
                if (
                    not isinstance(start, (int, float))
                    or isinstance(start, bool)
                    or not isinstance(step, (int, float))
                    or isinstance(step, bool)
                ):
                    raise GeneratorFactoryError(
                        f"sequence field {field_name!r} start/step must be numeric"
                    )
                value = start + ((index - 1) * step)
            elif field_type == "choice":
                if "values" in spec:
                    values = spec["values"]
                    if not isinstance(values, list) or not values:
                        raise GeneratorFactoryError(
                            f"choice field {field_name!r} values must be non-empty"
                        )
                    if len(values) > self.max_input_items:
                        raise GeneratorFactoryError(
                            f"choice field {field_name!r} exceeds max_input_items"
                        )
                else:
                    values = self._input_list(inputs, str(spec["source_field"]))
                value = rng.choice(values)
            elif field_type == "template":
                value = self._render_template(str(spec["template"]), context | record)
            else:
                raise GeneratorFactoryError(
                    f"unsupported synthetic field type {field_type!r}"
                )
            record[field_name] = value

        return record
