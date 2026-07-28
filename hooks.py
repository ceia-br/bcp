#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import json
import logging
import re
import shutil
from collections.abc import MutableMapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from mkdocs.plugins import event_priority

log = logging.getLogger("mkdocs")

type Config = MutableMapping[str, object]

BASE_DIR = Path(__file__).resolve().parent
BCP_SCHEMA_PREFIX = "https://bcp.dev.br/schemas/"
BCP_AUTHORITY = "https://bcp.dev.br"
DATE_VERSION_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _publication_date() -> str:
    """Return the build date in UTC, YYYY-MM-DD format."""
    return datetime.now(tz=UTC).date().isoformat()


def _extra(config: Config) -> MutableMapping[str, object]:
    """Return the mutable MkDocs extra configuration."""
    extra = config.get("extra")
    if isinstance(extra, MutableMapping):
        return cast("MutableMapping[str, object]", extra)
    extra = {}
    config["extra"] = extra
    return extra


def _docs_version(config: Config) -> tuple[str, str]:
    """Resolve the URL label and schema publication version."""
    url_version = str(_extra(config).get("bcp_version") or "draft")
    if DATE_VERSION_PATTERN.fullmatch(url_version):
        return url_version, url_version
    schema_version = _publication_date()
    log.info(
        "Non-date version '%s': schema version set to '%s'",
        url_version,
        schema_version,
    )
    return url_version, schema_version


def _versioned_schema_url(url_version: str) -> str:
    """Return the versioned schema URL prefix."""
    return f"https://bcp.dev.br/{url_version}/schemas/"


def _process_refs(data: object, current_file_dir: Path, url_version: str | None) -> None:
    """Resolve relative $ref paths to absolute versioned schema URLs."""
    if isinstance(data, dict):
        values = cast("dict[str, object]", data)
        for key, value in values.items():
            if key == "$ref" and isinstance(value, str) and not value.startswith(("#", "http")):
                ref_parts = value.split("#", 1)
                relative_path = ref_parts[0]
                fragment = f"#{ref_parts[1]}" if len(ref_parts) > 1 else ""

                if not relative_path:
                    continue

                ref_file_path = (current_file_dir / relative_path).resolve()
                try:
                    with ref_file_path.open(encoding="utf-8") as f:
                        ref_data = json.load(f)
                except FileNotFoundError:
                    log.error("Referenced schema not found: %s", ref_file_path)
                    continue
                except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
                    log.error("Failed to read referenced schema %s: %s", ref_file_path, exc)
                    continue

                ref_id = ref_data.get("$id")
                if ref_id:
                    if url_version and ref_id.startswith(BCP_SCHEMA_PREFIX):
                        ref_id = ref_id.replace(
                            BCP_SCHEMA_PREFIX,
                            _versioned_schema_url(url_version),
                            1,
                        )
                    values[key] = ref_id + fragment
                else:
                    log.warning("No '$id' found in %s", ref_file_path)
            else:
                _process_refs(value, current_file_dir, url_version)
    elif isinstance(data, list):
        for item in data:
            _process_refs(item, current_file_dir, url_version)


def _rewrite_version_urls(data: object, url_version: str) -> None:
    """Rewrite schema/spec URLs to include the version path."""
    if isinstance(data, dict):
        values = cast("dict[str, object]", data)
        for key, value in values.items():
            if (
                key in ("$id", "$ref", "schema", "spec")
                and isinstance(value, str)
                and value.startswith(BCP_SCHEMA_PREFIX)
            ):
                values[key] = value.replace(
                    BCP_SCHEMA_PREFIX,
                    _versioned_schema_url(url_version),
                    1,
                )
            else:
                _rewrite_version_urls(value, url_version)
    elif isinstance(data, list):
        for item in data:
            _rewrite_version_urls(item, url_version)


def _set_schema_version(data: dict[str, object], version: str) -> None:
    """Set the version field for named entities."""
    if "name" in data:
        data["version"] = version
    info = data.get("info")
    if ("openapi" in data or "openrpc" in data) and isinstance(info, dict):
        cast("dict[str, object]", info)["version"] = version


def _output_path(data: dict[str, object], rel_path: Path) -> Path:
    """Map a schema $id to the static site path."""
    file_id = data.get("$id")
    if isinstance(file_id, str) and file_id.startswith(BCP_AUTHORITY):
        return Path(file_id.removeprefix(BCP_AUTHORITY).lstrip("/"))
    return rel_path


def _copy_processed_json(
    src_file: Path,
    rel_path: Path,
    site_dir: Path,
    url_version: str,
    schema_version: str,
) -> None:
    """Process and copy one JSON file into the static site."""
    try:
        with src_file.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        log.error("Failed to process %s, copying as-is: %s", src_file, exc)
        dest_file = site_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        return

    dest_rel_path = _output_path(data, rel_path)
    _process_refs(data, src_file.parent, url_version)
    _set_schema_version(data, schema_version)
    _rewrite_version_urls(data, url_version)

    dest_file = site_dir / dest_rel_path
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    with dest_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    log.info("Processed and copied %s to %s", src_file, dest_file)


def _copy_protocol_tree(
    source_dir: Path,
    site_dir: Path,
    url_version: str,
    schema_version: str,
) -> None:
    """Copy a protocol source tree into the static site."""
    if not source_dir.exists():
        log.warning("Protocol source directory not found: %s", source_dir)
        return
    for src_file in source_dir.rglob("*"):
        if not src_file.is_file():
            continue
        rel_path = src_file.relative_to(source_dir)
        if src_file.suffix == ".json":
            _copy_processed_json(
                src_file,
                rel_path,
                site_dir,
                url_version,
                schema_version,
            )
            continue
        dest_file = site_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)


def _copy_notices(site_dir: Path) -> None:
    """Copy legal and provenance files used by the attribution page."""
    for filename in ("LICENSE", "NOTICE", "CHANGELOG-divergencia.md"):
        src = BASE_DIR / filename
        if not src.exists():
            continue
        shutil.copy2(src, site_dir / filename)


def _copy_playground(site_dir: Path) -> None:
    """Copy frozen playground files without rewriting their JSON payloads."""
    source_dir = BASE_DIR / "playground"
    directories = (
        (source_dir / "web", site_dir / "playground" / "app"),
        (
            source_dir / "snapshots",
            site_dir / "assets" / "playground" / "snapshots",
        ),
    )
    for source, target in directories:
        if not source.exists():
            log.warning("Playground source directory not found: %s", source)
            continue
        shutil.copytree(source, target, dirs_exist_ok=True)
    license_dir = site_dir / "assets" / "playground"
    license_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("FONT-LICENSES.md", "OFL-1.1.txt"):
        shutil.copy2(source_dir / "static" / filename, license_dir / filename)


@event_priority(100)
def on_config(config: Config) -> Config:
    """Resolve docs version and expose it to templates."""
    url_version, schema_version = _docs_version(config)
    extra = _extra(config)
    extra["bcp_version"] = url_version
    extra["bcp_schema_version"] = schema_version
    extra["ucp_version"] = url_version
    return config


def on_post_build(config: Config) -> None:
    """Copy protocol, playground, and legal files after the MkDocs build."""
    extra = _extra(config)
    url_version = str(extra["bcp_version"])
    schema_version = str(extra["bcp_schema_version"])
    site_dir = Path(str(config["site_dir"]))

    _copy_protocol_tree(
        BASE_DIR / "schemas",
        site_dir,
        url_version,
        schema_version,
    )
    _copy_protocol_tree(
        BASE_DIR / "discovery",
        site_dir,
        url_version,
        schema_version,
    )
    _copy_playground(site_dir)
    _copy_notices(site_dir)
