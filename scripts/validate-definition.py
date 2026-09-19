#!/usr/bin/env python3
"""Validate one or more definition files without relying on git-diff discovery."""

from __future__ import annotations

import argparse
import decimal
import json
import os
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.device_types import (  # noqa: E402
    DeviceType,
    ModuleType,
    RackType,
    validate_components,
    verify_filename,
)
from tests.test_configuration import COMPONENT_TYPES  # noqa: E402
from tests.yaml_loader import DecimalSafeLoader  # noqa: E402


SCHEMAS = {
    "device-types": "devicetype.json",
    "module-types": "moduletype.json",
    "rack-types": "racktype.json",
}


def schema_registry() -> Registry:
    registry = Registry()
    for schema_path in (ROOT / "schema").glob("*.json"):
        with schema_path.open() as schema_file:
            resource = Resource.from_contents(
                json.load(schema_file, parse_float=decimal.Decimal)
            )
        registry = resource @ registry
    return registry


def load_known_data(name: str) -> set[tuple[str, str]]:
    path = ROOT / "tests" / name
    with path.open() as data_file:
        return {
            (item[0], item[1])
            for item in json.load(data_file)
            if isinstance(item, list) and len(item) == 2
        }


def definition_type(path: Path, definition: dict):
    relative = path.relative_to(ROOT)
    category = relative.parts[0]
    if category == "device-types":
        return DeviceType(definition, str(relative), "A")
    if category == "module-types":
        return ModuleType(definition, str(relative), "A")
    if category == "rack-types":
        return RackType(definition, str(relative), "A")
    raise ValueError(
        f"{path}: expected a file under device-types/, module-types/, or rack-types/"
    )


def validate_file(path: Path, registry: Registry) -> list[str]:
    errors: list[str] = []
    relative = path.relative_to(ROOT)
    category = relative.parts[0]
    schema_name = SCHEMAS.get(category)
    if schema_name is None:
        return [f"{path}: unsupported definition directory"]
    if path.suffix not in {".yaml", ".yml"}:
        return [f"{path}: definition files must use .yaml or .yml"]

    content = path.read_text()
    if not content.endswith("\n"):
        errors.append("missing trailing newline")
    non_ascii = sorted({char for char in content if ord(char) > 127})
    if non_ascii:
        errors.append(f"contains non-ASCII characters: {', '.join(non_ascii)}")

    try:
        definition = yaml.load(content, Loader=DecimalSafeLoader)
    except yaml.YAMLError as exc:
        return [f"{path}: invalid YAML: {exc}"]

    with (ROOT / "schema" / schema_name).open() as schema_file:
        schema = json.load(schema_file, parse_float=decimal.Decimal)
    validator = Draft202012Validator(schema, registry=registry)
    errors.extend(
        f"schema validation: {error.message} (at {list(error.absolute_path)})"
        for error in validator.iter_errors(definition)
    )
    if errors:
        return [f"{path}: {error}" for error in errors]

    item = definition_type(path, definition)
    known_name_file = {
        "module-types": "known-modules.json",
        "rack-types": "known-racks.json",
    }.get(category)
    known = load_known_data(known_name_file) if known_name_file else set()
    if category == "device-types":
        known = load_known_data("known-slugs.json")

    checks = [verify_filename(item, known), validate_components(COMPONENT_TYPES, item)]
    if isinstance(item, DeviceType):
        checks.extend(
            [
                item.verify_slug(known),
                item.validate_power(),
                item.ensure_no_vga(),
                item.validate_child_u_height(),
            ]
        )
    if category in {"device-types", "module-types"}:
        rear_port_names = {
            port.get("name")
            for port in definition.get("rear-ports", []) or []
            if isinstance(port, dict)
        }
        for front_port in definition.get("front-ports", []) or []:
            if (
                isinstance(front_port, dict)
                and front_port.get("rear_port")
                and front_port["rear_port"] not in rear_port_names
            ):
                errors.append(
                    f"front-port {front_port.get('name')!r} references missing "
                    f"rear-port {front_port['rear_port']!r}"
                )
    if not all(checks):
        errors.append(item.failureMessage or "repository validation failed")
    return [f"{path}: {error}" for error in errors]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate definition files directly, including uncommitted files."
    )
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    registry = schema_registry()
    failures = []
    for file_path in args.files:
        path = (ROOT / file_path).resolve() if not file_path.is_absolute() else file_path
        if not path.is_file():
            failures.append(f"{path}: file does not exist")
            continue
        failures.extend(validate_file(path, registry))
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Validated {len(args.files)} definition file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
