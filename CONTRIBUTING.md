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

# Como contribuir

Adoraríamos receber suas correções e contribuições para o protocolo.

## Antes de começar

Leia o [código de conduta](CODE_OF_CONDUCT.md); ele vale para todos os
espaços do projeto.

Achou um bug, um erro na documentação ou sente falta de algo? Abra uma issue.
É assim que rastreamos os problemas. Para bug em schema, inclua o schema ou o
fixture afetado e o que você esperava que acontecesse. Para puxar uma
conversa, compartilhar uma ideia ou tirar uma dúvida, use as
[Discussões](https://github.com/Brazilian-Commerce-Protocol/bcp/discussions).

## Processo de contribuição

### Mudanças significativas

Uma mudança no protocolo obriga todo o ecossistema que o adota a acompanhar,
então mudanças significativas começam por uma discussão, antes de qualquer
PR. Consideramos significativas:

- modificações nos JSON Schemas, incluindo campos novos e mudanças de
  descrição;
- alterações nos fluxos de comunicação ou no comportamento esperado das
  operações;
- capacidades ou serviços inteiramente novos;
- qualquer quebra de compatibilidade.

A aprovação é dos [maintainers](MAINTAINERS.md).

### Extensões primeiro

O BCP mantém o núcleo do protocolo enxuto, o mesmo princípio do UCP. Um caso
de uso novo começa como extensão em namespace próprio de quem o propõe
(`com.{vendor}.*`) e só entra no núcleo quando tiver adoção comprovada.

### Versionamento

O protocolo usa versionamento por data (`YYYY-MM-DD`). Quebra de
compatibilidade tem custo alto para quem já implementou; antes de propor uma,
verifique se uma extensão não resolve.

### Revisão de código

Toda submissão passa por revisão, inclusive as dos próprios maintainers.
Usamos
[pull requests do GitHub](https://docs.github.com/articles/about-pull-requests).

### Títulos de PR e mensagens de commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/), em
inglês, no formato `type: description`. Se a mudança quebra compatibilidade
(remover um campo de schema, por exemplo), adicione `!` antes dos
dois-pontos: `type!: description`.

Tipos comuns: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`chore`.

O header tem no máximo 50 caracteres; o corpo vai em lista, com itens de até
100 caracteres explicando o porquê da mudança.

Exemplos:

- `feat: add new payment handler`
- `fix: resolve invalid ref in checkout schema`
- `docs: update setup guide`
- `feat!: remove deprecated buyer field from checkout`

### Submetendo um pull request

1. Faça fork do repositório e crie sua branch a partir de `main`.
2. Faça as mudanças seguindo o setup abaixo.
3. Rode `make validate` e `make docs-build` e confirme que passam.
4. Confira se o título do PR segue o formato de Conventional Commits.
5. Abra o PR descrevendo a motivação e a mudança; referencie a issue ou a
   discussão de origem.
6. Responda aos apontamentos da revisão.

## Setup de desenvolvimento local

### Schemas

Os schemas vivem em `schemas/` e são publicados com as anotações `ucp_*`
intactas. Agentes podem resolvê-las em runtime com o CLI
[ucp-schema](https://github.com/universal-commerce-protocol/ucp-schema), que
aceita o namespace `br.dev.bcp` sem fork.

1. Garanta o `ucp-schema` instalado:

   ```bash
   cargo install ucp-schema
   ```

2. Edite os JSON em `schemas/` seguindo as convenções abaixo.
3. Valide (lint de todos os schemas e fixtures de ponta a ponta):

   ```bash
   make validate
   ```

O `validate` usa o mapeamento `--schema-local-base` para resolver as URLs
`bcp.dev.br` nos arquivos locais, então funciona offline.

Se você adicionar ou mudar um recurso, inclua fixtures: payloads que devem
passar em `fixtures/valid/` e payloads que devem falhar em
`fixtures/invalid/`. São eles que protegem o protocolo contra regressão.

### Documentação

O projeto usa [uv](https://docs.astral.sh/uv/) para as dependências Python.

1. Instale as dependências: `make install`
2. Garanta o `ucp-schema` instalado (ver acima; o build da página de
   referência o usa).
3. Rode o servidor de desenvolvimento (versão pt-BR, com live reload):

   ```bash
   uv run --group docs mkdocs serve
   ```

4. Antes de submeter, monte o site completo (pt-BR, en e schemas
   versionados, o mesmo build de produção) e confira os warnings:

   ```bash
   make docs-build
   ```

## Estrutura do repositório

```
schemas/
├── ucp.json              # metadados do protocolo: entity, base, version, envelopes de resposta
├── capability.json       # declaração de capability
├── service.json          # definição de serviço
├── payment_handler.json  # template de payment handler
├── shopping/             # o DOMÍNIO de comércio (os recursos de topo)
│   ├── cart.json  checkout.json  order.json  payment.json
│   ├── catalog_lookup.json  catalog_search.json
│   ├── discount.json  ap2_mandate.json  buyer_consent.json  fulfillment.json  # extensões (UCP)
│   ├── fiscal_identity.json  tax.json  nfe.json  returns.json  # extensões BRASILEIRAS (originais)
│   └── types/            # VALUE OBJECTS reusáveis: amount, buyer, line_item, totals, ...
├── common/               # schemas compartilhados entre domínios (identity_linking)
├── handlers/             # payment handlers concretos (pix)
└── transports/           # bindings de transporte (embedded_config)
discovery/
└── profile_schema.json   # documento de /.well-known (perfil do agente)
docs/ e docs-en/          # spec em prosa (mkdocs, pt-BR e en)
fixtures/                 # payloads de exemplo: valid/ passam, invalid/ falham
scripts/validate.sh       # lint + validação dos fixtures com o ucp-schema
```

Por que a divisão raiz vs pasta:

- a raiz de `schemas/` é o nível de protocolo/meta, que vale para tudo:
  `ucp.json` (o vocabulário de metadados; mantém o nome `ucp` de propósito,
  ver abaixo), `capability.json`, `service.json`, `payment_handler.json`;
- `shopping/` é um domínio (comércio) com os recursos de topo: cart,
  checkout, order, payment, catálogo;
- `shopping/types/` são os value objects: peças pequenas e reusáveis que os
  recursos referenciam (amount, buyer, line_item, postal_address, totals),
  separadas dos recursos para distinguir "coisa que trafega inteira" de
  "peça reusada";
- `common/` é o compartilhado entre domínios; `transports/` liga o protocolo
  a cada transporte; `discovery/` é o perfil de well-known.

## Convenções de autoria

- Reverse-domain naming: cada capability tem `name` no formato
  `br.dev.bcp.shopping.discount`. É o que separa recurso base de extensão.
- Extensão por `extends`/`allOf`: um schema de extensão (ex. `discount.json`)
  faz `allOf` sobre um recurso base (cart, checkout) e declara sua capability
  reverse-domain. Na geração de modelos, isso vira subclasse do recurso base.
- Variantes de request (`ucp_request`): campos anotados com `ucp_request`
  (omit/optional/required por operação) fazem o pipeline gerar schemas
  derivados `*_create_request.json`, `*_update_request.json` etc. Eles não
  ficam commitados aqui; são materializados no pipeline de geração de
  modelos.
- `$id`/`$ref`: `$id` absoluto em `bcp.dev.br`; `$ref` entre arquivos é
  relativo (ex. `types/amount.json`, `../ucp.json`).
- Não edite schema vendorado do UCP: toda diferença brasileira entra como
  extensão nova.
- Schema no fonte não carrega `version` no objeto raiz: a versão é injetada
  no build do site, e o `make validate` rejeita versão literal.

### Extensões brasileiras novas

Uma extensão brasileira nova (como `fiscal_identity`, `tax`, `nfe` e
`returns`) precisa de quatro coisas:

1. o schema em `schemas/shopping/` (e config em `schemas/shopping/types/`,
   se houver);
2. a spec em prosa em `docs/specification/`;
3. o registro no [`CHANGELOG-divergencia.md`](CHANGELOG-divergencia.md);
4. fixtures válidos e inválidos.

## Fork: o que renomeamos

`dev.ucp.*` virou `br.dev.bcp.*` e `ucp.dev` virou `bcp.dev.br` (em `name`,
`$id`, `$ref`). Mantidos de propósito: o arquivo `ucp.json`, o campo de
envelope `ucp` e a keyword `ucp_request` (renomear forkaria o
`preprocess_schemas.py`/validador sem ganho). Baseline e detalhe em
[`CHANGELOG-divergencia.md`](CHANGELOG-divergencia.md).

Não vendorados ainda (faseamento): `services/` (OpenAPI/OpenRPC).

## Licença

Ao contribuir, você concorda que sua contribuição será licenciada sob a
[Apache License 2.0](LICENSE), como o restante do projeto. Trechos derivados
do UCP mantêm a atribuição exigida, registrada em [`NOTICE`](NOTICE).
