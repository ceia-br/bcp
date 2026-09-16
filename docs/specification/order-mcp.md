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

# Capacidade de pedido - vinculação MCP

Este documento especifica a ligação do Model Context Protocol (MCP) para o
[Capacidade de pedido](order.md).

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
      "br.dev.bcp.shopping.order": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/order",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/order.json"
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

<!-- ucp:example schema=transports/mcp_tool_call def=request direction=request -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_order",
    "arguments": {
      "meta": {
        "ucp-agent": {
          "profile": "https://platform.example/.well-known/bcp"
        }
      },
      "id": "order_abc123"
    }
  }
}
```

O campo `meta["ucp-agent"]` é **obrigatório** em todas as solicitações para habilitar
[negociação de capacidade](overview.md#protocolo-de-negociacao). Plataformas **PODEM**
incluir campos de metadados adicionais.

## Ferramentas

Os recursos do BCP são mapeados 1:1 para as ferramentas do MCP.

| Ferramenta | Operação | Descrição |
| :---- | :---- | :---- |
| `get_order` | [Obter pedido](order.md#get-order) | Obtenha o estado atual de um pedido. |

### `get_order`

Mapeia para a operação [Obter pedido](order.md#get-order). Retorna o
instantâneo do estado atual de um pedido.

#### Esquema de entrada

* `meta` (Objeto obrigatório): Solicita metadados com `ucp-agent.profile`.
* `id` (String, obrigatório): O ID do pedido.

#### Esquema de saída

{{ schema_fields('order', 'order') }}

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=transports/mcp_tool_call def=request direction=request -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/call",
      "params": {
        "name": "get_order",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/.well-known/bcp"
            }
          },
          "id": "order_abc123"
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/order op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.order": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "id": "order_abc123",
          "checkout_id": "checkout_xyz789",
          "permalink_url": "https://business.example.com/orders/abc123",
          "currency": "BRL",
          "line_items": [
            {
              "id": "li_shoes",
              "item": { "id": "prod_shoes", "title": "Running Shoes", "price": 3000 },
              "quantity": { "total": 1, "fulfilled": 1 },
              "totals": [
                {"type": "subtotal", "amount": 3000},
                {"type": "total", "amount": 3000}
              ],
              "status": "fulfilled"
            }
          ],
          "fulfillment": {
            "expectations": [
              {
                "id": "exp_1",
                "line_items": [{ "id": "li_shoes", "quantity": 1 }],
                "method_type": "shipping",
                "destination": {
                  "street_address": "Rua das Flores, 123",
                  "address_locality": "São Paulo",
                  "address_region": "SP",
                  "address_country": "BR",
                  "postal_code": "01310-100"
                },
                "description": "Entregue"
              }
            ],
            "events": [
              {
                "id": "evt_1",
                "occurred_at": "2026-01-08T10:30:00Z",
                "type": "delivered",
                "line_items": [{ "id": "li_shoes", "quantity": 1 }],
                "tracking_number": "BR123456784BR",
                "tracking_url": "https://rastreamento.correios.com.br/app/index.php?objetos=BR123456784BR",
                "description": "Entregue na portaria"
              }
            ]
          },
          "adjustments": [],
          "totals": [
            { "type": "subtotal", "amount": 3000 },
            { "type": "fulfillment", "amount": 800 },
            { "type": "tax", "amount": 304 },
            { "type": "total", "amount": 4104 }
          ]
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

    <!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result.structuredContent -->
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
              "br.dev.bcp.shopping.order": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "messages": [
            {
              "type": "error",
              "code": "not_found",
              "severity": "unrecoverable",
              "content": "Order not found."
            }
          ]
        },
        "content": [
          {
            "type": "text",
            "text": "Order not found."
          }
        ]
      }
    }
    ```

=== "Não autorizado"

    <!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result.structuredContent -->
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
              "br.dev.bcp.shopping.order": [{"version": "{{ bcp_schema_version }}"}]
            }
          },
          "messages": [
            {
              "type": "error",
              "code": "unauthorized",
              "severity": "unrecoverable",
              "content": "Not authorized to access this order."
            }
          ]
        },
        "content": [
          {
            "type": "text",
            "text": "Not authorized to access this order."
          }
        ]
      }
    }
    ```

## Tratamento de erros

Quando a empresa não consegue devolver um pedido, a resposta inclui uma matriz
`messages` que descreve o resultado. Plataformas **DEVEM** verificar `messages` antes de
acessar os campos do pedido.

## Conformidade

Plataformas que implementam a vinculação MCP:

* **DEVE** incluir `meta.ucp-agent.profile` em todas as solicitações
* **DEVE** verificar o array `messages` nas respostas antes de acessar os dados do pedido
* **DEVE** delegar à empresa, via `permalink_url`, a experiência oficial do pedido
  — o site da empresa é a fonte da verdade para os detalhes do pedido
  e operações pós-compra

Empresas que implementam a vinculação MCP:

* **DEVE** implementar a ferramenta `get_order` de acordo com
  [Esquema OpenRPC](https://bcp.dev.br/services/shopping/mcp.openrpc.json)

Consulte [Capacidade do pedido - Diretrizes](order.md#operations-guidelines) para
requisitos de nível de capacidade que se aplicam a todos os transportes.
