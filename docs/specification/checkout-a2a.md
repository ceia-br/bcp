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

# Capacidade de checkout: binding A2A

Este documento especifica o binding do
[Agent2Agent Protocol 1.0](https://a2a-protocol.org/latest/specification/)
para a [capacidade de checkout](checkout.md). O binding usa JSON-RPC 2.0 sobre
HTTP e os modelos ProtoJSON do A2A 1.0.

## Descoberta do transporte

Empresas que suportam A2A devem anunciar o endpoint do Agent Card em `services`
no perfil BCP publicado em `/.well-known/bcp`. O Agent Card é um documento A2A
separado, publicado no endereço anunciado pelo perfil.

<!-- ucp:example schema=profile def=business_schema extract=$.ucp.services target=$.ucp.services -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {
      "br.dev.bcp.shopping": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "a2a",
          "endpoint": "https://example-business.com/.well-known/agent-card.json"
        }
      ]
    }
  }
}
```

O Agent Card declara cada combinação de endpoint, binding e versão em
`supportedInterfaces`. Para este binding, `protocolBinding` é `JSONRPC` e
`protocolVersion` é `1.0`. A extensão BCP fica em
`capabilities.extensions`, conforme o modelo A2A 1.0.

<!-- ucp:example schema=transports/a2a_message def=agent_card -->
```json
{
  "name": "Agente comercial de exemplo",
  "description": "Agente comercial com checkout BCP",
  "version": "1.0.0",
  "supportedInterfaces": [
    {
      "url": "https://example-business.com/bcp/a2a",
      "protocolBinding": "JSONRPC",
      "protocolVersion": "1.0"
    }
  ],
  "capabilities": {
    "streaming": false,
    "pushNotifications": false,
    "extensions": [
      {
        "uri": "https://bcp.dev.br/{{ bcp_version }}/specification/reference",
        "description": "Tipos estruturados do Brazilian Commerce Protocol",
        "required": false,
        "params": {
          "capabilities": {
            "br.dev.bcp.shopping.checkout": [
              {"version": "{{ bcp_schema_version }}"}
            ],
            "br.dev.bcp.shopping.fulfillment": [
              {
                "version": "{{ bcp_schema_version }}",
                "extends": "br.dev.bcp.shopping.checkout"
              }
            ]
          }
        }
      }
    ]
  },
  "defaultInputModes": ["text/plain", "application/json"],
  "defaultOutputModes": ["text/plain", "application/json"],
  "skills": [
    {
      "id": "bcp-checkout",
      "name": "Checkout BCP",
      "description": "Cria, atualiza e conclui sessões de checkout BCP",
      "tags": ["commerce", "checkout", "bcp"]
    }
  ]
}
```

## Anúncio do perfil do agente de compras

Plataformas de compras devem enviar o URI de seu perfil BCP em `BCP-Agent` em
cada solicitação. O perfil pode ser publicado em qualquer URI estável controlado
pela plataforma.

O cliente também deve selecionar a versão A2A e ativar a extensão BCP pelos
parâmetros de serviço do A2A. No binding JSON-RPC, esses parâmetros são
cabeçalhos HTTP.

```http
BCP-Agent: profile="https://agent.example/profiles/v2026-07/shopping-agent.json"
A2A-Version: 1.0
A2A-Extensions: https://bcp.dev.br/{{ bcp_version }}/specification/reference
Content-Type: application/json
```

| Cabeçalho | Descrição |
| :-- | :-- |
| `BCP-Agent` | URI do perfil BCP da plataforma de compras. |
| `A2A-Version` | Versão A2A selecionada para a interface, `1.0`. |
| `A2A-Extensions` | Lista separada por vírgulas das extensões ativadas. |

O URI da extensão BCP A2A é
`https://bcp.dev.br/{{ bcp_version }}/specification/reference`.

## Interações A2A

Agentes comerciais podem retornar diretamente um `Message` ou criar um `Task`
quando a operação exigir acompanhamento. Em ambos os casos, os tipos BCP são
transportados em um `Part` cujo membro `data` contém o objeto estruturado.

No A2A 1.0, `Part` não usa `kind` nem `type`. A presença de `text`, `data`,
`raw` ou `url` identifica o conteúdo. Mensagens que carregam dados BCP também
declaram o URI em `extensions`.

O agente comercial gera `contextId`. A plataforma deve reutilizá-lo nos turnos
seguintes da mesma conversa. Se a resposta criar um `Task`, a plataforma também
deve enviar `taskId` até o encerramento da tarefa. Uma tarefa terminal não aceita
novas mensagens, mas o mesmo `contextId` pode iniciar outra tarefa.

## Idempotência

Agentes comerciais devem usar o `messageId`, criado por quem envia a mensagem,
para detectar mensagens duplicadas causadas por novas tentativas da plataforma.

## Funcionalidade de checkout

A capacidade Checkout permite gerenciar itens em uma sessão e concluir a
compra. O agente comercial normalmente integra essa capacidade às APIs de
checkout da empresa.

O checkout completo retornado pelo agente comercial deve aparecer no membro
`a2a.bcp.checkout` de um `Part.data`.

### Solicitação em linguagem natural

<!-- ucp:example schema=transports/a2a_message def=message_request direction=request -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [
        {
          "text": "adicione um Pixel 10 Pro ao meu checkout"
        }
      ],
      "messageId": "69da8f87-991b-479e-80dc-ed92fcb57cbe",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```

### Solicitação estruturada

A extensão aceita uma intenção estruturada quando a plataforma já interpretou a
ação do usuário. O vocabulário de `action` descreve a intenção do agente e não
substitui o schema BCP do checkout.

<!-- ucp:example schema=transports/a2a_message def=message_request direction=request -->
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [
        {
          "data": {
            "action": "add_to_checkout",
            "product_id": "PIXEL-10-PRO",
            "quantity": 1
          },
          "mediaType": "application/json"
        }
      ],
      "messageId": "e94a8c10-69f4-4c4c-b988-21a298302da6",
      "contextId": "aad14abc-4082-4748-84ca-4afff85aedfa",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```

### Resposta

`SendMessageResponse` contém exatamente um de `message` ou `task`. Para uma
resposta direta, o checkout fica em `result.message.parts`.

<!-- ucp:example schema=transports/a2a_message def=message_response -->
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "message": {
      "contextId": "aad14abc-4082-4748-84ca-4afff85aedfa",
      "messageId": "8e8566e0-6d7c-4f29-bd90-26a132385baa",
      "parts": [
        {
          "data": {
            "a2a.bcp.checkout": {
              "ucp": {
                "version": "{{ bcp_schema_version }}",
                "payment_handlers": {}
              },
              "id": "checkout_abc123",
              "line_items": [
                {
                  "id": "line_1",
                  "item": {
                    "id": "PIXEL-10-PRO",
                    "title": "Pixel 10 Pro",
                    "price": 599900
                  },
                  "quantity": 1,
                  "totals": [
                    {"type": "subtotal", "amount": 599900}
                  ]
                }
              ],
              "status": "ready_for_complete",
              "currency": "BRL",
              "totals": [
                {"type": "subtotal", "amount": 599900},
                {"type": "total", "amount": 599900}
              ],
              "links": [
                {
                  "type": "terms_of_service",
                  "url": "https://example-business.com/terms"
                }
              ]
            }
          },
          "mediaType": "application/json"
        }
      ],
      "role": "ROLE_AGENT",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```

## Conclusão do checkout

Quando o usuário estiver pronto para pagar, `payment` deve ser enviado ao agente
comercial em `a2a.bcp.checkout.payment`. Sinais associados devem ser enviados em
`a2a.bcp.checkout.signals`.

Após a conclusão, o agente comercial deve retornar o checkout com `order`
contendo somente `id` e `permalink_url`, conforme `OrderConfirmation`.

O exemplo abaixo usa o manipulador padrão do BCP,
[`br.dev.bcp.pix`](pix-payment-handler.md#processamento). Como a cobrança
já foi gerada e exibida em uma resposta anterior de atualização de
checkout, a solicitação de conclusão referencia o instrumento apenas por
`id`/`handler_id`, sem reenviar a credencial — a confirmação de liquidação
chega à empresa por webhook do PSP. Para manipuladores baseados em
tokenização (cartão, carteiras digitais), a plataforma envia a credencial
adquirida diretamente neste passo; veja o
[Guia do manipulador de pagamentos](payment-handler-guide.md).

### Solicitação

<!-- ucp:example schema=transports/a2a_message def=message_request direction=request -->
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [
        {
          "data": {
            "action": "complete_checkout"
          },
          "mediaType": "application/json"
        },
        {
          "data": {
            "a2a.bcp.checkout.payment": {
              "instruments": [
                {
                  "id": "instr_1",
                  "handler_id": "pix_recebedor_001",
                  "type": "pix",
                  "selected": true
                }
              ]
            },
            "a2a.bcp.checkout.signals": {
              "br.dev.bcp.buyer_ip": "203.0.113.42",
              "br.dev.bcp.user_agent": "Mozilla/5.0 ..."
            }
          },
          "mediaType": "application/json"
        }
      ],
      "messageId": "fcdd5da7-e593-414c-aa1a-3208e0551ba7",
      "contextId": "aad14abc-4082-4748-84ca-4afff85aedfa",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```

### Resposta

<!-- ucp:example schema=transports/a2a_message def=message_response -->
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "message": {
      "contextId": "aad14abc-4082-4748-84ca-4afff85aedfa",
      "messageId": "322bd1db-390d-426a-9e32-326bad2474bc",
      "parts": [
        {
          "data": {
            "a2a.bcp.checkout": {
              "ucp": {
                "version": "{{ bcp_schema_version }}",
                "payment_handlers": {}
              },
              "id": "checkout_abc123",
              "line_items": [
                {
                  "id": "line_1",
                  "item": {
                    "id": "PIXEL-10-PRO",
                    "title": "Pixel 10 Pro",
                    "price": 599900
                  },
                  "quantity": 1,
                  "totals": [
                    {"type": "subtotal", "amount": 599900}
                  ]
                }
              ],
              "status": "completed",
              "currency": "BRL",
              "totals": [
                {"type": "subtotal", "amount": 599900},
                {"type": "total", "amount": 599900}
              ],
              "links": [
                {
                  "type": "terms_of_service",
                  "url": "https://example-business.com/terms"
                }
              ],
              "order": {
                "id": "order_abc123",
                "permalink_url": "https://example-business.com/orders/order_abc123"
              }
            }
          },
          "mediaType": "application/json"
        }
      ],
      "role": "ROLE_AGENT",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```

## Conclusão com AP2

Agentes comerciais podem implementar a extensão de mandatos AP2 para trocar
intenções e autorizações de pagamento. O suporte deve ser negociado nos perfis
BCP e anunciado nos Agent Cards das duas partes.

Quando AP2 estiver ativo, o agente comercial deve assinar o checkout com ES256 e
retornar um JWS com payload destacado (detached) em `ap2.merchant_authorization`. A
assinatura cobre o checkout sem o membro `ap2`, canonizado com JCS conforme a
RFC 8785. Os detalhes de geração e verificação estão na
[extensão de mandatos AP2](ap2-mandates.md).

<!-- ucp:example schema=transports/a2a_message def=message_response -->
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "message": {
      "contextId": "aad14abc-4082-4748-84ca-4afff85aedfa",
      "messageId": "47694e9e-aeda-4e73-9f2e-caa903e9bfdf",
      "parts": [
        {
          "data": {
            "a2a.bcp.checkout": {
              "ucp": {
                "version": "{{ bcp_schema_version }}",
                "payment_handlers": {}
              },
              "id": "checkout_abc123",
              "line_items": [
                {
                  "id": "line_1",
                  "item": {
                    "id": "PIXEL-10-PRO",
                    "title": "Pixel 10 Pro",
                    "price": 599900
                  },
                  "quantity": 1,
                  "totals": [
                    {"type": "subtotal", "amount": 599900}
                  ]
                }
              ],
              "status": "ready_for_complete",
              "currency": "BRL",
              "totals": [
                {"type": "subtotal", "amount": 599900},
                {"type": "total", "amount": 599900}
              ],
              "links": [
                {
                  "type": "terms_of_service",
                  "url": "https://example-business.com/terms"
                }
              ],
              "ap2": {
                "merchant_authorization": "eyJhbGciOiJFUzI1NiIsImtpZCI6Im1lcmNoYW50XzIwMjYifQ..c2lnbmF0dXJl"
              }
            }
          },
          "mediaType": "application/json"
        }
      ],
      "role": "ROLE_AGENT",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```

Quando o usuário confirmar o pagamento, a plataforma deve enviar o pagamento em
`a2a.bcp.checkout.payment` e o mandato de checkout em
`ap2.checkout_mandate`. O mandato de pagamento fica em
`payment.instruments[*].credential.token`, conforme a extensão AP2.

### Solicitação

<!-- ucp:example schema=transports/a2a_message def=message_request direction=request -->
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [
        {
          "data": {
            "action": "complete_checkout"
          },
          "mediaType": "application/json"
        },
        {
          "data": {
            "a2a.bcp.checkout.payment": {
              "instruments": [
                {
                  "id": "instr_1",
                  "handler_id": "gpay",
                  "type": "card",
                  "selected": true,
                  "billing_address": {
                    "street_address": "Avenida Paulista, 1000",
                    "address_locality": "São Paulo",
                    "address_region": "SP",
                    "address_country": "BR",
                    "postal_code": "01310-100"
                  },
                  "credential": {
                    "type": "PAYMENT_GATEWAY",
                    "token": "examplePaymentMethodToken"
                  }
                }
              ]
            },
            "ap2": {
              "checkout_mandate": "eyJhbGciOiJFUzI1NiIsInR5cCI6InZjK3NkLWp3dCJ9.e30.c2lnbmF0dXJl"
            }
          },
          "mediaType": "application/json"
        }
      ],
      "messageId": "18746922-563a-4c60-bc22-3c10a8629139",
      "contextId": "aad14abc-4082-4748-84ca-4afff85aedfa",
      "extensions": [
        "https://bcp.dev.br/{{ bcp_version }}/specification/reference"
      ]
    }
  }
}
```
