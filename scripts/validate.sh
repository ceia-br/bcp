#!/usr/bin/env bash
# Valida o protocolo BCP com o CLI oficial `ucp-schema` (cargo install ucp-schema).
#
# 1. lint: estática de todos os schemas — $refs, anotações ucp_request/ucp_response
#    e os `examples` embutidos (regra E008, valida cada exemplo contra o schema).
# 2. validate: fixtures de ponta a ponta — compose (com authority binding
#    br.dev.bcp.* <-> bcp.dev.br) + resolve + validação do payload.
#    fixtures/valid/** devem passar; fixtures/invalid/** devem falhar.
#
# O mapeamento --schema-remote-base/--schema-local-base resolve as URLs
# https://bcp.dev.br/... para os arquivos locais, permitindo validar offline
# antes de o domínio existir.
set -euo pipefail

cd "$(dirname "$0")/.."                     # raiz do repo

UCP_SCHEMA="${UCP_SCHEMA:-$(command -v ucp-schema || echo "$HOME/.cargo/bin/ucp-schema")}"
REMOTE_BASE="https://bcp.dev.br"

if [ ! -x "$UCP_SCHEMA" ]; then
    echo "ERRO: ucp-schema nao encontrado em '$UCP_SCHEMA'." >&2
    echo "Instale com 'cargo install ucp-schema' ou aponte UCP_SCHEMA=/caminho." >&2
    exit 1
fi

echo "== versões de schema no fonte (devem ser injetadas no build) =="
uv run python <<'PY'
import json
from pathlib import Path

schema_files = sorted(
    path for directory in ("schemas", "discovery") for path in Path(directory).rglob("*.json")
)
if not schema_files:
    print("ERRO: nenhum schema encontrado; a trava nao validou nada", flush=True)
    raise SystemExit(1)
versioned_files = [
    path
    for path in schema_files
    if "version" in json.loads(path.read_text(encoding="utf-8"))
]
if versioned_files:
    print("ERRO: schemas com version no objeto raiz:", flush=True)
    for path in versioned_files:
        print(f"  {path}", flush=True)
    raise SystemExit(1)
print(f"  ok: {len(schema_files)} schemas sem version literal")
PY

echo "== lint =="
"$UCP_SCHEMA" lint schemas/ --quiet

echo "== fixtures válidos (devem passar) =="
for f in fixtures/valid/*.json; do
    "$UCP_SCHEMA" validate "$f" --op read \
        --schema-remote-base "$REMOTE_BASE" --schema-local-base . >/dev/null
    echo "  ok: $f"
done

echo "== fixtures inválidos (devem falhar) =="
for f in fixtures/invalid/*.json; do
    if "$UCP_SCHEMA" validate "$f" --op read \
        --schema-remote-base "$REMOTE_BASE" --schema-local-base . >/dev/null 2>&1; then
        echo "  ERRO: $f passou mas deveria falhar" >&2
        exit 1
    fi
    echo "  ok (rejeitado): $f"
done

echo "OK: protocolo validado"
