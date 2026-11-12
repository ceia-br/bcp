import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.protocols import Validator

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_protocol import EXPECTATIONS_PATH, FIXTURES_DIR, load_registry

SCHEMA = "https://bcp.dev.br/schemas/shopping/catalog_publish.json"
DEFINITIONS = {
    "replace": "replace_request",
    "update": "update_request",
    "catalog": "catalog",
}
OPERATIONS = {definition: operation for operation, definition in DEFINITIONS.items()}
DESCRIPTION_FORMATS = ("plain", "html", "markdown")
MEMBER_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    content: str

    def message(self) -> dict[str, str]:
        """Use the existing BCP message format, including JSONPath locations."""
        return {
            "type": "error",
            "code": self.code,
            "path": self.path,
            "content": self.content,
            "severity": "recoverable",
        }


@lru_cache
def _validator(definition: str) -> Validator:
    return Draft202012Validator(
        {"$ref": f"{SCHEMA}#/$defs/{definition}"},
        registry=load_registry(),
        format_checker=FormatChecker(),
    )


def _jsonpath(parts: list[str | int]) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        elif MEMBER_NAME.fullmatch(part):
            path += f".{part}"
        else:
            path += f"[{json.dumps(part, ensure_ascii=False)}]"
    return path


def schema_issues(payload: Any, definition: str) -> list[Issue]:
    """Validate structural constraints against the local draft 2020-12 registry."""
    issues: set[Issue] = set()
    for error in _validator(definition).iter_errors(payload):
        parts = list(error.absolute_path)
        if error.validator == "required":
            for field in error.validator_value:
                if error.message == f"{field!r} is a required property":
                    parts.append(field)
                    break
        issues.add(Issue("catalog_schema_invalid", _jsonpath(parts), error.message))
    return sorted(issues, key=lambda issue: (issue.path, issue.content))


def product_issues(
    products: list[dict[str, Any]], prefix: str = "$.products"
) -> list[Issue]:
    """Check cross-field invariants after structural validation has succeeded."""
    issues: list[Issue] = []
    identifiers: set[str] = set()
    for index, product in enumerate(products):
        path = f"{prefix}[{index}]"
        entities = [(product, path)] + [
            (variant, f"{path}.variants[{i}]")
            for i, variant in enumerate(product["variants"])
        ]
        for entity, entity_path in entities:
            identifier = entity["id"]
            if identifier in identifiers:
                issues.append(
                    Issue(
                        "catalog_id_duplicate",
                        f"{entity_path}.id",
                        f"Duplicate product or variant ID: {identifier}",
                    )
                )
            identifiers.add(identifier)
            if not any(
                entity["description"].get(fmt, "").strip()
                for fmt in DESCRIPTION_FORMATS
            ):
                issues.append(
                    Issue(
                        "catalog_description_empty",
                        f"{entity_path}.description",
                        "Provide nonblank plain, html or markdown content.",
                    )
                )

        currency = product["variants"][0]["price"]["currency"]
        prices = [variant["price"]["amount"] for variant in product["variants"]]
        money = [
            (product["price_range"][bound], f"{path}.price_range.{bound}")
            for bound in ("min", "max")
        ]
        if "list_price_range" in product:
            money.extend(
                (product["list_price_range"][bound], f"{path}.list_price_range.{bound}")
                for bound in ("min", "max")
            )
        for i, variant in enumerate(product["variants"]):
            money.extend(
                (variant[field], f"{path}.variants[{i}].{field}")
                for field in ("price", "list_price", "unit_price")
                if field in variant
            )
        for price, price_path in money:
            if price["currency"] != currency:
                issues.append(
                    Issue(
                        "catalog_currency_mismatch",
                        f"{price_path}.currency",
                        "Every price within a product must use the same currency.",
                    )
                )
        if (
            product["price_range"]["min"]["amount"],
            product["price_range"]["max"]["amount"],
        ) != (min(prices), max(prices)):
            issues.append(
                Issue(
                    "catalog_price_range_mismatch",
                    f"{path}.price_range",
                    "The range must equal the minimum and maximum variant prices.",
                )
            )
        issues.extend(_option_issues(product, path))
    return issues


def _selected_value(
    values: list[dict[str, Any]], selection: dict[str, Any]
) -> int | None:
    """Index of the declared value a selection points to, or None when none matches."""
    if "id" in selection:
        matches = [
            i for i, value in enumerate(values) if value.get("id") == selection["id"]
        ]
        if len(matches) == 1 and values[matches[0]]["label"] == selection["label"]:
            return matches[0]
        return None
    return next(
        (i for i, value in enumerate(values) if value["label"] == selection["label"]),
        None,
    )


def _option_issues(product: dict[str, Any], path: str) -> list[Issue]:
    issues: list[Issue] = []
    options: dict[str, list[dict[str, Any]]] = {}
    for index, option in enumerate(product.get("options", [])):
        name = option["name"]
        values = option["values"]
        labels = [value["label"] for value in values]
        ids = [value["id"] for value in values if "id" in value]
        if (
            not name.strip()
            or name in options
            or any(not label.strip() for label in labels)
            or len(labels) != len(set(labels))
            or len(ids) != len(set(ids))
            or any(not identifier.strip() for identifier in ids)
        ):
            issues.append(
                Issue(
                    "catalog_options_invalid",
                    f"{path}.options[{index}]",
                    "Option names and values must be nonblank and unambiguous.",
                )
            )
        options[name] = values
    combinations: set[frozenset[tuple[str, int]]] = set()
    for index, variant in enumerate(product["variants"]):
        selections = variant.get("options", [])
        names = [selection["name"] for selection in selections]
        variant_path = f"{path}.variants[{index}].options"
        complete = len(names) == len(set(names)) and set(names) == set(options)
        if not complete:
            issues.append(
                Issue(
                    "catalog_option_selection_invalid",
                    variant_path,
                    "Select each declared product option exactly once.",
                )
            )
        combination: set[tuple[str, int]] = set()
        for i, selection in enumerate(selections):
            value = _selected_value(options.get(selection["name"], []), selection)
            if value is None:
                issues.append(
                    Issue(
                        "catalog_option_selection_invalid",
                        f"{variant_path}[{i}]",
                        "The selection must match a declared option value and label.",
                    )
                )
            else:
                combination.add((selection["name"], value))
        if options and complete and len(combination) == len(options):
            if frozenset(combination) in combinations:
                issues.append(
                    Issue(
                        "catalog_option_selection_invalid",
                        variant_path,
                        "Another variant of this product has the same option values.",
                    )
                )
            combinations.add(frozenset(combination))
    return issues


def validate_document(payload: Any, operation: str) -> list[Issue]:
    """Check a publish payload against its schema and the conformance rules.

    Args:
        payload: Parsed JSON document.
        operation: "replace" (PUT body), "update" (PATCH body) or "catalog"
            (GET snapshot).

    Returns:
        Conformance issues; empty when the document is conformant.
    """
    issues = schema_issues(payload, DEFINITIONS[operation])
    if issues:
        return issues
    if operation != "update":
        return product_issues(payload["products"])
    upserts = payload["upsert_products"]
    removals = set(payload["remove_product_ids"])
    issues = product_issues(upserts, "$.upsert_products")
    if not upserts and not removals:
        issues.append(
            Issue(
                "catalog_update_empty", "$", "Provide at least one update or removal."
            )
        )
    if removals.intersection(product["id"] for product in upserts):
        issues.append(
            Issue(
                "catalog_update_overlap",
                "$.remove_product_ids",
                "A product cannot be upserted and removed in the same batch.",
            )
        )
    return issues


def check_fixtures() -> list[str]:
    """Run the repository's catalog publish fixtures through the conformance rules.

    Valid publish fixtures must be conformant; each fixture in
    fixtures/conformance/ must fail with the code and path declared in
    fixtures/expectations.json.

    Returns:
        Failure descriptions; empty when every fixture behaves as declared.
    """
    expectations = read_json(EXPECTATIONS_PATH)
    failures: list[str] = []
    for name, entry in sorted(expectations["valid"].items()):
        for uri in entry.get("schemas", []):
            base, _, definition = uri.partition("#/$defs/")
            if base != SCHEMA or definition not in OPERATIONS:
                continue
            payload = read_json(FIXTURES_DIR / "valid" / name)
            failures.extend(
                f"fixtures/valid/{name}: {issue.code} em {issue.path}"
                for issue in validate_document(payload, OPERATIONS[definition])
            )

    declared = expectations["conformance"]
    paths = sorted((FIXTURES_DIR / "conformance").glob("*.json"))
    for name in sorted(set(declared) - {path.name for path in paths}):
        failures.append(
            f"expectations.json: motivo declarado para fixture inexistente '{name}'"
        )
    for path in paths:
        entry = declared.get(path.name)
        if entry is None:
            failures.append(f"fixtures/conformance/{path.name}: sem motivo declarado")
            continue
        issues = validate_document(read_json(path), entry["operation"])
        if any(
            issue.code == entry["code"] and issue.path == entry["path"]
            for issue in issues
        ):
            continue
        found = "; ".join(f"{issue.code} em {issue.path}" for issue in issues)
        failures.append(
            f"fixtures/conformance/{path.name}: esperado {entry['code']} em "
            f"{entry['path']}; obtido: {found or 'nenhum erro'}"
        )
    return failures


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON member: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON number: {value}")


def _finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Invalid JSON number: {value}")
    return number


def read_json(path: Path) -> Any:
    """Parse JSON, rejecting duplicate members and non-finite numbers.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the content is not valid UTF-8 JSON under these rules.
    """
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
        parse_float=_finite_number,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline BCP catalog publish conformance; no network or state."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("file", nargs="?", type=Path, help="JSON document to check.")
    target.add_argument(
        "--fixtures",
        action="store_true",
        help="Check the repository's catalog publish fixtures.",
    )
    parser.add_argument("--operation", choices=tuple(DEFINITIONS), default="replace")
    args = parser.parse_args()
    try:
        if args.fixtures:
            failures = check_fixtures()
            for failure in failures:
                sys.stderr.write(f"  ERRO: {failure}\n")
            if not failures:
                sys.stdout.write("  ok: fixtures de publicacao de catalogo conformes\n")
            return 1 if failures else 0
        issues = validate_document(read_json(args.file), args.operation)
    except (OSError, ValueError) as error:
        sys.stderr.write(f"Unable to read local input: {error}\n")
        return 2
    report = {
        "conformant": not issues,
        "messages": [issue.message() for issue in issues],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
