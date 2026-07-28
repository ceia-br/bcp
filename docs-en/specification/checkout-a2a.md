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

# Checkout capability: A2A binding

This document specifies the
[Agent2Agent Protocol 1.0](https://a2a-protocol.org/latest/specification/)
binding for the [Checkout capability](checkout.md). The binding uses JSON-RPC
2.0 over HTTP and the A2A 1.0 ProtoJSON models.

## Transport discovery

Businesses that support A2A must advertise the Agent Card endpoint in
`services` in the BCP profile published at `/.well-known/bcp`. The Agent Card is
a separate A2A document published at the address advertised by the profile.

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

The Agent Card declares each endpoint, binding, and version combination in
`supportedInterfaces`. For this binding, `protocolBinding` is `JSONRPC` and
`protocolVersion` is `1.0`. The BCP extension is declared in
`capabilities.extensions`, as required by the A2A 1.0 model.

<!-- ucp:example schema=transports/a2a_message def=agent_card -->
```json
{
  "name": "Example business agent",
  "description": "Business agent with BCP checkout",
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
        "description": "Brazilian Commerce Protocol structured types",
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
      "name": "BCP checkout",
      "description": "Creates, updates, and completes BCP checkout sessions",
      "tags": ["commerce", "checkout", "bcp"]
    }
  ]
}
```

## Shopping agent profile advertisement

Shopping platforms must send their BCP profile URI in `BCP-Agent` on every
request. The profile may be published at any stable URI controlled by the
platform.

The client must also select the A2A version and activate the BCP extension using
A2A service parameters. In the JSON-RPC binding, these parameters are HTTP
headers.

```http
BCP-Agent: profile="https://agent.example/profiles/v2026-07/shopping-agent.json"
A2A-Version: 1.0
A2A-Extensions: https://bcp.dev.br/{{ bcp_version }}/specification/reference
Content-Type: application/json
```

| Header | Description |
| :-- | :-- |
| `BCP-Agent` | Shopping platform BCP profile URI. |
| `A2A-Version` | A2A version selected for the interface, `1.0`. |
| `A2A-Extensions` | Comma-separated list of activated extensions. |

The BCP A2A extension URI is
`https://bcp.dev.br/{{ bcp_version }}/specification/reference`.

## A2A interactions

Business agents may return a `Message` directly or create a `Task` when the
operation requires tracking. In both cases, BCP types are transported in a
`Part` whose `data` member contains the structured object.

In A2A 1.0, `Part` does not use `kind` or `type`. The presence of `text`,
`data`, `raw`, or `url` identifies the content. Messages carrying BCP data also
declare the URI in `extensions`.

The business agent generates `contextId`. The platform must reuse it on later
turns in the same conversation. If the response creates a `Task`, the platform
must also send `taskId` until the task ends. A terminal task does not accept new
messages, but the same `contextId` can start another task.

## Idempotency

Business agents must use `messageId`, created by the message sender, to detect
duplicate messages caused by platform retries.

## Checkout functionality

The Checkout capability lets consumers manage items in a session and complete
the purchase. The business agent typically integrates this capability with the
business checkout APIs.

The complete checkout returned by the business agent must appear in the
`a2a.bcp.checkout` member of a `Part.data` object.

### Natural-language request

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
          "text": "add a Pixel 10 Pro to my checkout"
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

### Structured request

The extension accepts a structured intent after the platform has interpreted
the user's action. The `action` vocabulary describes agent intent and does not
replace the BCP checkout schema.

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

### Response

`SendMessageResponse` contains exactly one of `message` or `task`. For a direct
response, the checkout is in `result.message.parts`.

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

## Checkout completion

When the user is ready to pay, `payment` must be sent to the business agent in
`a2a.bcp.checkout.payment`. Associated signals must be sent in
`a2a.bcp.checkout.signals`.

After completion, the business agent must return the checkout with `order`
containing only `id` and `permalink_url`, as defined by `OrderConfirmation`.

The example below uses BCP's default handler,
[`br.dev.bcp.pix`](pix-payment-handler.md#processing). Since the charge was
already generated and displayed in an earlier checkout update response, the
completion request references the instrument only by `id`/`handler_id`,
without resending the credential — settlement confirmation reaches the
business through the PSP's webhook. For tokenization-based handlers (card,
digital wallets), the platform sends the acquired credential directly at
this step; see the [Payment Handler Guide](payment-handler-guide.md).

### Request

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

### Response

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

## AP2-based completion

Business agents may implement the AP2 mandates extension to exchange payment
intent and authorization. Support must be negotiated in BCP profiles and
advertised in both parties' Agent Cards.

When AP2 is active, the business agent must sign the checkout with ES256 and
return a detached-content JWS in `ap2.merchant_authorization`. The signature
covers the checkout without the `ap2` member, canonicalized with JCS according
to RFC 8785. Generation and verification details are defined in the
[AP2 mandates extension](ap2-mandates.md).

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

When the user confirms payment, the platform must send the payment in
`a2a.bcp.checkout.payment` and the checkout mandate in
`ap2.checkout_mandate`. The payment mandate is placed in
`payment.instruments[*].credential.token`, as defined by the AP2 extension.

### Request

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
