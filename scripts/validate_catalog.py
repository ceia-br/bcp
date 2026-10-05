import argparse
import copy
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_protocol import load_registry

CAPABILITY = "br.dev.bcp.shopping.catalog.publish"
PROTOCOL_VERSION = "2026-04-08"
CAPABILITY_VERSION = "2026-10-04"
SCHEMA = "https://bcp.dev.br/schemas/shopping/catalog_publication.json"
DESCRIPTION_FORMATS = ("plain", "html", "markdown")


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


@dataclass(frozen=True)
class Result:
    http_status: int
    response: dict[str, Any]
    catalog: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None


@lru_cache
def _validator(definition: str) -> Draft202012Validator:
    return Draft202012Validator(
        {"$ref": f"{SCHEMA}#/$defs/{definition}"},
        registry=load_registry(),
        format_checker=FormatChecker(),
    )


def _jsonpath(parts: Any) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f"[{json.dumps(part, ensure_ascii=False)}]"
    return path


def schema_issues(payload: Any, definition: str) -> list[Issue]:
    """Validate structural constraints against the local draft 2020-12 registry."""
    issues: list[Issue] = []
    for error in _validator(definition).iter_errors(payload):
        parts = list(error.absolute_path)
        if error.validator == "required":
            for field in error.validator_value:
                if error.message == f"{field!r} is a required property":
                    parts.append(field)
                    break
        issues.append(Issue("catalog_schema_invalid", _jsonpath(parts), error.message))
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
    for index, variant in enumerate(product["variants"]):
        selections = variant.get("options", [])
        names = [selection["name"] for selection in selections]
        variant_path = f"{path}.variants[{index}].options"
        if len(names) != len(set(names)) or set(names) != set(options):
            issues.append(
                Issue(
                    "catalog_option_selection_invalid",
                    variant_path,
                    "Select each declared product option exactly once.",
                )
            )
        for i, selection in enumerate(selections):
            values = options.get(selection["name"], [])
            if "id" in selection:
                matches = [
                    value for value in values if value.get("id") == selection["id"]
                ]
                valid = len(matches) == 1 and matches[0]["label"] == selection["label"]
            else:
                valid = any(value["label"] == selection["label"] for value in values)
            if not valid:
                issues.append(
                    Issue(
                        "catalog_option_selection_invalid",
                        f"{variant_path}[{i}]",
                        "The selection must match a declared option value and label.",
                    )
                )
    return issues


def _metadata() -> dict[str, Any]:
    return {
        "version": PROTOCOL_VERSION,
        "status": "success",
        "capabilities": {CAPABILITY: [{"version": CAPABILITY_VERSION}]},
    }


def _failure(status: int, issues: list[Issue]) -> Result:
    metadata = _metadata()
    metadata["status"] = "error"
    return Result(
        status, {"ucp": metadata, "messages": [issue.message() for issue in issues]}
    )


def validate_catalog(catalog: Any) -> list[Issue]:
    """Validate an accepted snapshot, including its supported versions and products."""
    issues = schema_issues(catalog, "catalog")
    if issues:
        return issues
    return _version_issues(catalog) + product_issues(catalog["products"])


def _version_issues(payload: dict[str, Any]) -> list[Issue]:
    if payload["ucp"]["version"] != PROTOCOL_VERSION:
        return [
            Issue(
                "version_unsupported", "$.ucp.version", "Unsupported protocol version."
            )
        ]
    if payload["ucp"]["capabilities"][CAPABILITY][0]["version"] != CAPABILITY_VERSION:
        return [
            Issue(
                "version_unsupported",
                f"$.ucp.capabilities['{CAPABILITY}'][0].version",
                "Unsupported catalog publication capability version.",
            )
        ]
    return []


def _response(catalog: dict[str, Any]) -> dict[str, Any]:
    return {
        "ucp": _metadata(),
        "catalog_id": catalog["catalog_id"],
        "merchant_id": catalog["merchant_id"],
        "revision": catalog["revision"],
        "product_count": len(catalog["products"]),
    }


def evaluate_publication(
    payload: Any,
    *,
    operation: str,
    catalog_id: str,
    idempotency_key: str,
    current: Any = None,
    publisher_id: str = "offline",
    receipt: Any = None,
    request_body: bytes | None = None,
) -> Result:
    """Evaluate a write with trusted state, without authentication, persistence or network.

    Transports pass the original request_body bytes for BCP digest matching.
    In-memory callers without bytes use the compact serialization of payload.
    """
    if operation not in ("replace", "update"):
        raise ValueError("operation must be replace or update")
    if (
        not catalog_id.strip()
        or not publisher_id.strip()
        or not idempotency_key.strip()
    ):
        return _failure(
            400,
            [
                Issue(
                    "publication_identity_required",
                    "$",
                    "Catalog, publisher and idempotency identifiers are required.",
                )
            ],
        )
    encoded = request_body
    if encoded is None:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    scope = {
        "publisher_id": publisher_id,
        "catalog_id": catalog_id,
        "idempotency_key": idempotency_key,
    }
    if isinstance(receipt, dict) and all(
        receipt.get(key) == value for key, value in scope.items()
    ):
        if (
            receipt["operation"] != operation
            or receipt["request_digest"] != fingerprint
        ):
            return _failure(
                409,
                [
                    Issue(
                        "idempotency_conflict",
                        "$",
                        "This key was already used for a different request.",
                    )
                ],
            )
        return Result(
            receipt["http_status"],
            copy.deepcopy(receipt["response"]),
            receipt=copy.deepcopy(receipt),
        )

    result = _evaluate_request(
        payload, operation=operation, catalog_id=catalog_id, current=current
    )
    recorded_receipt = {
        **scope,
        "operation": operation,
        "request_digest": fingerprint,
        "http_status": result.http_status,
        "response": copy.deepcopy(result.response),
    }
    return Result(result.http_status, result.response, result.catalog, recorded_receipt)


def _evaluate_request(
    payload: Any, *, operation: str, catalog_id: str, current: Any
) -> Result:
    issues = schema_issues(payload, f"{operation}_request")
    if issues:
        return _failure(422, issues)
    issues = _version_issues(payload)
    if issues:
        return _failure(422, issues)

    if current is not None:
        issues = validate_catalog(current)
        if issues:
            return _failure(422, issues)
        if (
            current["catalog_id"] != catalog_id
            or current["merchant_id"] != payload["merchant_id"]
        ):
            return _failure(
                409,
                [
                    Issue(
                        "catalog_identity_conflict",
                        "$.merchant_id",
                        "Catalog identity and merchant ownership are immutable.",
                    )
                ],
            )
    elif operation == "update":
        return _failure(
            404,
            [Issue("catalog_not_found", "$", "Create the catalog before updating it.")],
        )
    expected_revision = current["revision"] if current is not None else None
    if payload["base_revision"] != expected_revision:
        return _failure(
            409,
            [
                Issue(
                    "revision_conflict",
                    "$.base_revision",
                    "Read the current catalog and reapply the intended changes.",
                )
            ],
        )

    if operation == "replace":
        products = payload["products"]
    else:
        upserts = payload["upsert_products"]
        removals = set(payload["remove_product_ids"])
        issues = product_issues(upserts, "$.upsert_products")
        if not upserts and not removals:
            issues.append(
                Issue(
                    "catalog_update_empty",
                    "$",
                    "Provide at least one update or removal.",
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
        if issues:
            return _failure(422, issues)
        by_id = {product["id"]: product for product in current["products"]}
        for identifier in removals:
            by_id.pop(identifier, None)
        for product in upserts:
            by_id[product["id"]] = product
        products = list(by_id.values())
    issues = product_issues(products)
    if issues:
        return _failure(422, issues)
    catalog = {
        "ucp": _metadata(),
        "catalog_id": catalog_id,
        "merchant_id": payload["merchant_id"],
        "revision": (expected_revision or 0) + 1,
        "products": copy.deepcopy(products),
    }
    status = 201 if current is None else 200
    response = _response(catalog)
    return Result(status, response, catalog)


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


def _parse_json(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
        parse_float=_finite_number,
    )


def read_json(path: Path) -> Any:
    return _parse_json(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline BCP catalog conformance; no network or authentication."
    )
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--operation", choices=("replace", "update", "catalog"), default="replace"
    )
    parser.add_argument("--catalog-id")
    parser.add_argument("--publisher-id", default="offline")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--current", type=Path)
    parser.add_argument(
        "--receipt",
        type=Path,
        help="Trusted receipt from a previously processed write.",
    )
    args = parser.parse_args()
    if args.operation != "catalog" and (
        not args.catalog_id or not args.idempotency_key
    ):
        parser.error("writes require --catalog-id and --idempotency-key")
    try:
        request_body = args.file.read_bytes()
        payload = _parse_json(request_body.decode("utf-8"))
        if args.operation == "catalog":
            issues = validate_catalog(payload)
            result = (
                _failure(422, issues)
                if issues
                else Result(200, _response(payload), payload)
            )
        else:
            result = evaluate_publication(
                payload,
                operation=args.operation,
                catalog_id=args.catalog_id,
                publisher_id=args.publisher_id,
                idempotency_key=args.idempotency_key,
                current=read_json(args.current) if args.current else None,
                receipt=read_json(args.receipt) if args.receipt else None,
                request_body=request_body,
            )
        print(json.dumps(asdict(result), indent=2))
        return 0 if result.http_status < 400 else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Unable to validate local input: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
