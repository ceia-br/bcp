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

<div align="center">

<img src="docs/assets/bcp-logo.svg" alt="Brazilian Commerce Protocol" width="96">

# Brazilian Commerce Protocol (BCP)

**A língua aberta do comércio agêntico brasileiro: Pix, nota fiscal,
identidade fiscal e tributos como cidadãos de primeira classe do protocolo.**

[Documentação](https://bcp.dev.br) ·
[Especificação](https://bcp.dev.br/latest/specification/overview/) ·
[Playground](https://bcp.dev.br/latest/playground/) ·
[English](https://bcp.dev.br/latest/en/) ·
[Discussões](https://github.com/ceia-br/bcp/discussions)

[![Licença](https://img.shields.io/badge/licen%C3%A7a-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-draft-orange.svg)](https://bcp.dev.br)
[![Forkado do UCP](https://img.shields.io/badge/forkado%20do-UCP-8A2BE2.svg)](https://ucp.dev)
[![Docs](https://img.shields.io/badge/docs-bcp.dev.br-00c07a.svg)](https://bcp.dev.br)

</div>

## O que é

O Brazilian Commerce Protocol (BCP) é um protocolo aberto para comércio
agêntico descentralizado no Brasil: a linguagem comum entre agentes de IA,
lojas e provedores de pagamento e de credencial, da descoberta ao checkout.

Hoje, a descoberta e a compra na internet passam por poucas plataformas de
intermediação, e a chegada dos agentes de IA tende a concentrar isso ainda
mais. O BCP aposta no caminho contrário: com um protocolo aberto, esses
participantes conversam diretamente, sem intermediário obrigatório.

O BCP é um fork do [Universal Commerce Protocol (UCP)](https://ucp.dev),
derivado da spec `2026-04-08` sob namespace próprio, `br.dev.bcp` (ver
[Atribuição](#atribuição)).

Este repositório é a fonte da verdade do protocolo: os JSON Schemas em
`schemas/` e `discovery/`, e a especificação em prosa publicada em
[bcp.dev.br](https://bcp.dev.br).

## Por que o BCP?

- A infraestrutura brasileira é nativa: o Pix é o pagador padrão do
  protocolo, e nota fiscal e identidade fiscal são conceitos de primeira
  classe, não adaptações por cima de um padrão estrangeiro.
- As obrigações do comércio brasileiro entram como extensões próprias,
  ancoradas na legislação, sem editar nenhum schema herdado do UCP.
- As empresas ficam no centro: vendedores continuam comerciantes
  responsáveis, donos da relação com o cliente.

## Como o BCP se organiza

O BCP parte do núcleo comercial do UCP (catálogo, carrinho, checkout,
pedido) e adiciona, por cima, uma camada de extensões brasileiras e o
payment handler de Pix.

## Extensões brasileiras

| Extensão          | O que adiciona                                                          |
| :---------------- | :---------------------------------------------------------------------- |
| `fiscal_identity` | Identificação fiscal do comprador e do vendedor no checkout e no pedido |
| `tax`             | Detalhamento dos tributos de cada item, na transparência que a lei exige |
| `nfe`             | Referência da nota fiscal eletrônica no pedido                          |
| `returns`         | Devoluções e direito de arrependimento, com prazos legais e logística reversa |

Cada uma tem spec em prosa em `docs/specification/` e registro no
[`CHANGELOG-divergencia.md`](CHANGELOG-divergencia.md). Além das extensões,
o protocolo traz o payment handler de Pix Cobrança (`br.dev.bcp.pix`).

## Principais características

- As capacidades (checkout, carrinho, catálogo, pedido, vínculo de
  identidade) são schemas base; toda extensão entra por `allOf`, sem inchar
  as definições que todo mundo implementa.
- Cada negócio publica um perfil de descoberta (`discovery/`) que os agentes
  leem para se configurar sozinhos.
- O protocolo é agnóstico de transporte: as mesmas capacidades funcionam via
  MCP, A2A ou protocolo embarcado.
- A base técnica é a mesma do UCP: JSON Schema draft 2020-12, reverse-domain
  naming, versionamento por data e compatibilidade com AP2.

## Começando

- Explore a [documentação](https://bcp.dev.br): visão geral, especificação
  completa e guias.
- Experimente o [Playground](https://bcp.dev.br/latest/playground/).
- Consuma os schemas versionados, servidos como arquivos estáticos junto da
  spec. Exemplo:
  [`/latest/schemas/shopping/checkout.json`](https://bcp.dev.br/latest/schemas/shopping/checkout.json).

## Contribuindo

- Dúvidas e propostas: use as
  [Discussões](https://github.com/ceia-br/bcp/discussions).
- Bugs e melhorias: abra uma issue neste repositório.
- Fluxo de PR, commits, convenções de schema e código de conduta: veja o
  [CONTRIBUTING.md](CONTRIBUTING.md).
- Maintainers: veja o [MAINTAINERS.md](MAINTAINERS.md).

### Desenvolvimento de schemas

Os schemas vivem em `schemas/` e são publicados com as anotações `ucp_*`
intactas. Agentes podem resolvê-las em runtime com o CLI
[ucp-schema](https://github.com/universal-commerce-protocol/ucp-schema), que
aceita o namespace `br.dev.bcp` sem fork.

1. Instale as dependências: `make install`

2. Edite os JSON em `schemas/` seguindo as convenções do
   [CONTRIBUTING.md](CONTRIBUTING.md).

3. Valide schemas, fixtures e snapshots do playground (offline, sem
   toolchain externa; se o `ucp-schema` estiver instalado, o `lint` dele
   roda junto):

   ```bash
   make check
   ```

### Desenvolvimento da documentação

O projeto usa [uv](https://docs.astral.sh/uv/) para as dependências Python.

1. Instale as dependências: `make install`
2. Instale o `ucp-schema` (`cargo install ucp-schema`); as macros de schema
   da página de referência dependem dele.
3. Rode o servidor de desenvolvimento (versão pt-BR, com live reload):

   ```bash
   uv run --group docs mkdocs serve
   ```

4. Antes de submeter, monte o site completo (pt-BR, en e schemas
   versionados, o mesmo build de produção) e confira os warnings:

   ```bash
   make docs-build
   ```

   `make docs-serve` sobe um preview do site completo em
   <http://127.0.0.1:8000>.

## Atribuição

O BCP deriva do
[Universal Commerce Protocol](https://github.com/Universal-Commerce-Protocol/ucp),
Copyright 2026 UCP Authors, licenciado sob a Apache License 2.0. No material
derivado, o namespace `dev.ucp.*` foi renomeado para `br.dev.bcp.*` e as URLs
de schema resolvem em `bcp.dev.br`. A estrutura dos schemas permanece
idêntica à do UCP, o que deixa aberta uma ponte futura entre os dois
protocolos; a sincronização com o upstream acontece quando for da vontade do
BCP.

A atribuição formal está em [`NOTICE`](NOTICE), e cada divergência é
registrada em [`CHANGELOG-divergencia.md`](CHANGELOG-divergencia.md).

## O que vem a seguir

Veja o [roadmap em bcp.dev.br](https://bcp.dev.br/latest/roadmap/).

## Sobre

O BCP é um projeto open-source sob a [Apache License 2.0](LICENSE), aberto a
contribuições da comunidade.
