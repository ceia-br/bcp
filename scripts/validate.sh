#!/usr/bin/env bash
# Valida o protocolo BCP.
#
# 1. `validate_protocol.py` é a trava: roda só com as dependências do workspace
#    (jsonschema + referencing), então funciona na CI sem toolchain externa.
#    Cobre $id/$ref por resolução de URI, metaschema, anotações ucp_request/
#    ucp_response, examples embutidos, fixtures válidas por composição e
#    fixtures inválidas pelo motivo declarado em fixtures/expectations.json.
# 2. `ucp-schema lint` (cargo install ucp-schema) é reforço opcional: aplica as
#    regras E### do CLI oficial. Quando o binário não está no ambiente, o passo
#    é anunciado e pulado — a trava do item 1 já rodou.
#
# Fronteira entre os dois: a resolução de $ref do `lint` é por caminho de
# arquivo, então ela não enxerga divergência entre o $id e a URL publicada;
# quem cobre isso é o validador local.
set -euo pipefail

cd "$(dirname "$0")/.."                     # raiz do repo

UCP_SCHEMA="${UCP_SCHEMA:-$(command -v ucp-schema || echo "$HOME/.cargo/bin/ucp-schema")}"

echo "== validador local (trava) =="
uv run --group playground python scripts/validate_protocol.py

echo "== lint ucp-schema (reforço opcional) =="
if [ -x "$UCP_SCHEMA" ]; then
    "$UCP_SCHEMA" lint schemas/ --quiet
    "$UCP_SCHEMA" lint discovery/ --quiet
    echo "  ok: schemas/ e discovery/"
else
    echo "  pulado: ucp-schema ausente (instale com 'cargo install ucp-schema'"
    echo "          ou aponte UCP_SCHEMA=/caminho para rodar o reforço)."
fi

echo "OK: protocolo validado"
