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
# Cart Capability - MCP Binding

This document specifies the Model Context Protocol (MCP) binding for the
[Cart Capability](cart.md).

## Protocol Fundamentals

### Discovery

Businesses advertise MCP transport availability through their BCP profile at
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

### Request Metadata

MCP clients **MUST** include a `meta` object in every request containing
protocol metadata:

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

The `meta["ucp-agent"]` field is **required** on all requests to enable
[capability negotiation](overview.md#negotiation-protocol). Platforms **MAY**
include additional metadata fields.

## Tools

BCP Capabilities map 1:1 to MCP Tools.

### Identifier Pattern

MCP tools separate resource identification from payload data:

* **Requests:** For operations on existing carts (`get`, `update`, `cancel`),
    a top-level `id` parameter identifies the target resource. The `cart`
    object in the request payload **MUST NOT** contain an `id` field.
* **Responses:** All responses include `cart.id` as part of the full resource state.
* **Create:** The `create_cart` operation does not require an `id` in the
    request, and the response includes the newly assigned `cart.id`.

| Tool | Operation | Description |
| :---- | :---- | :---- |
| `create_cart` | [Create Cart](cart.md#create-cart) | Create a cart session. |
| `get_cart` | [Get Cart](cart.md#get-cart) | Get a cart session. |
| `update_cart` | [Update Cart](cart.md#update-cart) | Update a cart session. |
| `cancel_cart` | [Cancel Cart](cart.md#cancel-cart) | Cancel a cart session. |

### `create_cart`

Maps to the [Create Cart](cart.md#create-cart) operation.

#### Input Schema

{{ schema_fields('cart_create_req', 'cart') }}

#### Output Schema

{{ schema_fields('cart_resp', 'cart') }}

#### Example

=== "Request"

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

=== "Response"

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

=== "Error Response"

    All items out of stock — no cart resource is created:

    <!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result.structuredContent -->
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

Maps to the [Get Cart](cart.md#get-cart) operation.

#### Input Schema

* `id` (String, required): The ID of the cart session.

#### Output Schema

{{ schema_fields('cart_resp', 'cart') }}

#### Example

=== "Request"

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

=== "Response"

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

=== "Not Found"

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

Maps to the [Update Cart](cart.md#update-cart) operation.

#### Input Schema

* `id` (String, required): The ID of the cart session to update.

{{ schema_fields('cart_update_req', 'cart') }}

#### Output Schema

{{ schema_fields('cart_resp', 'cart') }}

#### Example

=== "Request"

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

=== "Response"

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

Maps to the [Cancel Cart](cart.md#cancel-cart) operation.

#### Input Schema

* `id` (String, required): The ID of the cart session.

#### Output Schema

{{ schema_fields('cart_resp', 'cart') }}

#### Example

=== "Request"

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

=== "Response"

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

## Error Handling

BCP distinguishes between protocol errors and business outcomes. See the
[Core Specification](overview.md#error-handling) for the complete error code
registry and transport binding examples.

* **Protocol errors**: Transport-level failures (authentication, rate limiting,
    unavailability) that prevent request processing. Returned as JSON-RPC
    `error` with code `-32000` (or `-32001` for discovery errors).
* **Business outcomes**: Application-level results from successful request
    processing, returned as JSON-RPC `result` with BCP envelope and `messages`.

### Business Outcomes

Business outcomes (including not found and validation errors) are returned as
JSON-RPC `result` with `structuredContent` containing the BCP envelope and
`messages`:

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

## Conformance

A conforming MCP transport implementation **MUST**:

1. Implement JSON-RPC 2.0 protocol correctly.
2. Provide all core cart tools defined in this specification.
3. Return errors per the [Core Specification](overview.md#error-handling).
4. Return business outcomes as JSON-RPC `result` with BCP envelope and
    `messages` array.
5. Validate tool inputs against BCP schemas.
6. Support HTTP transport with streaming.
