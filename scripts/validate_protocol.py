import json
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError, _WrappedReferencingError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

PROTOCOL_DIR = Path(__file__).resolve().parent.parent
AUTHORITY = "https://bcp.dev.br"
SCHEMA_ROOTS = ("schemas", "discovery")
FIXTURES_DIR = PROTOCOL_DIR / "fixtures"
EXPECTATIONS_PATH = FIXTURES_DIR / "expectations.json"
DOC_ROOTS = ("docs", "docs-en")

ANNOTATION_STATES = frozenset({"omit", "optional", "required"})
ANNOTATION_OPS = frozenset({"create", "update", "complete"})
EXAMPLE_ANNOTATION = re.compile(r"ucp:example\s+([^>]*?)-->")

# Envelope schemas the docs annotate but the fork never vendored: A2A 1.0 is
# normative in Protobuf and the MCP/JSON-RPC/EP envelopes have no BCP source.
# Tracked in docs/features/playground-a2a-pendencias.md; anything outside this
# list must resolve to a local file.
UNVENDORED_DOC_SCHEMAS = frozenset(
    {
        "transports/a2a_message",
        "transports/embedded_message",
        "transports/jsonrpc",
        "transports/mcp_tool_call",
    }
)

JsonObject = dict[str, Any]


@dataclass
class Report:
    """Accumulates failures and notes across the individual checks."""

    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


@dataclass(frozen=True)
class SchemaFile:
    """A vendored schema together with the path it was loaded from."""

    path: Path
    relative: Path
    document: JsonObject

    @property
    def schema_id(self) -> str | None:
        value = self.document.get("$id")
        return value if isinstance(value, str) else None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_files() -> list[SchemaFile]:
    files: list[SchemaFile] = []
    for root in SCHEMA_ROOTS:
        for path in sorted((PROTOCOL_DIR / root).rglob("*.json")):
            document = _load_json(path)
            if not isinstance(document, dict):
                raise ValueError(f"expected a JSON object in {path}")
            files.append(SchemaFile(path, path.relative_to(PROTOCOL_DIR), document))
    return files


def _registry(files: Sequence[SchemaFile]) -> Registry[Any]:
    registry: Registry[Any] = Registry()
    for schema in files:
        if schema.schema_id is not None:
            registry = registry.with_resource(
                schema.schema_id, Resource.from_contents(schema.document)
            )
    return registry


def _walk(node: Any, pointer: str = "") -> Iterator[tuple[str, Any]]:
    yield pointer, node
    if isinstance(node, dict):
        for key, value in node.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from _walk(value, f"{pointer}/{escaped}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{pointer}/{index}")


def _resolve_pointer(document: Any, fragment: str) -> Any:
    if not fragment or fragment == "/":
        return document
    node = document
    for raw in fragment.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict):
            if token not in node:
                raise KeyError(token)
            node = node[token]
        elif isinstance(node, list):
            node = node[int(token)]
        else:
            raise KeyError(token)
    return node


def check_no_literal_version(files: Sequence[SchemaFile], report: Report) -> None:
    """Schema versions are injected at build time, never written in the source."""
    for schema in files:
        if "version" in schema.document:
            report.fail(f"{schema.relative}: version literal no objeto raiz")
    report.note(f"{len(files)} schemas sem version literal")


def check_identity(files: Sequence[SchemaFile], report: Report) -> None:
    """Every $id is unique and lives under the directory that holds the file."""
    seen: dict[str, Path] = {}
    for schema in files:
        schema_id = schema.schema_id
        if schema_id is None:
            report.fail(f"{schema.relative}: sem $id")
            continue
        if schema_id in seen:
            report.fail(f"{schema.relative}: $id duplicado de {seen[schema_id]}")
        seen[schema_id] = schema.relative
        prefix = f"{AUTHORITY}/{schema.relative.parent.as_posix()}/"
        remainder = schema_id.removeprefix(prefix)
        if remainder == schema_id or "/" in remainder:
            report.fail(f"{schema.relative}: $id '{schema_id}' nao resolve sob '{prefix}'")


def check_metaschema(files: Sequence[SchemaFile], report: Report) -> None:
    """Each schema is itself a valid JSON Schema draft 2020-12 document."""
    for schema in files:
        try:
            Draft202012Validator.check_schema(schema.document)
        except SchemaError as error:
            report.fail(f"{schema.relative}: schema invalido: {error.message}")


def check_refs(files: Sequence[SchemaFile], registry: Registry[Any], report: Report) -> None:
    """Every $ref resolves by $id-relative URI, the way a remote consumer resolves it."""
    resolver = registry.resolver()
    total = 0
    for schema in files:
        base = schema.schema_id
        if base is None:
            continue
        for pointer, node in _walk(schema.document):
            if not isinstance(node, dict):
                continue
            ref = node.get("$ref")
            if not isinstance(ref, str):
                continue
            total += 1
            target, fragment = urldefrag(urljoin(base, ref))
            try:
                document = registry.contents(target) if target != base else schema.document
            except LookupError:
                try:
                    document = resolver.lookup(target).contents
                except Unresolvable:
                    report.fail(f"{schema.relative}{pointer}: $ref '{ref}' nao resolve ({target})")
                    continue
            if fragment.startswith("/") or not fragment:
                try:
                    _resolve_pointer(document, fragment)
                except (KeyError, IndexError, ValueError):
                    report.fail(f"{schema.relative}{pointer}: $ref '{ref}' sem alvo '#{fragment}'")
    report.note(f"{total} $refs resolvidos por URI")


def check_annotations(files: Sequence[SchemaFile], report: Report) -> None:
    """ucp_request/ucp_response only carry the documented states and operations."""
    for schema in files:
        for pointer, node in _walk(schema.document):
            if not isinstance(node, dict):
                continue
            for key in ("ucp_request", "ucp_response"):
                value = node.get(key)
                if value is None:
                    continue
                if isinstance(value, str):
                    if value not in ANNOTATION_STATES:
                        report.fail(f"{schema.relative}{pointer}: {key} invalido '{value}'")
                    continue
                if not isinstance(value, dict):
                    report.fail(f"{schema.relative}{pointer}: {key} nao e string nem objeto")
                    continue
                for operation, state in value.items():
                    if operation not in ANNOTATION_OPS:
                        report.fail(f"{schema.relative}{pointer}: {key} com op '{operation}'")
                    if state not in ANNOTATION_STATES:
                        report.fail(f"{schema.relative}{pointer}: {key}.{operation} = '{state}'")


def check_embedded_examples(
    files: Sequence[SchemaFile], registry: Registry[Any], report: Report
) -> None:
    """Every `examples` entry validates against the subschema that declares it."""
    total = 0
    for schema in files:
        base = schema.schema_id
        if base is None:
            continue
        for pointer, node in _walk(schema.document):
            if not isinstance(node, dict) or not isinstance(node.get("examples"), list):
                continue
            subschema = {key: value for key, value in node.items() if key != "examples"}
            if not subschema:
                continue
            subschema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            subschema["$id"] = base
            validator = Draft202012Validator(
                subschema, registry=registry, format_checker=FormatChecker()
            )
            for index, example in enumerate(node["examples"]):
                total += 1
                for error in validator.iter_errors(example):
                    report.fail(f"{schema.relative}{pointer}/examples/{index}: {error.message}")
    report.note(f"{total} examples embutidos validados")


def _capability_schemas(files: Sequence[SchemaFile]) -> dict[str, SchemaFile]:
    return {
        name: schema for schema in files if isinstance(name := schema.document.get("name"), str)
    }


def _composed_uris(payload: Any, by_name: dict[str, SchemaFile]) -> list[str]:
    """Resolve the schema URIs a payload declares through its own ucp.capabilities."""
    capabilities = payload.get("ucp", {}).get("capabilities", {})
    if not isinstance(capabilities, dict):
        return []
    uris: list[str] = []
    for name, entries in sorted(capabilities.items()):
        schema = by_name.get(name)
        if schema is None or schema.schema_id is None:
            continue
        entry = entries[0] if isinstance(entries, list) and entries else {}
        extends = entry.get("extends") if isinstance(entry, dict) else None
        if extends is None:
            uris.append(schema.schema_id)
        else:
            uris.append(f"{schema.schema_id}#/$defs/{extends}")
    return uris


def _errors(payload: Any, uri: str, registry: Registry[Any]) -> list[ValidationError]:
    """Validation errors for a payload, or ValueError when the URI itself does not resolve."""
    validator = Draft202012Validator(
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": uri},
        registry=registry,
        format_checker=FormatChecker(),
    )
    try:
        errors = list(validator.iter_errors(payload))
    except _WrappedReferencingError as error:
        raise ValueError(f"schema '{uri}' nao resolve: {error}") from error
    return sorted(errors, key=lambda error: list(error.absolute_path))


def check_fixtures(files: Sequence[SchemaFile], registry: Registry[Any], report: Report) -> None:
    """Valid fixtures compose and pass; invalid ones fail for their declared reason."""
    by_name = _capability_schemas(files)
    expectations = _load_json(EXPECTATIONS_PATH)

    valid_paths = sorted((FIXTURES_DIR / "valid").glob("*.json"))
    approved = 0
    for path in valid_paths:
        payload = _load_json(path)
        declared = expectations["valid"].get(path.name, {}).get("schemas")
        uris = declared if declared is not None else _composed_uris(payload, by_name)
        if not uris:
            report.fail(f"fixtures/valid/{path.name}: nao declara capabilities validaveis")
            continue
        clean = True
        for uri in uris:
            try:
                errors = _errors(payload, uri, registry)
            except ValueError as failure:
                report.fail(f"fixtures/valid/{path.name}: {failure}")
                clean = False
                continue
            for error in errors:
                location = "/".join(str(part) for part in error.absolute_path)
                report.fail(f"fixtures/valid/{path.name} [{uri}] {location}: {error.message}")
                clean = False
        approved += clean
    report.note(f"{approved} de {len(valid_paths)} fixtures validas compostas e aprovadas")

    invalid_paths = sorted((FIXTURES_DIR / "invalid").glob("*.json"))
    for name in sorted(set(expectations["invalid"]) - {path.name for path in invalid_paths}):
        report.fail(f"expectations.json: motivo declarado para fixture inexistente '{name}'")

    rejected = 0
    for path in invalid_paths:
        payload = _load_json(path)
        expectation = expectations["invalid"].get(path.name)
        if expectation is None:
            report.fail(f"fixtures/invalid/{path.name}: sem motivo declarado em expectations.json")
            continue
        uri = expectation["schema"]
        try:
            errors = _errors(payload, uri, registry)
        except ValueError as failure:
            report.fail(f"fixtures/invalid/{path.name}: {failure}")
            continue
        if not errors:
            report.fail(f"fixtures/invalid/{path.name}: passou em {uri}, deveria falhar")
            continue
        wanted_path = expectation.get("instance_path", "")
        wanted_keyword = expectation["keyword"]
        wanted_message = expectation["message_contains"]
        matched = [
            error
            for error in errors
            if "/".join(str(part) for part in error.absolute_path) == wanted_path
            and error.validator == wanted_keyword
            and wanted_message in error.message
        ]
        if matched:
            rejected += 1
            continue
        found = "; ".join(
            f"[{'/'.join(str(part) for part in error.absolute_path)}] "
            f"{error.validator}: {error.message}"
            for error in errors[:3]
        )
        report.fail(
            f"fixtures/invalid/{path.name}: falhou por outro motivo. "
            f"Esperado {wanted_keyword} em '{wanted_path}' contendo "
            f"'{wanted_message}'; obtido: {found}"
        )
    report.note(
        f"{rejected} de {len(invalid_paths)} fixtures invalidas rejeitadas pelo motivo certo"
    )


def _annotation_schemas() -> set[str]:
    names: set[str] = set()
    for root in DOC_ROOTS:
        for path in sorted((PROTOCOL_DIR / root).rglob("*.md")):
            for match in EXAMPLE_ANNOTATION.finditer(path.read_text(encoding="utf-8")):
                for token in match.group(1).split():
                    if token.startswith("schema="):
                        names.add(token.removeprefix("schema="))
    return names


def check_doc_annotations(files: Sequence[SchemaFile], report: Report) -> None:
    """Schemas named by `ucp:example` annotations exist locally, or are known gaps."""
    available = {
        schema.relative.with_suffix("").as_posix().removeprefix("schemas/") for schema in files
    }
    available.add("profile")  # discovery/profile_schema.json is annotated as `profile`
    for name in sorted(_annotation_schemas()):
        if name in available or name in UNVENDORED_DOC_SCHEMAS:
            continue
        report.fail(f"docs: anotacao ucp:example aponta para schema inexistente '{name}'")
    report.note(
        f"{len(UNVENDORED_DOC_SCHEMAS)} envelopes de transporte nao vendorados (conhecidos)"
    )


def main() -> int:
    report = Report()
    files = _schema_files()
    if not files:
        sys.stderr.write("ERRO: nenhum schema encontrado; a trava nao validou nada\n")
        return 1
    registry = _registry(files)

    check_no_literal_version(files, report)
    check_identity(files, report)
    check_metaschema(files, report)
    check_refs(files, registry, report)
    check_annotations(files, report)
    check_embedded_examples(files, registry, report)
    check_fixtures(files, registry, report)
    check_doc_annotations(files, report)

    for note in report.notes:
        sys.stdout.write(f"  ok: {note}\n")
    for failure in report.failures:
        sys.stderr.write(f"  ERRO: {failure}\n")
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
