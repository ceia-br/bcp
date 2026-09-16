import io
import re
import sys
import urllib.request
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

_REPO_DIR = Path(__file__).resolve().parent.parent
_PLAYGROUND_DIR = _REPO_DIR / "playground"
_STATIC_DIR = _PLAYGROUND_DIR / "static"
_TEXT_SOURCES = (
    _REPO_DIR / "docs" / "playground.md",
    _REPO_DIR / "docs-en" / "playground.md",
)
_USER_AGENT = "Mozilla/5.0 (compatible; BCP playground font vendor/1.0)"
_CSS_URL = (
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700"
    "&family=IBM+Plex+Mono:wght@400;500&display=swap"
)


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read()


def _is_latin(block: str) -> bool:
    match = re.search(r"unicode-range:\s*([^;]+);", block)
    if not match:
        return True
    value = match.group(1)
    return "U+0000-00FF" in value or "U+0100-02BA" in value


def _subset(font_data: bytes, text: str) -> bytes:
    options = Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.hinting = False
    options.desubroutinize = True
    font = TTFont(io.BytesIO(font_data))
    subsetter = Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.flavor = "woff2"
    buffer = io.BytesIO()
    font.save(buffer)
    return buffer.getvalue()


def _playground_text() -> str:
    sources = [path.read_text(encoding="utf-8") for path in _TEXT_SOURCES]
    for path in sorted(_PLAYGROUND_DIR.rglob("*")):
        if path.is_file() and path.suffix in {".json", ".js"}:
            sources.append(path.read_text(encoding="utf-8"))
    return "\n".join(sources)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _font_entries(text: str) -> list[tuple[str, int, bytes]]:
    css = _fetch(_CSS_URL).decode("utf-8")
    cache: dict[str, bytes] = {}
    entries: list[tuple[str, int, bytes]] = []
    for block in re.findall(r"@font-face\s*\{[^}]*\}", css):
        if not _is_latin(block):
            continue
        url_match = re.search(r"url\((https://[^)]+)\)", block)
        family_match = re.search(r"font-family:\s*'([^']+)'", block)
        weight_match = re.search(r"font-weight:\s*(\d+)", block)
        if not (url_match and family_match and weight_match):
            continue
        url = url_match.group(1)
        if url not in cache:
            cache[url] = _subset(_fetch(url), text)
        entries.append((family_match.group(1), int(weight_match.group(1)), cache[url]))
    return entries


def _write_fonts(entries: list[tuple[str, int, bytes]]) -> None:
    groups: dict[tuple[str, bytes], list[int]] = {}
    for family, weight, data in entries:
        groups.setdefault((family, data), []).append(weight)

    _STATIC_DIR.mkdir(parents=True, exist_ok=True)
    faces: list[str] = []
    for (family, data), weights in groups.items():
        low, high = min(weights), max(weights)
        weight_range = str(low) if low == high else f"{low} {high}"
        filename = f"{_slug(family)}-{low}-{high}.woff2"
        (_STATIC_DIR / filename).write_bytes(data)
        faces.append(
            "@font-face {\n"
            f'  font-family: "{family}";\n'
            "  font-style: normal;\n"
            f"  font-weight: {weight_range};\n"
            "  font-display: swap;\n"
            f'  src: url("{filename}") format("woff2");\n'
            "}"
        )
    (_STATIC_DIR / "fonts.css").write_text("\n\n".join(faces) + "\n", encoding="utf-8")


def main() -> None:
    """Generate local WOFF2 subsets and CSS for the MkDocs playground."""
    entries = _font_entries(_playground_text())
    if not entries:
        raise SystemExit("Nenhuma fonte latin foi encontrada")
    _write_fonts(entries)
    sys.stdout.write(f"Fontes do playground geradas em {_STATIC_DIR}\n")


if __name__ == "__main__":
    main()
