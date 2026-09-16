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
# Order Capability - MCP Binding

This document specifies the Model Context Protocol (MCP) binding for the
[Order Capability](order.md).

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

### Request Metadata

MCP clients **MUST** include a `meta` object in every request containing
protocol metadata:

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

The `meta["ucp-agent"]` field is **required** on all requests to enable
[capability negotiation](overview.md#negotiation-protocol). Platforms **MAY**
include additional metadata fields.

## Tools

BCP Capabilities map 1:1 to MCP Tools.

| Tool | Operation | Description |
| :---- | :---- | :---- |
| `get_order` | [Get Order](order.md#get-order) | Get the current state of an order. |

### `get_order`

Maps to the [Get Order](order.md#get-order) operation. Returns the
current-state snapshot of an order.

#### Input Schema

* `meta` (Object, required): Request metadata with `ucp-agent.profile`.
* `id` (String, required): The ID of the order.

#### Output Schema

{{ schema_fields('order', 'order') }}

#### Example

=== "Request"

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

=== "Response"

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
                "description": "Delivered"
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
                "description": "Delivered to front door"
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

=== "Not Authorized"

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

## Error Handling

When the business cannot return an order, the response includes a `messages`
array describing the outcome. Platforms **MUST** check `messages` before
accessing order fields.

## Conformance

Platforms implementing the MCP binding:

* **MUST** include `meta.ucp-agent.profile` on all requests
* **MUST** check the `messages` array in responses before accessing order data
* **SHOULD** delegate to the business via `permalink_url` for the authoritative
  order experience - the business site is the source of truth for order details
  and post-purchase operations

Businesses implementing the MCP binding:

* **MUST** implement the `get_order` tool per the
  [OpenRPC schema](https://bcp.dev.br/services/shopping/mcp.openrpc.json)

See [Order Capability - Guidelines](order.md#operations-guidelines) for
capability-level requirements that apply across all transports.
