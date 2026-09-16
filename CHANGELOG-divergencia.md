<!--
   Copyright 2026 BCP Authors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
-->

# Changelog de divergência: BCP vs UCP

Registro consciente do fork, atualizado a cada sync com o upstream: o que o
material derivado do UCP mudou, o que se mantém e o que o BCP decidiu não
acompanhar. As adições originais do BCP aparecem aqui só como lista; a spec
completa de cada uma vive em `docs/specification/`.

## Baseline

- O BCP deriva do UCP `2026-04-08` (spec vendorada em `schemas/` e
  `discovery/`).
- `discovery/profile_schema.json` (documento de well-known) vendorado com o
  mesmo rename de `$id`. O `$id` fica em
  `https://bcp.dev.br/discovery/profile.json`: o `$ref` herdado
  (`../schemas/ucp.json`) só resolve com base em `/discovery/`, que também é
  onde o arquivo mora no repo e onde o site o publica.
- `services/` (OpenAPI/OpenRPC) ainda não vendorados.
- `handlers/` contém apenas material original do BCP, nada vendorado do UCP.

## O que seguimos do UCP

- JSON Schema draft 2020-12, reverse-domain naming, `extends`/`allOf`.
- Versionamento por data, open enums, `ucp_request` (omit/optional/required
  por operação).
- Authority binding e serialização canônica (JCS) para assinatura.

## O que renomeamos

- `dev.ucp.*` → `br.dev.bcp.*` (nomes de capability, `extends`, chaves de
  `$defs`).
- `https://ucp.dev/...` → `https://bcp.dev.br/...` (em `$id` e URLs).
- `/.well-known/ucp` → `/.well-known/bcp` na descoberta do perfil comercial.
- `a2a.ucp.*` → `a2a.bcp.*` nas chaves estruturadas da extensão A2A.
- Mantidos como estão: o arquivo `ucp.json`, o campo de envelope `ucp` e a
  keyword `ucp_request` (renomear quebraria o validador sem ganho).

## O que divergimos de propósito

- O binding A2A acompanha a versão estável 1.0: Agent Card com
  `supportedInterfaces`, extensões em `capabilities.extensions`, header
  `A2A-Extensions` e Parts discriminados pelo nome do membro. O caminho do
  Agent Card permanece `/.well-known/agent-card.json`; as interfaces BCP usam
  `/bcp/a2a` nos exemplos.
- Perfis BCP publicam o JWK Set canônico em `keys[]`, no lugar do campo
  `signing_keys` do baseline UCP.
- Layout de handlers: o handler concreto vive em `schemas/handlers/`, não em
  uma árvore `source/handlers/` separada como no UCP.

## O que adicionamos (original do BCP)

Sem linhagem UCP (Copyright 2026 BCP Authors), tudo por `allOf` sobre os
recursos base, sem editar nenhum schema vendorado:

- `br.dev.bcp.shopping.fiscal_identity`: identificação fiscal do comprador e
  do vendedor no checkout e no pedido.
- `br.dev.bcp.shopping.tax`: detalhamento dos tributos por item, com
  comportamento no preço e nível federativo.
- `br.dev.bcp.shopping.nfe`: referência da nota fiscal eletrônica no pedido.
- `br.dev.bcp.shopping.returns`: devoluções e direito de arrependimento, com
  política declarável no perfil.
- `br.dev.bcp.pix`: payment handler de Pix Cobrança única (QR dinâmico,
  fluxo push).

## O que decidimos NÃO puxar do upstream

- Nada ainda; registrar por release UCP futura, com a razão.
