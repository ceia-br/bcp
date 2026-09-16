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

# Catálogo - vinculação MCP

Este documento especifica a ligação do Model Context Protocol (MCP) para o
[Capacidade de catálogo](index.md).

## Fundamentos do Protocolo

### Descoberta

As empresas anunciam a disponibilidade de transporte MCP através do seu perfil BCP em
`/.well-known/bcp`.

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {
      "br.dev.bcp.shopping": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "mcp",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/mcp.openrpc.json",
          "endpoint": "https://business.example.com/bcp/mcp"
        }
      ]
    },
    "capabilities": {
      "br.dev.bcp.shopping.catalog.search": [{
        "version": "{{ bcp_schema_version }}",
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/catalog/search",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/catalog_search.json"
      }],
      "br.dev.bcp.shopping.catalog.lookup": [{
        "version": "{{ bcp_schema_version }}",
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/catalog/lookup",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/catalog_lookup.json"
      }]
    },
    "payment_handlers": {}
  }
}
```

### Solicitar metadados

Os clientes MCP **DEVEM** incluir um objeto `meta` em cada solicitação contendo
metadados do protocolo:

<!-- ucp:example schema=shopping/catalog_search op=search direction=request extract=$.params.arguments.catalog -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "search_catalog",
    "arguments": {
      "meta": {
        "ucp-agent": {
          "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
        }
      },
      "catalog": {
        "query": "blue running shoes",
        "context": {
          "address_country": "BR",
          "intent": "looking for comfortable everyday shoes"
        }
      }
    }
  }
}
```

O campo `meta["ucp-agent"]` é **obrigatório** em todas as solicitações para habilitar
verificação de compatibilidade de versão e negociação de capacidade.

## Ferramentas

| Ferramenta | Capacidade | Descrição |
| :--- | :--- | :--- |
| `search_catalog` | [Pesquisar](search.md) | Pesquise produtos. |
| `lookup_catalog` | [Consulta](lookup.md) | Consulte um ou mais produtos ou variantes por identificador. |
| `get_product` | [Consulta](lookup.md#obter-produto-get_product) | Obtenha detalhes completos do produto por identificador. |

### `search_catalog`

Mapeia para o recurso [Pesquisa de catálogo](search.md).

#### Solicitação de pesquisa

{{ extension_schema_fields(
  'catalog_search.json#/$defs/search_request', 'catalog/mcp'
) }}

### Resposta de pesquisa

{{ extension_schema_fields(
  'catalog_search.json#/$defs/search_response', 'catalog/mcp'
) }}

#### Exemplo de pesquisa

=== "Solicitação"

    <!-- ucp:example schema=shopping/catalog_search op=search direction=request extract=$.params.arguments.catalog -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/call",
      "params": {
        "name": "search_catalog",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "catalog": {
            "query": "blue running shoes",
            "context": {
              "address_country": "BR",
              "address_region": "SP",
              "intent": "looking for comfortable everyday shoes"
            },
            "filters": {
              "categories": ["Footwear"],
              "price": {
                "max": 15000
              }
            },
            "pagination": {
              "limit": 20
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/catalog_search op=search direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.catalog.search": [
                {"version": "{{ bcp_schema_version }}"}
              ]
            }
          },
          "products": [
            {
              "id": "prod_abc123",
              "handle": "blue-runner-pro",
              "title": "Blue Runner Pro",
              "description": {
                "plain": "Lightweight running shoes with responsive cushioning."
              },
              "url": "https://business.example.com/products/blue-runner-pro",
              "categories": [
                { "value": "187", "taxonomy": "google_product_category" },
                { "value": "aa-8-1", "taxonomy": "shopify" },
                { "value": "Footwear > Running", "taxonomy": "merchant" }
              ],
              "price_range": {
                "min": { "amount": 12000, "currency": "BRL" },
                "max": { "amount": 12000, "currency": "BRL" }
              },
              "media": [
                {
                  "type": "image",
                  "url": "https://cdn.example.com/products/blue-runner-pro.jpg",
                  "alt_text": "Blue Runner Pro running shoes"
                }
              ],
              "options": [
                {
                  "name": "Size",
                  "values": [
                    {"label": "8"},
                    {"label": "9"},
                    {"label": "10"},
                    {"label": "11"},
                    {"label": "12"}
                  ]
                }
              ],
              "variants": [
                {
                  "id": "prod_abc123_size10",
                  "sku": "BRP-BLU-10",
                  "title": "Size 10",
                  "description": { "plain": "Size 10 variant" },
                  "price": { "amount": 12000, "currency": "BRL" },
                  "availability": { "available": true },
                  "options": [
                    { "name": "Size", "label": "10" }
                  ],
                  "tags": ["running", "road", "neutral"],
                  "seller": {
                    "name": "Example Store",
                    "links": [
                      {
                        "type": "refund_policy",
                        "url": "https://business.example.com/refunds"
                      }
                    ]
                  }
                }
              ],
              "rating": {
                "value": 4.5,
                "scale_max": 5,
                "count": 128
              },
              "metadata": {
                "collection": "Winter 2026",
                "technology": {
                  "midsole": "React foam",
                  "outsole": "Continental rubber"
                }
              }
            }
          ],
          "pagination": {
            "cursor": "eyJwYWdlIjoxfQ==",
            "has_next_page": true,
            "total_count": 47
          }
        }
      }
    }
    ```

### `lookup_catalog`

Mapeia para o recurso [Consulta de catálogo](lookup.md). Consulte a documentação de capacidade
para identificadores suportados, comportamento de resolução e requisitos de correlação do cliente.

O parâmetro `catalog.ids` aceita um array de identificadores e contexto opcional.

#### Solicitação de pesquisa

{{ extension_schema_fields(
  'catalog_lookup.json#/$defs/lookup_request', 'catalog/mcp'
) }}

### Resposta de pesquisa

{{ extension_schema_fields(
  'catalog_lookup.json#/$defs/lookup_response', 'catalog/mcp'
) }}

#### Exemplo de pesquisa

=== "Solicitação"

    <!-- ucp:example schema=shopping/catalog_lookup op=lookup direction=request extract=$.params.arguments.catalog -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "lookup_catalog",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "catalog": {
            "ids": ["prod_abc123", "var_xyz789"],
            "context": {
              "address_country": "BR"
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/catalog_lookup op=lookup direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.catalog.lookup": [
                {"version": "{{ bcp_schema_version }}"}
              ]
            }
          },
          "products": [
            {
              "id": "prod_abc123",
              "title": "Blue Runner Pro",
              "description": {
                "plain": "Lightweight running shoes with responsive cushioning."
              },
              "price_range": {
                "min": { "amount": 12000, "currency": "BRL" },
                "max": { "amount": 12000, "currency": "BRL" }
              },
              "variants": [
                {
                  "id": "prod_abc123_size10",
                  "sku": "BRP-BLU-10",
                  "title": "Size 10",
                  "description": { "plain": "Size 10 variant" },
                  "price": { "amount": 12000, "currency": "BRL" },
                  "availability": { "available": true },
                  "inputs": [
                    { "id": "prod_abc123", "match": "featured" }
                  ],
                  "tags": ["running", "road", "neutral"],
                  "seller": {
                    "name": "Example Store",
                    "links": [
                      {
                        "type": "refund_policy",
                        "url": "https://business.example.com/policies/refunds"
                      }
                    ]
                  }
                }
              ],
              "metadata": {
                "collection": "Winter 2026",
                "technology": {
                  "midsole": "React foam",
                  "outsole": "Continental rubber"
                }
              }
            },
            {
              "id": "prod_def456",
              "title": "Trail Master X",
              "description": {
                "plain": "Rugged trail running shoes with aggressive tread."
              },
              "price_range": {
                "min": { "amount": 15000, "currency": "BRL" },
                "max": { "amount": 15000, "currency": "BRL" }
              },
              "variants": [
                {
                  "id": "var_xyz789",
                  "sku": "TMX-GRN-11",
                  "title": "Size 11 - Green",
                  "description": { "plain": "Size 11 Green variant" },
                  "price": { "amount": 15000, "currency": "BRL" },
                  "availability": { "available": true },
                  "inputs": [
                    { "id": "var_xyz789", "match": "exact" }
                  ],
                  "tags": ["trail", "waterproof"],
                  "seller": {
                    "name": "Example Store"
                  }
                }
              ]
            }
          ]
        }
      }
    }
    ```

#### Sucesso Parcial

Quando alguns identificadores não são encontrados, a resposta inclui os produtos encontrados. O
a resposta PODE incluir mensagens informativas indicando quais identificadores não foram encontrados.

<!-- ucp:example schema=shopping/catalog_lookup op=lookup extract=$.result.structuredContent -->
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "structuredContent": {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "capabilities": {
          "br.dev.bcp.shopping.catalog.lookup": [
            {"version": "{{ bcp_schema_version }}"}
          ]
        }
      },
      "products": [
        {
          "id": "prod_abc123",
          "title": "Blue Runner Pro",
          "description": {
            "plain": "A comfortable everyday running shoe."
          },
          "price_range": {
            "min": { "amount": 12000, "currency": "BRL" },
            "max": { "amount": 12000, "currency": "BRL" }
          },
          "variants": [ ... ]
        }
      ],
      "messages": [
        {
          "type": "info",
          "code": "not_found",
          "content": "prod_notfound1"
        },
        {
          "type": "info",
          "code": "not_found",
          "content": "prod_notfound2"
        }
      ]
    }
  }
}
```

### `get_product`

Mapeia para o recurso [Consulta de catálogo](lookup.md#obter-produto-get_product). Retorna um singular
Objeto `product` para detalhes completos do produto com seleção interativa de opções.

#### Obter solicitação de produto

{{ extension_schema_fields(
  'catalog_lookup.json#/$defs/get_product_request', 'catalog/mcp'
) }}

#### Obtenha resposta do produto

{{ extension_schema_fields(
  'catalog_lookup.json#/$defs/get_product_response', 'catalog/mcp'
) }}

#### Obtenha exemplo de produto

=== "Solicitação"

    <!-- ucp:example schema=shopping/catalog_lookup op=get_product direction=request extract=$.params.arguments.catalog -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 3,
      "method": "tools/call",
      "params": {
        "name": "get_product",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "catalog": {
            "id": "prod_abc123",
            "selected": [
              { "name": "Color", "label": "Blue" }
            ],
            "preferences": ["Color", "Size"],
            "context": {
              "address_country": "BR"
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/catalog_lookup op=get_product direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 3,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.catalog.lookup": [
                {"version": "{{ bcp_schema_version }}"}
              ]
            }
          },
          "product": {
            "id": "prod_abc123",
            "handle": "runner-pro",
            "title": "Runner Pro",
            "description": {
              "plain": "Lightweight running shoes with responsive cushioning."
            },
            "url": "https://business.example.com/products/runner-pro",
            "price_range": {
              "min": { "amount": 12000, "currency": "BRL" },
              "max": { "amount": 15000, "currency": "BRL" }
            },
            "media": [
              {
                "type": "image",
                "url": "https://cdn.example.com/products/runner-pro-blue.jpg",
                "alt_text": "Runner Pro in Blue"
              }
            ],
            "options": [
              {
                "name": "Color",
                "values": [
                  {"label": "Blue", "available": true, "exists": true},
                  {"label": "Red", "available": true, "exists": true},
                  {"label": "Green", "available": false, "exists": true}
                ]
              },
              {
                "name": "Size",
                "values": [
                  {"label": "8", "available": true, "exists": true},
                  {"label": "9", "available": true, "exists": true},
                  {"label": "10", "available": true, "exists": true},
                  {"label": "11", "available": false, "exists": false},
                  {"label": "12", "available": true, "exists": true}
                ]
              }
            ],
            "selected": [
              { "name": "Color", "label": "Blue" }
            ],
            "variants": [
              {
                "id": "prod_abc123_blu_10",
                "sku": "BRP-BLU-10",
                "title": "Blue, Size 10",
                "description": { "plain": "Blue, Size 10" },
                "price": { "amount": 12000, "currency": "BRL" },
                "availability": { "available": true },
                "options": [
                  { "name": "Color", "label": "Blue" },
                  { "name": "Size", "label": "10" }
                ]
              },
              {
                "id": "prod_abc123_blu_12",
                "sku": "BRP-BLU-12",
                "title": "Blue, Size 12",
                "description": { "plain": "Blue, Size 12" },
                "price": { "amount": 15000, "currency": "BRL" },
                "availability": { "available": true },
                "options": [
                  { "name": "Color", "label": "Blue" },
                  { "name": "Size", "label": "12" }
                ]
              }
            ],
            "rating": {
              "value": 4.5,
              "scale_max": 5,
              "count": 128
            }
          }
        }
      }
    }
    ```

#### Produto não encontrado

Quando o identificador não é resolvido para um produto, o servidor retorna um
resultado JSON-RPC bem-sucedido com `ucp.status: "error"` e um descritivo
mensagem. Este é um resultado do aplicativo, não um erro de transporte.

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result.structuredContent -->
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "structuredContent": {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "status": "error",
        "capabilities": {
          "br.dev.bcp.shopping.catalog.lookup": [
            {"version": "{{ bcp_schema_version }}"}
          ]
        }
      },
      "messages": [
        {
          "type": "error",
          "code": "not_found",
          "content": "Product not found: prod_invalid",
          "severity": "unrecoverable"
        }
      ]
    }
  }
}
```

## Tratamento de erros

O BCP usa um modelo de erro de duas camadas que separa os erros de transporte dos resultados de negócios.

### Erros de transporte

Falhas no nível de transporte (autenticação, limitação de taxa, indisponibilidade) que
impedir o processamento da solicitação são retornados como JSON-RPC `error`. Veja o
[Especificação principal](../reference.md#error-code) para o código de erro completo
mapeamentos de código de erro de registro e JSON-RPC.

### Resultados de negócios

Todos os resultados no nível do aplicativo retornam um resultado JSON-RPC bem-sucedido com o BCP
envelope e matriz `messages` opcional. Consulte [Visão geral do catálogo](index.md#mensagens-e-tratamento-de-erros)
para semântica de mensagens e cenários comuns.

#### Exemplo: Todos os produtos não encontrados

Quando todos os identificadores solicitados não são resolvidos, a resposta contém um `products` vazio
matriz. A resposta PODE incluir mensagens informativas indicando quais identificadores foram
não encontrado.

<!-- ucp:example schema=shopping/catalog_lookup op=lookup direction=response extract=$.result.structuredContent -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "structuredContent": {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "capabilities": {
          "br.dev.bcp.shopping.catalog.lookup": [
            {"version": "{{ bcp_schema_version }}"}
          ]
        }
      },
      "products": [],
      "messages": [
        {
          "type": "info",
          "code": "not_found",
          "content": "prod_invalid"
        }
      ]
    }
  }
}
```

Os resultados de negócios usam o campo JSON-RPC `result` com mensagens na resposta
carga útil. Consulte a seção [Sucesso parcial](#sucesso-parcial) para lidar com problemas mistos
resultados.

## Entidades

### Produto detalhado {: #detail-product }

{{ extension_schema_fields('catalog_lookup.json#/$defs/detail_product', 'catalog/mcp') }}

### Obter resposta do produto {: #catalog-lookup-get-product-response }

{{ extension_schema_fields('catalog_lookup.json#/$defs/get_product_response', 'catalog/mcp') }}

### Resposta de erro {: #error-response }

{{ schema_fields('types/error_response', 'catalog/mcp') }}

## Conformidade

Uma implementação de transporte MCP em conformidade **DEVE**:

1. Implemente o protocolo JSON-RPC 2.0 corretamente.
2. Implementar ferramentas para cada capacidade de catálogo anunciada no perfil BCP da empresa, de acordo com seus respectivos requisitos de capacidade ([Search](search.md), [Lookup](lookup.md)). Cada capacidade pode ser adotada de forma independente. Quando o recurso Lookup é anunciado, as ferramentas `lookup_catalog` e `get_product` DEVEM estar disponíveis.
3. Use erros JSON-RPC para problemas de transporte; use a matriz `messages` para resultados de negócios.
4. Retorne o resultado bem-sucedido para solicitações de pesquisa; identificadores desconhecidos resultam em menos produtos devolvidos (PODEM incluir mensagens informativas `not_found`).
5. Valide as entradas da ferramenta em relação aos esquemas BCP.
6. Devolver produtos com objetos `Price` válidos (valor + moeda).
7. Suporta paginação baseada em cursor com limite padrão de 10.
8. Retorne `-32602` (parâmetros inválidos) para solicitações que excedem os limites de tamanho de lote.
