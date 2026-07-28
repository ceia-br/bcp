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

# Capacidade de pesquisa de catálogo

* **Nome do recurso:** `br.dev.bcp.shopping.catalog.search`

Executa uma pesquisa no catálogo de produtos da empresa. Suporta texto livre
consultas, filtragem por categoria e preço e paginação.

## Operação

| Operação | Descrição |
| :--- | :--- |
| **Pesquisar Catálogo** | Pesquise produtos usando entradas e filtros fornecidos. |

### Solicitação

{{ extension_schema_fields('catalog_search.json#/$defs/search_request', 'catalog') }}

### Resposta

{{ extension_schema_fields('catalog_search.json#/$defs/search_response', 'catalog') }}

## Entradas de pesquisa

Uma solicitação de pesquisa válida DEVE incluir pelo menos um dos seguintes: uma string `query`,
um ou mais `filters`, ou uma entrada definida por extensão. Quando `query` é
omitido, a solicitação representa uma operação de navegação — o negócio retorna
produtos que correspondem aos filtros fornecidos sem classificação de relevância de texto.
As extensões PODEM definir entradas adicionais (por exemplo, similaridade visual,
referências do produto).

As implementações DEVEM validar se as solicitações recebidas contêm pelo menos um
entrada reconhecida e DEVE rejeitar solicitações vazias ou inválidas com um
erro apropriado. As implementações definem e aplicam suas próprias regras para
presença e conteúdo de entrada - por exemplo, exigindo `query`, rejeitando
strings `query` vazias ou aceitar solicitações somente de filtro para navegação por categoria.

## Filtros de pesquisa

Filtre critérios para restringir os resultados da pesquisa. Os filtros padrão são definidos abaixo;
os comerciantes PODEM oferecer suporte a filtros personalizados adicionais via `additionalProperties`.

{{ schema_fields('types/search_filters', 'catalog') }}

### Filtro de Preço

{{ schema_fields('types/price_filter', 'catalog') }}

## Paginação

Paginação baseada em cursor para operações de lista. Cursores são strings opacas
que as implementações PODEM ser codificadas como tokens de conjunto de chaves sem estado.

### Tamanho da página

O parâmetro `limit` é um tamanho de página solicitado, não uma contagem garantida.
As implementações DEVEM aceitar um tamanho de página de pelo menos 10. Quando o
limite solicitado excede o máximo da implementação, implementações
PODEM atingir o máximo silenciosamente - retornando menos resultados sem
erro. Os clientes NÃO DEVEM assumir que o tamanho da resposta é igual ao limite solicitado.

### Solicitação de paginação

{{ extension_schema_fields('types/pagination.json#/$defs/request', 'catalog') }}

### Resposta de paginação

{{ extension_schema_fields('types/pagination.json#/$defs/response', 'catalog') }}

## Ligações de transporte

* REST Binding: não publicado nesta versão do BCP.
* [Vinculação MCP](mcp.md#search_catalog): ferramenta `search_catalog`
