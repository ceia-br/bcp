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

# Capacidade de checkout - vinculação MCP

Este documento especifica a ligação do Model Context Protocol (MCP) para a
[capacidade de checkout](checkout.md).

## Fundamentos do Protocolo

### Descoberta

As empresas anunciam a disponibilidade de transporte MCP através do seu perfil BCP em
`/.well-known/bcp`.

<!-- ucp:example schema=profile def=business_schema op=read direction=response -->
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
      "br.dev.bcp.shopping.fulfillment": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
          "extends": "br.dev.bcp.shopping.checkout"
        }
      ]
    },
    "payment_handlers": {
      "br.dev.bcp.pix": [
        {
          "id": "pix_recebedor_001",
          "version": "{{ bcp_schema_version }}",
          "available_instruments": [{"type": "pix"}],
          "config": {"environment": "production"}
        }
      ],
      "com.example.vendor.delegate_payment": [
        {
          "id": "handler_1",
          "version": "{{ bcp_schema_version }}",
          "spec": "https://example.vendor.com/specs/delegate-payment",
          "schema": "https://example.vendor.com/schemas/delegate-payment-config.json",
          "available_instruments": [
            {"type": "card", "constraints": {"brands": ["visa", "mastercard"]}}
          ],
          "config": {}
        }
      ]
    }
  }
}
```

### Solicitar metadados

Os clientes MCP **DEVEM** incluir um objeto `meta` em cada solicitação contendo
metadados do protocolo:

<!-- ucp:example schema=shopping/checkout op=create direction=request extract=$.params.arguments.checkout -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "create_checkout",
    "arguments": {
      "meta": {
        "ucp-agent": {
          "profile": "https://platform.example/profiles/shopping-agent.json"
        },
        "idempotency-key": "550e8400-e29b-41d4-a716-446655440000"
      },
      "checkout": { "line_items": [ ... ] }
    }
  }
}
```

O campo `meta["ucp-agent"]` é **obrigatório** em todas as solicitações para habilitar
[negociação de capacidade](overview.md#protocolo-de-negociacao).
As operações `complete_checkout` e `cancel_checkout` também requerem
`meta["idempotency-key"]` para segurança de nova tentativa. Plataformas **PODEM** incluir
campos de metadados adicionais.

## Ferramentas

Os recursos do BCP são mapeados 1:1 para as ferramentas do MCP.

### Padrão de identificador

As ferramentas MCP separam a identificação de recursos dos dados de carga útil:

* **Solicitações:** Para operações em checkouts existentes (`get`, `update`,
    `complete`, `cancel`), um parâmetro `id` de nível superior identifica o
    recurso de destino. O objeto `checkout` na carga útil da solicitação
    **NÃO DEVE** conter um campo `id`.
* **Respostas:** Todas as respostas incluem `checkout.id` como parte do estado completo do recurso.
* **Criar:** A operação `create_checkout` não requer um `id` na solicitação e a resposta inclui o `checkout.id` recentemente atribuído.

| Ferramenta | Operação | Descrição |
| :----------------- | :------------------------------------------------- | :------------------------- |
| `create_checkout` | [Criar Check-out](checkout.md#criar-check-out) | Crie uma sessão de checkout. |
| `get_checkout` | [Obter check-out](checkout.md#obter-check-out) | Obtenha uma sessão de checkout.    |
| `update_checkout` | [Atualizar Check-out](checkout.md#atualizar-check-out) | Atualize uma sessão de checkout. |
| `complete_checkout` | [Check-out completo](checkout.md#concluir-check-out) | Faça o pedido.           |
| `cancel_checkout` | [Cancelar check-out](checkout.md#cancelar-check-out) | Cancele uma sessão de checkout. |

### `create_checkout`

Mapeia para a operação [Criar Checkout](checkout.md#criar-check-out).

#### Esquema de entrada

* `checkout` ([Checkout](checkout.md#criar-check-out)): **Obrigatório**. Contém
    os dados da sessão de checkout inicial e extensões opcionais.
    * Extensões (opcional):
        * `br.dev.bcp.shopping.buyer_consent`: [Consentimento do comprador](buyer-consent.md)
        * `br.dev.bcp.shopping.fulfillment`: [Fulfillment](fulfillment.md)
        * `br.dev.bcp.shopping.discount`: [Desconto](discount.md)
        * `br.dev.bcp.shopping.ap2_mandate`: [Mandatos AP2](ap2-mandates.md)

#### Esquema de saída

* Objeto [Checkout](checkout.md#criar-check-out).

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=shopping/checkout op=create direction=request extract=$.params.arguments.checkout -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "tools/call",
      "params": {
        "name": "create_checkout",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "checkout": {
            "buyer": {
              "email": "jane.doe@example.com",
              "first_name": "Jane",
              "last_name": "Doe"
            },
            "line_items": [
              {
                "id": "li_1",
                "item": {
                  "id": "item_123"
                },
                "quantity": 1
              }
            ],
            "currency": "BRL",
            "fulfillment": {
              "methods": [
                {
                  "type": "shipping",
                  "destinations": [
                    {
                      "street_address": "Avenida Paulista, 1000",
                      "address_locality": "São Paulo",
                      "address_region": "SP",
                      "postal_code": "01310-100",
                      "address_country": "BR"
                    }
                  ]
                }
              ]
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.checkout": [
                {"version": "{{ bcp_schema_version }}"}
              ],
              "br.dev.bcp.shopping.fulfillment": [
                {"version": "{{ bcp_schema_version }}"}
              ]
            },
            "payment_handlers": {
              "br.dev.bcp.pix": [
                {"id": "pix_recebedor_001", "version": "{{ bcp_schema_version }}", "available_instruments": [{"type": "pix"}], "config": {"environment": "production"}}
              ],
              "com.example.vendor.delegate_payment": [
                {"id": "handler_1", "version": "{{ bcp_schema_version }}", "available_instruments": [{"type": "card"}], "config": {}}
              ]
            }
          },
          "id": "checkout_abc123",
          "status": "incomplete",
          "buyer": {
            "email": "jane.doe@example.com",
            "first_name": "Jane",
            "last_name": "Doe"
          },
          "line_items": [
            {
              "id": "li_1",
              "item": {
                "id": "item_123",
                "title": "Blue Jeans",
                "price": 5000
              },
              "quantity": 1,
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
              "type": "fulfillment",
              "display_text": "Shipping",
              "amount": 500
            },
            {
              "type": "total",
              "amount": 5500
            }
          ],
          "fulfillment": {
            "methods": [
              {
                "id": "shipping_1",
                "type": "shipping",
                "line_item_ids": ["li_1"],
                "selected_destination_id": "dest_home",
                "destinations": [
                  {
                    "id": "dest_home",
                    "street_address": "Avenida Paulista, 1000",
                    "address_locality": "São Paulo",
                    "address_region": "SP",
                    "postal_code": "01310-100",
                    "address_country": "BR"
                  }
                ],
                "groups": [
                  {
                    "id": "package_1",
                    "line_item_ids": ["li_1"],
                    "selected_option_id": "standard",
                    "options": [
                      {
                        "id": "standard",
                        "title": "Standard Shipping",
                        "description": "Arrives in 5-7 business days",
                        "totals": [
                          {
                            "type": "total",
                            "amount": 500
                          }
                        ]
                      },
                      {
                        "id": "express",
                        "title": "Express Shipping",
                        "description": "Arrives in 2-3 business days",
                        "totals": [
                          {
                            "type": "total",
                            "amount": 1000
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            ]
          },
          "links": [
            {
              "type": "privacy_policy",
              "url": "https://business.example.com/privacy"
            },
            {
              "type": "terms_of_service",
              "url": "https://business.example.com/terms"
            }
          ],
          "continue_url": "https://business.example.com/checkout-sessions/checkout_abc123",
          "expires_at": "2026-01-11T18:30:00Z"
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

    Todos os itens fora de estoque — nenhum recurso de checkout é criado:

    <!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": { "version": "2026-01-11", "status": "error" },
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

### `get_checkout`

Mapeia para a operação [Get Checkout](checkout.md#obter-check-out).

#### Esquema de entrada

* `id` (String): **Obrigatório**. O ID da sessão de checkout.

#### Esquema de saída

* Objeto [Checkout](checkout.md#obter-check-out).

### `update_checkout`

Mapeia para a operação [Update Checkout](checkout.md#atualizar-check-out).

#### Esquema de entrada

* `id` (String): **Obrigatório**. O ID da sessão de checkout a ser atualizada.
* `checkout` ([Checkout](checkout.md#atualizar-check-out)): **Obrigatório**.
    Contém os dados atualizados da sessão de checkout.
    * Extensões (opcional):
        * `br.dev.bcp.shopping.buyer_consent`: [Consentimento do comprador](buyer-consent.md)
        * `br.dev.bcp.shopping.fulfillment`: [Fulfillment](fulfillment.md)
        * `br.dev.bcp.shopping.discount`: [Desconto](discount.md)
        * `br.dev.bcp.shopping.ap2_mandate`: [Mandatos AP2](ap2-mandates.md)

#### Esquema de saída

* Objeto [Checkout](checkout.md#atualizar-check-out).

#### Exemplo

=== "Solicitação"

    <!-- ucp:example schema=shopping/checkout op=update direction=request extract=$.params.arguments.checkout -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "method": "tools/call",
      "params": {
        "name": "update_checkout",
        "arguments": {
          "meta": {
            "ucp-agent": {
              "profile": "https://platform.example/profiles/v2026-01/shopping-agent.json"
            }
          },
          "id": "checkout_abc123",
          "checkout": {
            "buyer": {
              "email": "jane.doe@example.com",
              "first_name": "Jane",
              "last_name": "Doe"
            },
            "line_items": [
              {
                "item": {
                  "id": "item_123"
                },
                "id": "li_1",
                "quantity": 1
              }
            ],
            "currency": "BRL",
            "fulfillment": {
              "methods": [
                {
                  "id": "shipping_1",
                  "line_item_ids": ["li_1"],
                  "groups": [
                    {
                      "id": "package_1",
                      "selected_option_id": "express"
                    }
                  ]
                }
              ]
            }
          }
        }
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 2,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "capabilities": {
              "br.dev.bcp.shopping.checkout": [
                {"version": "{{ bcp_schema_version }}"}
              ],
              "br.dev.bcp.shopping.fulfillment": [
                {"version": "{{ bcp_schema_version }}"}
              ]
            },
            "payment_handlers": {
              "br.dev.bcp.pix": [
                {"id": "pix_recebedor_001", "version": "{{ bcp_schema_version }}", "available_instruments": [{"type": "pix"}], "config": {"environment": "production"}}
              ],
              "com.example.vendor.delegate_payment": [
                {"id": "handler_1", "version": "{{ bcp_schema_version }}", "available_instruments": [{"type": "card"}], "config": {}}
              ]
            }
          },
          "id": "checkout_abc123",
          "status": "incomplete",
          "buyer": {
            "email": "jane.doe@example.com",
            "first_name": "Jane",
            "last_name": "Doe"
          },
          "line_items": [
            {
              "id": "li_1",
              "item": {
                "id": "item_123",
                "title": "Blue Jeans",
                "price": 5000
              },
              "quantity": 1,
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
              "type": "fulfillment",
              "display_text": "Shipping",
              "amount": 1000
            },
            {
              "type": "total",
              "amount": 6000
            }
          ],
          "fulfillment": {
            "methods": [
              {
                "id": "shipping_1",
                "type": "shipping",
                "line_item_ids": ["li_1"],
                "selected_destination_id": "dest_home",
                "destinations": [
                  {
                    "id": "dest_home",
                    "street_address": "Avenida Paulista, 1000",
                    "address_locality": "São Paulo",
                    "address_region": "SP",
                    "postal_code": "01310-100",
                    "address_country": "BR"
                  }
                ],
                "groups": [
                  {
                    "id": "package_1",
                    "line_item_ids": ["li_1"],
                    "selected_option_id": "express",
                    "options": [
                      {
                        "id": "standard",
                        "title": "Standard Shipping",
                        "description": "Arrives in 5-7 business days",
                        "totals": [
                          {
                            "type": "total",
                            "amount": 500
                          }
                        ]
                      },
                      {
                        "id": "express",
                        "title": "Express Shipping",
                        "description": "Arrives in 2-3 business days",
                        "totals": [
                          {
                            "type": "total",
                            "amount": 1000
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            ]
          },
          "links": [
            {
              "type": "privacy_policy",
              "url": "https://business.example.com/privacy"
            },
            {
              "type": "terms_of_service",
              "url": "https://business.example.com/terms"
            }
          ],
          "continue_url": "https://business.example.com/checkout-sessions/checkout_abc123",
          "expires_at": "2026-01-11T18:30:00Z"
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

### `complete_checkout`

Mapeia para a operação [Complete Checkout](checkout.md#concluir-check-out).

#### Esquema de entrada

* `meta` (Objeto): **Obrigatório**. Solicite metadados contendo:
    * `ucp-agent` (Objeto): **Obrigatório**. Identificação do agente da plataforma.
    * `idempotency-key` (String, UUID): **Obrigatório**. Chave exclusiva para segurança de novas tentativas.
* `id` (String): **Obrigatório**. O ID da sessão de checkout.
* `checkout` ([Checkout](checkout.md#concluir-check-out)): **Obrigatório**.
    Contém credenciais de pagamento e outros dados de finalização para executar a transação.

#### Esquema de saída

* Objeto [Checkout](checkout.md#concluir-check-out), contendo um parcial
   `order` que contém apenas `id` e `permalink_url`.

### `cancel_checkout`

Mapeia para a operação [Cancel Checkout](checkout.md#cancelar-check-out).

#### Esquema de entrada

* `meta` (Objeto): **Obrigatório**. Solicite metadados contendo:
    * `ucp-agent` (Objeto): **Obrigatório**. Identificação do agente da plataforma.
    * `idempotency-key` (String, UUID): **Obrigatório**. Chave exclusiva para segurança de novas tentativas.
* `id` (String): **Obrigatório**. O ID da sessão de checkout.

#### Esquema de saída

* Objeto [Checkout](checkout.md#cancelar-check-out) com `status: canceled`.

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

Os resultados de negócios (incluindo erros como mercadorias indisponíveis) são retornados
como JSON-RPC `result` com `structuredContent` contendo o envelope BCP e
`messages`:

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.result.structuredContent -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "structuredContent": {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "payment_handlers": {},
        "capabilities": {
          "br.dev.bcp.shopping.checkout": [{"version": "{{ bcp_schema_version }}"}]
        }
      },
      "id": "checkout_abc123",
      "status": "incomplete",
      "line_items": [
        {
          "id": "li_1",
           "item": {
              "id": "item_123",
              "title": "Blue Jeans",
              "price": 5000
            },
          "quantity": 12,
          "totals": [...]
        }
      ],
      "totals": [...],
      "currency": "BRL",
      "links": [],
      "messages": [
        {
          "type": "warning",
          "code": "quantity_adjusted",
          "content": "Quantity adjusted, requested 100 units but only 12 available",
          "path": "$.line_items[0].quantity"
        }
      ],
      "continue_url": "https://merchant.com/checkout/checkout_abc123"
    },
    "content": [
      {"type": "text", "text": "{\"ucp\":{…},…}"}
    ]
  }
}
```

Para `create_checkout`, quando todos os itens estiverem indisponíveis e nenhum checkout puder ser criado,
JSON-RPC `result` com `structuredContent` contendo o envelope BCP e `messages`:

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result.structuredContent -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "structuredContent": {
      "ucp": { "version": "2026-01-11", "status": "error" },
      "messages": [
        {
          "type": "error",
          "code": "item_unavailable",
          "content": "Items are not available for purchase in your region",
          "severity": "unrecoverable",
          "path": "$.line_items"
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

## Assinatura de mensagem

As plataformas **DEVEM** autenticar agentes ao usar o transporte MCP. Ao usar
Assinaturas de mensagens HTTP, todas as operações de checkout seguem a
especificação de [Assinaturas de mensagens](signatures.md).

### Solicitar assinatura

O transporte MCP do BCP usa **HTTP streamable**, permitindo o mesmo mecanismo
de assinatura RFC 9421 usado pelo REST. A assinatura é aplicada na camada HTTP:

| Cabeçalho | Obrigatório | Descrição |
| :---------------------- | :------- | :--------------------------------------- |
| `Signature-Input` | Sim | Descreve componentes assinados |
| `Signature` | Sim | Contém o valor da assinatura |
| `Content-Digest` | Sim | Hash SHA-256 do corpo da solicitação |
| `BCP-Agent` | Sim | Identidade do signatário (URL do perfil) |
| `Idempotency-Key` | Cond.* | Chave exclusiva para proteção de repetição |

\* Obrigatório para `complete_checkout` e `cancel_checkout`

**Exemplo de solicitação assinada:**

```http
POST /mcp HTTP/1.1
Host: business.example.com
Content-Type: application/json
BCP-Agent: profile="https://platform.example/.well-known/bcp"
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Digest: sha-256=:RK/0qy18MlBSVnWgjwz6lZEWjP/lF5HF9bvEF8FabDg=:
Signature-Input: sig1=("@method" "@authority" "@path" "content-digest" "content-type" "bcp-agent" "idempotency-key");keyid="platform-2026"
Signature: sig1=:MEUCIQDXyK9N3p5Rt...:

{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"complete_checkout","arguments":{"id":"checkout_abc123","checkout":{"payment":{...}}}}}
```

O `Content-Digest` vincula o corpo JSON-RPC à assinatura. Nenhuma canonização
JSON é necessária.

Consulte [Assinaturas de mensagens - Transporte MCP](signatures.md#transporte-mcp)
para obter detalhes.

### Assinatura de resposta

Assinaturas de resposta são **RECOMENDADAS** para:

* Respostas `complete_checkout` (confirmação do pedido)

As assinaturas de resposta são **OPCIONAIS** para:

* `create_checkout`, `get_checkout`, `update_checkout`, `cancel_checkout`

**Exemplo de resposta assinada:**

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Digest: sha-256=:Y5fK8nLmPqRsT3vWxYzAbCdEfGhIjKlMnO...:
Signature-Input: sig1=("@status" "content-digest" "content-type");keyid="merchant-2026"
Signature: sig1=:MFQCIH7kL9nM2oP5qR8sT1uV4wX6yZaB3cD...:

{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"..."}],"structuredContent":{"id":"checkout_abc123","status":"completed"}}}
```

Consulte [Assinaturas de mensagens - Assinatura de resposta REST](signatures.md#assinatura-de-resposta-rest)
para o algoritmo de assinatura (idêntico para MCP sobre HTTP).

## Conformidade

Uma implementação de transporte MCP em conformidade **DEVE**:

1. Implementar o protocolo JSON-RPC 2.0 corretamente.
2. Fornecer todas as ferramentas básicas de checkout definidas nesta especificação.
3. Retornar erros de acordo com a [especificação principal](overview.md#tratamento-de-erros).
4. Retornar os resultados de negócios como JSON-RPC `result` com envelope BCP e
    matriz `messages`.
5. Validar as entradas da ferramenta em relação aos esquemas BCP.
6. Suportar transporte HTTP com streaming.

Uma implementação em conformidade **DEVE**:

1. Autenticar os agentes usando um dos mecanismos suportados (chaves de API, OAuth,
    mTLS ou assinaturas de mensagens HTTP conforme [Assinaturas de mensagens](signatures.md)).
2. Verificar a autenticação nas solicitações recebidas antes do processamento.

## Implementação

As operações BCP são definidas usando [OpenRPC](https://open-rpc.org/) (formato
de esquema JSON-RPC). A [especificação MCP](https://modelcontextprotocol.io/)
requer que todas as invocações de ferramenta usem um método `tools/call` com o
nome da operação e os argumentos envolvidos em `params`. Os implementadores
**DEVEM** aplicar esta transformação:

| OpenRPC | MCP |
|:--------|:-------------------|
| `method` | `params.name` |
| `params` | `params.arguments` |

**Convenções de parâmetros:**

* `meta` contém metadados de solicitação
* `id` identifica o recurso alvo (equivalente ao parâmetro do caminho)
* `checkout` contém a carga útil do domínio (equivalente ao corpo)

**Exemplo:** Dada a operação `complete_checkout` definida em OpenRPC:

<!-- ucp:example schema=shopping/checkout op=complete direction=request extract=$.params.checkout -->
```json
{
  "method": "complete_checkout",
  "params": {
    "meta": {
      "ucp-agent": { "profile": "https://..." },
      "idempotency-key": "550e8400-e29b-41d4-a716-446655440000"
    },
    "id": "checkout_abc123",
    "checkout": { "payment": {...} }
  }
}
```

Os implementadores **DEVEM** expor isso como um endpoint MCP `tools/call`:

<!-- ucp:example schema=shopping/checkout op=complete direction=request extract=$.params.arguments.checkout -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "complete_checkout",
    "arguments": {
      "meta": {
        "ucp-agent": { "profile": "https://..." },
        "idempotency-key": "550e8400-e29b-41d4-a716-446655440000"
      },
      "id": "checkout_abc123",
      "checkout": { "payment": {...} }
    }
  }
}
```
