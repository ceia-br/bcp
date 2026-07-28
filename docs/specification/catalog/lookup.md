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

# Capacidade de consulta de catálogo

* **Nome do recurso:** `br.dev.bcp.shopping.catalog.lookup`

Recupera produtos ou variantes por identificador. Use isso quando você já tiver
identificadores (por exemplo, de uma lista salva, links diretos, validação de carrinho ou um selecionado
produto para renderização de detalhes).

## Operações

| Operação | Ferramenta / Ponto final | Descrição |
| :--- | :--- | :--- |
| **Pesquisa em lote** | `lookup_catalog` / `POST /catalog/lookup` | Recuperar vários produtos por identificador. |
| **Obter produto** | `get_product` / `POST /catalog/product` | Recuperar todos os detalhes de um único produto. |

`lookup_catalog` resolve identificadores para produtos; `get_product` busca
detalhes completos de um produto conhecido ou ID de variante:

| Preocupação | `lookup_catalog` | `get_product` |
| :--- | :--- | :--- |
| **Entrada** | `ids[]` — ID do produto/variante; PODE suportar SKU, identificador, URL, etc. | `id` — ID do produto ou variante |
| **Objetivo** | Resolver identificadores para produtos | Detalhes completos do produto para decisões de compra com seleção de opções interativas |
| **Variantes** | Uma variante em destaque por produto | Variante em destaque e subconjunto relevante, filtrado por seleções de opções |

Use `lookup_catalog` quando tiver identificadores para resolver ou exibir em uma lista.
Use `get_product` quando um produto for identificado e o agente precisar
detalhes, incluindo seleção interativa de variantes, para uma decisão de compra.

---

## Pesquisa em lote (`lookup_catalog`)

### Identificadores Suportados

O parâmetro `ids` aceita um array de identificadores. As implementações DEVEM apoiar
pesquisa por ID do produto e ID da variante. As implementações PODEM apoiar adicionalmente
identificadores secundários, como SKU ou identificador, desde que também sejam campos em
o objeto do produto retornado.

Identificadores duplicados na solicitação DEVEM ser desduplicados. Quando um identificador
corresponde a vários produtos (por exemplo, um SKU compartilhado entre variantes), as implementações
DEVEM retornar os produtos correspondentes e PODEM limitar o conjunto de resultados. Quando vários
identificadores resolverem para o mesmo produto, ele DEVE ser devolvido uma vez.

### Correlação do cliente

A resposta não garante a ordem. Cada variante carrega um `inputs`
matriz identificando quais identificadores de solicitação foram resolvidos e como.

{{ schema_fields('types/input_correlation', 'catalog') }}

Vários identificadores de solicitação podem resolver para a mesma variante (por exemplo, um
ID do produto e um de seus IDs de variante). Quando isso ocorre, o array `inputs` da variante
contém uma entrada por identificador resolvido, cada uma com seu
próprio tipo de correspondência. Variantes sem entrada `inputs` NÃO DEVEM aparecer em
respostas de pesquisa.

### Tamanho do lote

As implementações DEVEM aceitar pelo menos 10 identificadores por solicitação. As implementações
PODEM impor um tamanho máximo de lote e DEVEM rejeitar solicitações que excedam esse limite
com um erro apropriado (HTTP 400 `request_too_large` para REST, JSON-RPC
`-32602` para MCP).

### Comportamento de resolução

`match` reflete o nível de resolução do identificador, não o seu tipo:

* **`exact`**: Identificador resolvido diretamente para esta variante
  (por exemplo, ID da variante, SKU, código de barras).
* **`featured`**: Identificador resolvido para o produto pai; servidor
  selecionou esta variante como representativa (por exemplo, ID do produto, identificador).

### Filtros

Tanto `lookup_catalog` quanto `get_product` aceitam `filters` opcional para
restringir os produtos e variantes devolvidos. Os filtros usam o mesmo esquema
e a mesma semântica AND que os [Filtros de pesquisa](search.md#filtros-de-pesquisa) — por
exemplo, um filtro de preço exclui variantes fora do intervalo especificado.

Os filtros são aplicados *após* a resolução do identificador (`lookup_catalog`) ou a seleção
de opções (`get_product`). Um identificador que resolve um produto cujas variantes
todas ficarem fora do filtro de preço resulta na exclusão desse produto
da resposta.

### Solicitação

{{ extension_schema_fields('catalog_lookup.json#/$defs/lookup_request', 'catalog') }}

### Resposta

{{ extension_schema_fields('catalog_lookup.json#/$defs/lookup_response', 'catalog') }}

---

## Obter produto (`get_product`)

Recupera o estado atual do produto para um único identificador, com suporte para
seleção interativa de variantes e sinais de disponibilidade em tempo real. Este é o
fonte confiável para decisões de compra.

### Identificadores Suportados

O parâmetro `id` aceita um único ID de produto ou ID de variante.

### Comportamento de resolução

A resposta retorna o produto com contexto completo (título, descrição,
mídia, opções) e um **subconjunto de variantes correspondentes
[`product.selected`](#selecao-de-opcoes)**:

* **ID do produto**: `variants` DEVE conter a variante em destaque e outras
  variantes correspondentes a `product.selected`. Quando a solicitação inclui `selected`
  opções, isso restringe o subconjunto a variantes que correspondam às escolhas do cliente.
* **ID da variante**: A variante solicitada DEVE ser o primeiro elemento (destaque).
  `product.selected` reflete as opções dessa variante. Variantes restantes
  corresponder às mesmas seleções efetivas. Quando a solicitação inclui `selected`
  opções que entram em conflito com as próprias opções da variante, as opções da variante
  as opções têm precedência – o ID da variante determina totalmente a seleção
  estado e `selected` é ignorado.

### Forma de resposta

A resposta contém um objeto `product` singular (não uma matriz). Isso reflete
a semântica de recurso único da operação. Quando o identificador não é encontrado,
o servidor retorna `ucp.status: "error"` com um array `messages` contendo
o detalhe do erro. Este é um resultado de aplicação — o manipulador foi executado e reportou
seu resultado através do envelope BCP, não um erro de transporte.

### Seleção de opções

Os parâmetros `selected` e `preferences` permitem o estreitamento interativo de variantes:
a interação principal da página de detalhes do produto, onde um usuário seleciona opções progressivamente
(Cor, Tamanho, etc.) e a interface atualiza a disponibilidade em tempo real.

#### Entrada

* **`selected`**: Matriz de seleções de opções (por exemplo, `[{"name": "Color", "label": "Red"}]`).
  As seleções parciais são válidas; o cliente envia tudo o que o usuário escolheu até agora.
  Cada nome de opção DEVE aparecer no máximo uma vez.
* **`preferences`**: Nomes de opções em ordem de prioridade de relaxamento (por exemplo,
  `["Color", "Size"]`). Quando nenhuma variante corresponde a todas as seleções, o servidor descarta
  opções do **final** desta lista primeiro, mantendo as seleções de maior prioridade
  intacto. Opcional; se omitido, o servidor usa sua própria heurística de relaxamento.

#### Saída: Seleções Efetivas

A resposta DEVE incluir `product.selected` quando o produto tiver
opções configuráveis — refletindo as seleções efetivas após qualquer
relaxamento, quando a solicitação incluir `selected`, ou as seleções padrão da
variante em destaque, caso contrário. Quando o produto não possui
opções configuráveis, `selected` PODE estar vazio ou omitido.

Clientes que enviam `selected` detectam relaxamento diferenciando sua solicitação
contra `product.selected`:

* **Sem relaxamento**: A resposta `selected` corresponde à solicitação — todas
  seleções resolvidas para pelo menos uma variante.
* **Ocorreu relaxamento**: A resposta `selected` é um subconjunto do
  solicitação - o servidor eliminou opções não resolvíveis por `preferences`
  prioridade.

#### Saída: Sinais de Disponibilidade

Os valores das opções na resposta DEVEM incluir sinais de disponibilidade
em relação a `product.selected`:

| `available` | `exists` | Significado | Tratamento de IU |
| :--- | :--- | :--- | :--- |
| `true` | `true` | Em estoque — comprável | Selecionável |
| `false` | `true` | Esgotado – variante existe, mas não está disponível | Desativado/tachado |
| `false` | `false` | Nenhuma variante para esta combinação | Oculto ou visualmente distinto |

Esses campos aparecem em cada valor de opção em `product.options[].values[]`. Eles
refletem a disponibilidade **em relação às seleções efetivas**. Mudando um
seleção altera o mapa de disponibilidade.

### Solicitação

{{ extension_schema_fields('catalog_lookup.json#/$defs/get_product_request', 'catalog') }}

### Resposta

{{ extension_schema_fields('catalog_lookup.json#/$defs/get_product_response', 'catalog') }}

---

## Ligações de transporte

* REST Binding: não publicado nesta versão do BCP.
* [MCP Binding](mcp.md#lookup_catalog): ferramenta `lookup_catalog` (lote)
* [MCP Binding](mcp.md#get_product): ferramenta `get_product` (única)
