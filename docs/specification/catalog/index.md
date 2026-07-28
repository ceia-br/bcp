<!--
   Copyright 2026 UCP Authors

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

<!--
   BCP adaptation: this documentation page is derived from UCP documentation,
   renamed to the br.dev.bcp namespace and adjusted for the Brazilian Commerce
   Protocol fork. See NOTICE and CHANGELOG-divergencia.md.
-->

# Capacidade de catálogo

## Visão geral

O recurso Catálogo permite que as plataformas pesquisem e naveguem em catálogos de produtos comerciais.
Isso permite a descoberta do produto antes da finalização da compra, suportando casos de uso como:

* Pesquisa de produtos em texto livre
* Categoria e navegação baseada em filtros
* Recuperação de produto/variante em lote por identificador
* Comparação de preços entre variantes

## Capacidades

| Capacidade | Descrição |
| :--- | :--- |
| [`br.dev.bcp.shopping.catalog.search`](search.md) | Pesquise produtos usando texto de consulta e filtros. |
| [`br.dev.bcp.shopping.catalog.lookup`](lookup.md) | Recuperar produtos ou variantes por identificador. |

## Conceitos-chave

* **Produto**: um item de catálogo com título, descrição, mídia e um ou mais
  variantes.
* **Variante**: um item comprável com seleções de opções específicas (por exemplo, "Azul /
  Grande"), preço e disponibilidade.
* **Preço**: os valores de preço incluem o valor (em unidades monetárias menores) e
  código de moeda, permitindo catálogos em várias moedas.

### Relacionamento com Checkout

As operações de catálogo retornam IDs de produtos e variantes que podem ser usados diretamente no
checkout, em `line_items[].item.id`. O ID da variante retornado pelo catálogo deve corresponder
ao ID do item esperado pela finalização da compra.

As respostas do catálogo (preço, disponibilidade, etc.) refletem os termos atuais do negócio
para a solicitação fornecida, mas não são compromissos transacionais — o checkout
é a fonte da verdade. As respostas podem ser específicas da sessão e **NÃO DEVEM** ser
reutilizadas em sessões sem revalidação.

## Entidades Compartilhadas

### Contexto

Localização e contexto de mercado para operações de catálogo. Todos os campos são dicas opcionais
de relevância e localização. As plataformas PODEM detectar o contexto geograficamente a partir dos
cabeçalhos da solicitação.

Os sinais de contexto são dados provisórios e não oficiais. As empresas DEVEM usar
esses valores quando as entradas verificadas (por exemplo, endereço de entrega) estiverem ausentes e PODEM
ignorá-los ou rebaixá-los quando forem inconsistentes com sinais de maior confiança
(conta autenticada, detecção de risco) ou com restrições regulatórias (controles de
exportação). A elegibilidade e a aplicação da política DEVEM ocorrer no momento da finalização da compra, usando
dados vinculantes da transação.

As empresas determinam a atribuição de mercado – incluindo a moeda – com base nos sinais de
contexto. Os valores do filtro de preços são denominados em `context.currency`; quando
a moeda de apresentação é diferente, as empresas DEVEM converter antes de aplicar
(veja [Filtro de Preço](search.md#filtro-de-preco)). Os preços de resposta incluem
códigos de moeda explícitos que confirmam a resolução.

Quando as reivindicações `context.eligibility` estão presentes, as empresas que as aceitam
**PODEM** ajustar `price` / `list_price` diretamente para exibição tachada e
**PODEM** usar `messages` com `code: "eligibility_benefit"` para atribuir o
ajuste a uma reivindicação específica.

{{ schema_fields('types/context', 'catalog') }}

### Sinais

Dados ambientais fornecidos pela plataforma para apoiar a autorização
e prevenção de abusos. Os valores do sinal NÃO DEVEM ser reivindicações afirmadas pelo comprador. Veja
[Sinais](../overview.md#sinais) para detalhes e requisitos de privacidade.

{{ schema_fields('types/signals', 'catalog') }}

### Atribuição

Contexto de referência e evento de conversão fornecido pela plataforma – IDs de campanha,
identificadores de clique e marcadores de origem/mídia comunicados pela plataforma.
Consulte [Atribuição](../overview.md#atribuicao) para obter detalhes e consentimento
requisitos.

{{ schema_fields('types/attribution', 'catalog') }}

### Produto

Um item de catálogo que representa um item vendável com uma ou mais variantes compráveis.

`media` e `variants` são arrays ordenados. As empresas DEVEM retornar primeiro a
variante e a imagem mais relevantes – ordem padrão para consultas de lookup, melhor correspondência
com base na consulta e no contexto para pesquisas (search). As plataformas DEVEM tratar o primeiro
elemento como destaque.

{{ schema_fields('types/product', 'catalog') }}

### Variante

Um item comprável com seleções de opções específicas, preço e disponibilidade.

Nas respostas de pesquisa, cada variante carrega um array `inputs` para correlação:
quais identificadores de solicitação foram resolvidos para esta variante e se a correspondência
era `exact` ou `featured` (selecionado pelo servidor). Veja
[Correlação do cliente](lookup.md#correlacao-do-cliente) para obter detalhes.

`media` é uma matriz ordenada. As empresas DEVEM retornar a imagem da variante em destaque
como o primeiro elemento. As plataformas DEVEM tratar o primeiro elemento como destaque.

{{ schema_fields('types/variant', 'catalog') }}

### Preço

{{ schema_fields('types/price', 'catalog') }}

### Faixa de preço

{{ schema_fields('types/price_range', 'catalog') }}

### Mídia

{{ schema_fields('types/media', 'catalog') }}

### Opção de produto

{{ schema_fields('types/product_option', 'catalog') }}

### Valor da opção

{{ schema_fields('types/option_value', 'catalog') }}

### Opção selecionada

{{ schema_fields('types/selected_option', 'catalog') }}

### Avaliação

{{ schema_fields('types/rating', 'catalog') }}

## Mensagens e tratamento de erros

Todas as respostas do catálogo incluem um array `messages` opcional que permite às empresas
fornecer contexto sobre erros, avisos ou mensagens informativas.

### Tipos de mensagens

As mensagens comunicam os resultados do negócio e fornecem contexto:

| Tipo | Quando usar | Códigos de exemplo |
| :--- | :--- | :--- |
| `error` | Erros em nível de negócio | `NOT_FOUND`, `OUT_OF_STOCK`, `REGION_RESTRICTED` |
| `warning` | Condições importantes que afetam a compra | `DELAYED_FULFILLMENT`, `FINAL_SALE` |
| `info` | Contexto adicional sem problemas | `PROMOTIONAL_PRICING`, `LIMITED_AVAILABILITY` |

Os avisos com `presentation: "disclosure"` trazem alertas (por exemplo, declarações
de alérgenos, avisos de segurança) que as plataformas NÃO DEVEM ocultar ou ignorar. Veja
[Apresentação de aviso](../checkout.md#apresentacao-de-aviso) para o contrato completo de
apresentação.

**Observação**: A maioria dos erros de catálogo usa `severity: "recoverable"` — os agentes
devem tratá-los programaticamente (tentar novamente, informar o usuário, mostrar alternativas).
`get_product` retorna `severity: "unrecoverable"` quando um identificador
não resolve; os agentes NÃO DEVEM tentar novamente o mesmo `id`. Veja o
exemplo em [MCP](mcp.md#produto-nao-encontrado). Os documentos do serviço REST não são publicados
nesta versão do BCP.

#### Mensagem (Erro)

{{ schema_fields('types/message_error', 'catalog') }}

#### Mensagem (Aviso)

{{ schema_fields('types/message_warning', 'catalog') }}

#### Mensagem (Informações)

{{ schema_fields('types/message_info', 'catalog') }}

### Cenários Comuns

#### Pesquisa vazia

Quando a pesquisa não encontrar correspondências, retorne um array vazio sem mensagens.

<!-- ucp:example schema=shopping/catalog_search op=search -->
```json
{
  "ucp": {...},
  "products": []
}
```

Isto não é um erro – a consulta era válida, mas não retornou resultados.

#### Aviso de pedido pendente

Quando um produto estiver disponível, mas tiver atraso no atendimento, devolva o produto com
uma mensagem de aviso. Use o campo `path` para segmentar variantes específicas.

<!-- ucp:example schema=shopping/catalog_search op=search -->
```json
{
  "ucp": {...},
  "products": [
    {
      "id": "prod_xyz789",
      "title": "Professional Chef Knife Set",
      "description": { "plain": "Complete professional knife collection." },
      "price_range": {
        "min": { "amount": 29900, "currency": "BRL" },
        "max": { "amount": 29900, "currency": "BRL" }
      },
      "variants": [
        {
          "id": "var_abc",
          "title": "12-piece Set",
          "description": { "plain": "Complete professional knife collection." },
          "price": { "amount": 29900, "currency": "BRL" },
          "availability": { "available": true }
        }
      ]
    }
  ],
  "messages": [
    {
      "type": "warning",
      "code": "delayed_fulfillment",
      "path": "$.products[0].variants[0]",
      "content": "12-piece set on backorder, ships in 2-3 weeks"
    }
  ]
}
```

Os agentes podem apresentar a opção e informar o usuário sobre o atraso. O `path`
campo usa RFC 9535 JSONPath para direcionar componentes específicos.

#### Identificadores não encontrados

Quando os identificadores solicitados não existirem, retorne sucesso com os produtos encontrados
(se houver). A resposta PODE incluir mensagens informativas indicando quais
identificadores não foram encontrados.

<!-- ucp:example schema=shopping/catalog_lookup op=lookup -->
```json
{
  "ucp": {...},
  "products": [],
  "messages": [
    {
      "type": "info",
      "code": "not_found",
      "content": "prod_invalid"
    }
  ]
}
```

Os agentes correlacionam os resultados usando a matriz `inputs` em cada variante. Veja
[Correlação do cliente](lookup.md#correlacao-do-cliente).

#### Divulgação do Produto

Quando um produto exige uma divulgação (por exemplo, aviso sobre alérgenos, aviso de segurança),
retorne-o como aviso com `presentation: "disclosure"`. O campo `path` tem como alvo o
componente relevante na resposta – quando se destina a um produto, o
a divulgação se aplica a todas as suas variantes.

<!-- ucp:example schema=shopping/catalog_search op=search -->
```json
{
  "ucp": {...},
  "products": [
    {
      "id": "prod_nut_butter",
      "title": "Artisan Nut Butter Collection",
      "description": { "plain": "Assorted artisan nut butters." },
      "price_range": {
        "min": { "amount": 1299, "currency": "BRL" },
        "max": { "amount": 1499, "currency": "BRL" }
      },
      "variants": [
        {
          "id": "var_almond",
          "title": "Almond Butter",
          "description": { "plain": "Smooth almond butter." },
          "price": { "amount": 1299, "currency": "BRL" },
          "availability": { "available": true }
        },
        {
          "id": "var_cashew",
          "title": "Cashew Butter",
          "description": { "plain": "Creamy cashew butter." },
          "price": { "amount": 1499, "currency": "BRL" },
          "availability": { "available": true }
        }
      ]
    }
  ],
  "messages": [
    {
      "type": "warning",
      "code": "allergens",
      "path": "$.products[0]",
      "content": "**Contains: tree nuts.** Produced in a facility that also processes peanuts, milk, and soy.",
      "content_type": "markdown",
      "presentation": "disclosure",
      "image_url": "https://merchant.com/allergen-tree-nuts.svg",
      "url": "https://merchant.com/allergen-info"
    }
  ]
}
```

Consulte [Apresentação de aviso](../checkout.md#apresentacao-de-aviso) para obter informações
contrato de prestação integral.

## Escopos

Os recursos Pesquisa de Catálogo e Pesquisa de Catálogo definem o seguinte
escopos bem conhecidos para acesso autenticado pelo usuário:

| Escopo | Descrição |
| :--- | :--- |
| `br.dev.bcp.shopping.catalog.search:read` | Pesquise em nome do usuário autenticado – resultados personalizados, preços para membros, inventário fechado. |
| `br.dev.bcp.shopping.catalog.lookup:read` | Pesquisa em nome do usuário autenticado – preços personalizados ou disponibilidade para produtos específicos. |

Declaração de escopo, derivação e regras para estender este conjunto com
escopos personalizados são definidos em [Vinculação de identidade — Escopos](../identity-linking.md#escopos).

## Ligações de transporte

Os recursos acima estão vinculados a protocolos de transporte específicos:

* REST Binding: não publicado nesta versão do BCP.
* [MCP Binding](mcp.md): mapeamento do protocolo de contexto do modelo via JSON-RPC.
