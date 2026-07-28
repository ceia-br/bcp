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

# Capacidade do carrinho - vinculação MCP

Este documento especifica a ligação do Model Context Protocol (MCP) para a
[capacidade do carrinho](cart.md).

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
      "br.dev.bcp.shopping.checkout": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/checkout",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/checkout.json"
        }
      ],
      "br.dev.bcp.shopping.cart": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/cart",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/cart.json"
        }
      ]
    },
    "payment_handlers": {}
  }
}
```

### Solicitar metadados

Os clientes MCP **DEVEM** incluir um objeto `meta` em cada solicitação contendo
metadados do protocolo:

<!-- ucp:example schema=shopping/cart op=create direction=request extract=$.params.arguments.cart -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_cart",
    "arguments": {
      "meta": {
        "ucp-agent": {
          "profile": "https://platform.example/profiles/shopping-agent.json"
        }
      },
      "cart": { "line_items": [ ... ] }
    }
  }
}
```

O campo `meta["ucp-agent"]` é **obrigatório** em todas as solicitações para habilitar
[negociação de capacidade](overview.md#protocolo-de-negociacao). Plataformas **PODEM**
incluir campos de metadados adicionais.

## Ferramentas

Os recursos do BCP são mapeados 1:1 para as ferramentas do MCP.

### Padrão de identificador

As ferramentas MCP separam a identificação de recursos dos dados de carga útil:

* **Solicitações:** Para operações em carrinhos existentes (`get`, `update`, `cancel`),
    um parâmetro `id` de nível superior identifica o recurso de destino. O
    objeto `cart` na carga útil da solicitação **NÃO DEVE** conter um campo `id`.
* **Respostas:** Todas as respostas incluem `cart.id` como parte do estado completo do recurso.
* **Criar:** A operação `create_cart` não requer um `id` na
    solicitação, e a resposta inclui o `cart.id` recentemente atribuído.

| Ferramenta | Operação | Descrição |
| :---- | :---- | :---- |
| `create_cart` | [Criar carrinho](cart.md#criar-carrinho) | Crie uma sessão de carrinho. |
| `get_cart` | [Obter carrinho](cart.md#obter-carrinho) | Obtenha uma sessão de carrinho. |
| `update_cart` | [Atualizar carrinho](cart.md#atualizar-carrinho) | Atualize uma sessão de carrinho. |
| `cancel_cart` | [Cancelar carrinho](cart.md#cancelar-carrinho) | Cancele uma sessão de carrinho. |

### `create_cart`

Mapeia para a operação [Criar carrinho](cart.md#criar-carrinho).

#### Esquema de entrada

{{ schema_fields('cart_create_req', 'cart') }}

#### Esquema de saída

{{ schema_fields('cart_resp', 'cart') }}

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=shopping/cart op=create direction=request extract=$.params.arguments.cart -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/call",
      "params": {
        "name": "create_cart",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "cart": {
            "line_items": [
              {
                "item": {
                  "id": "item_123"
                },
                "quantity": 2
              }
            ],
            "context": {
              "address_country": "BR",
              "address_region": "SP",
              "postal_code": "01310-100"
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.checkout": [{"version": "{{ bcp_schema_version }}"}],
              "br.dev.bcp.shopping.cart": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "id": "cart_abc123",
          "line_items": [
            {
              "id": "li_1",
              "item": {
                "id": "item_123",
                "title": "Red T-Shirt",
                "price": 2500
              },
              "quantity": 2,
              "totals": [
                {"type": "subtotal", "amount": 5000},
                {"type": "total", "amount": 5000}
              ]
            }
          ],
          "currency": "BRL",
          "totals": [
            {
              "type": "subtotal",
              "amount": 5000
            },
            {
              "type": "total",
              "amount": 5000
            }
          ],
          "continue_url": "https://business.example.com/checkout?cart=cart_abc123",
          "expires_at": "2026-01-16T12:00:00Z"
        },
        "content": [
          {
            "type": "text",
            "text": "{\"ucp\":{…},…}"
          }
        ]
      }
    }
    ```

=== "Resposta de erro"

    Todos os itens fora de estoque — nenhum recurso de carrinho é criado:

    <!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
          "messages": [
            {
              "type": "error",
              "code": "out_of_stock",
              "content": "All requested items are currently out of stock",
              "severity": "unrecoverable"
            }
          ],
          "continue_url": "https://merchant.com/"
        },
        "content": [
          {"type": "text", "text": "{\"ucp\":{…},…}"}
        ]
      }
    }
    ```

### `get_cart`

Mapeia para a operação [Get Cart](cart.md#obter-carrinho).

#### Esquema de entrada

* `id` (String, obrigatório): O ID da sessão do carrinho.

#### Esquema de saída

{{ schema_fields('cart_resp', 'cart') }}

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=transports/mcp_tool_call def=request direction=request -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/call",
      "params": {
        "name": "get_cart",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "id": "cart_abc123"
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.checkout": [{"version": "{{ bcp_schema_version }}"}],
              "br.dev.bcp.shopping.cart": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "id": "cart_abc123",
          "line_items": [
            {
              "id": "li_1",
              "item": {
                "id": "item_123",
                "title": "Red T-Shirt",
                "price": 2500
              },
              "quantity": 2,
              "totals": [
                {"type": "subtotal", "amount": 5000},
                {"type": "total", "amount": 5000}
              ]
            }
          ],
          "currency": "BRL",
          "totals": [
            {
              "type": "subtotal",
              "amount": 5000
            },
            {
              "type": "total",
              "amount": 5000
            }
          ],
          "continue_url": "https://business.example.com/checkout?cart=cart_abc123",
          "expires_at": "2026-01-16T12:00:00Z"
        },
        "content": [
          {
            "type": "text",
            "text": "{\"ucp\":{…},…}"
          }
        ]
      }
    }
    ```

=== "Não encontrado"

    <!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "status": "error",
            "capabilities": {
              "br.dev.bcp.shopping.cart": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "messages": [
            {
              "type": "error",
              "code": "not_found",
              "content": "Cart not found or has expired",
              "severity": "unrecoverable"
            }
          ],
          "continue_url": "https://merchant.com/"
        },
        "content": [
          {
            "type": "text",
            "text": "{\"ucp\":{…},…}"
          }
        ]
      }
    }
    ```

### `update_cart`

Mapeia para a operação [Atualizar carrinho](cart.md#atualizar-carrinho).

#### Esquema de entrada

* `id` (String, obrigatório): O ID da sessão do carrinho a ser atualizada.

{{ schema_fields('cart_update_req', 'cart') }}

#### Esquema de saída

{{ schema_fields('cart_resp', 'cart') }}

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=transports/mcp_tool_call def=request direction=request -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "update_cart",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "id": "cart_abc123",
          "cart": {
            "line_items": [
              {
                "item": {
                  "id": "item_123"
                },
                "quantity": 3
              },
              {
                "item": {
                  "id": "item_456"
                },
                "quantity": 1
              }
            ],
            "context": {
              "address_country": "BR",
              "address_region": "SP",
              "postal_code": "01310-100"
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.checkout": [{"version": "{{ bcp_schema_version }}"}],
              "br.dev.bcp.shopping.cart": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "id": "cart_abc123",
          "line_items": [
            {
              "id": "li_1",
              "item": {
                "id": "item_123",
                "title": "Red T-Shirt",
                "price": 2500
              },
              "quantity": 3,
              "totals": [
                {"type": "subtotal", "amount": 7500},
                {"type": "total", "amount": 7500}
              ]
            },
            {
              "id": "li_2",
              "item": {
                "id": "item_456",
                "title": "Blue Jeans",
                "price": 7500
              },
              "quantity": 1,
              "totals": [
                {"type": "subtotal", "amount": 7500},
                {"type": "total", "amount": 7500}
              ]
            }
          ],
          "currency": "BRL",
          "totals": [
            {
              "type": "subtotal",
              "amount": 15000
            },
            {
              "type": "total",
              "amount": 15000
            }
          ],
          "continue_url": "https://business.example.com/checkout?cart=cart_abc123",
          "expires_at": "2026-01-16T12:00:00Z"
        },
        "content": [
          {
            "type": "text",
            "text": "{\"ucp\":{…},…}"
          }
        ]
      }
    }
    ```

### `cancel_cart`

Mapeia para a operação [Cancelar carrinho](cart.md#cancelar-carrinho).

#### Esquema de entrada

* `id` (String, obrigatório): O ID da sessão do carrinho.

#### Esquema de saída

{{ schema_fields('cart_resp', 'cart') }}

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=transports/mcp_tool_call def=request direction=request -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/call",
      "params": {
        "name": "cancel_cart",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            },
            "idempotency-key": "660e8400-e29b-41d4-a716-446655440001"
          },
          "id": "cart_abc123"
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.checkout": [{"version": "{{ bcp_schema_version }}"}],
              "br.dev.bcp.shopping.cart": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "id": "cart_abc123",
          "line_items": [
            {
              "id": "li_1",
              "item": {
                "id": "item_123",
                "title": "Red T-Shirt",
                "price": 2500
              },
              "quantity": 2,
              "totals": [
                {"type": "subtotal", "amount": 5000},
                {"type": "total", "amount": 5000}
              ]
            }
          ],
          "currency": "BRL",
          "totals": [
            {
              "type": "subtotal",
              "amount": 5000
            },
            {
              "type": "total",
              "amount": 5000
            }
          ],
          "continue_url": "https://business.example.com/checkout?cart=cart_abc123"
        },
        "content": [
          {
            "type": "text",
            "text": "{\"ucp\":{…},…}"
          }
        ]
      }
    }
    ```

## Tratamento de erros

O BCP distingue entre erros de protocolo e resultados de negócios. Veja a
[especificação principal](overview.md#tratamento-de-erros) para o registro completo
de códigos de erro e exemplos de vinculação de transporte.

* **Erros de protocolo**: falhas no nível de transporte (autenticação, limitação de taxa,
    indisponibilidade) que impedem o processamento da solicitação. Retornadas como JSON-RPC
    `error` com código `-32000` (ou `-32001` para erros de descoberta).
* **Resultados de negócios**: resultados em nível de aplicação do processamento
    bem-sucedido da solicitação, retornados como JSON-RPC `result` com envelope BCP e `messages`.

### Resultados de negócios

Os resultados de negócios (incluindo erros não encontrados e de validação) são retornados como
JSON-RPC `result` com `structuredContent` contendo o envelope BCP e
`messages`:

<!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.result.structuredContent -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "structuredContent": {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "status": "error",
        "capabilities": {
          "br.dev.bcp.shopping.cart": [{"version": "{{ bcp_schema_version }}"}]
        }
      },
      "messages": [
        {
          "type": "error",
          "code": "not_found",
          "content": "Cart not found or has expired",
          "severity": "unrecoverable"
        }
      ],
      "continue_url": "https://merchant.com/"
    },
    "content": [
      {"type": "text", "text": "{\"ucp\":{…},…}"}
    ]
  }
}
```

## Conformidade

Uma implementação de transporte MCP em conformidade **DEVE**:

1. Implementar o protocolo JSON-RPC 2.0 corretamente.
2. Fornecer todas as ferramentas básicas do carrinho definidas nesta especificação.
3. Retornar erros de acordo com a [especificação principal](overview.md#tratamento-de-erros).
4. Retornar os resultados de negócios como JSON-RPC `result` com envelope BCP e
    matriz `messages`.
5. Validar as entradas da ferramenta em relação aos esquemas BCP.
6. Suportar transporte HTTP com streaming.
