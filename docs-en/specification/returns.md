# Returns Extension

`br.dev.bcp.shopping.returns` extends `order` and declares return policy in the
business profile.

## Overview

This extension covers Brazilian distance-commerce returns in two parts:

- **Policy in the discovery profile**: withdrawal period and request channel,
  so the consumer can see return rights before checkout completion.
- **Return record on the order**: BCP already models post-sale changes as order
  `adjustments[]`; this extension adds return reason, legal deadlines, and
  reverse logistics fields.

The seven-day withdrawal period starts at confirmed delivery, represented by the
existing `delivered` fulfillment event.

## Discovery

```json
{
  "capabilities": {
    "br.dev.bcp.shopping.returns": [
      {
        "version": "{{ bcp_schema_version }}",
        "extends": "br.dev.bcp.shopping.order",
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/returns",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/returns.json",
        "config": {
          "withdrawal_period_days": 7,
          "request_channel": "https://loja.example.com.br/devolucoes"
        }
      }
    ]
  }
}
```

## Schema Composition

- `order.adjustments[]` entries are extended for return-specific data.
- Policy config is defined by `schemas/shopping/types/returns_config.json`.
- Schema: `schemas/shopping/returns.json`.

## Fields

### Policy `config`

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `withdrawal_period_days` | integer | No | Withdrawal period in calendar days, minimum 7, counted from confirmed delivery. |
| `request_channel` | string | No | Channel used to request returns; should include the purchase channel. |

### Return adjustment fields

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `reason` | open string | No | Suggested values: `withdrawal`, `defect`, `wrong_product`. |
| `acknowledged_at` | date-time | No | When the seller acknowledged the request. |
| `reverse_shipping_code` | string | No | Reverse shipping/posting code. |
| `carrier` | string | No | Carrier handling the reverse flow. |
| `deadline` | date-time | No | Deadline for the consumer to ship the product back. |

### Refund adjustment fields

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `totals[].amount` | integer | Yes | Always negative; represents money returned to the buyer. |

### Fields on any order adjustment

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `related_adjustment_ids` | array of strings | No | Ids of causally related adjustments. A refund caused by a return references the return adjustment here. |

## Normative Rules

1. The withdrawal right **MUST** be disclosed before completion; policy `config`
   is the protocol source for that disclosure.
2. BCP transactions are distance-commerce transactions; withdrawal rules apply to
   all transactions unless a future extension scopes otherwise.
3. The seller **MUST** immediately acknowledge receipt of a withdrawal request. This
   acknowledgement cannot wait for posting, inspection, or physical receipt.
4. A withdrawal refund **MUST** be requested immediately and include every amount paid,
   including freight, as a separate refund adjustment related to the return.

## Relationship between return and refund

`return` represents the commercial and physical process; `refund` represents the financial
restitution. They have independent lifecycles, each with its own `status`, and are therefore
distinct adjustments. A refund caused by a return includes the return id in
`related_adjustment_ids`. Partial or multiple refunds are separate adjustments with negative
totals.

Refund execution data (PSP identifiers, settlement, mechanism used) **MUST NOT** travel in the
protocol. It is reconciliation between the business and its PSP, which delivers it through the
provider webhook as the `br.dev.bcp.pix` handler describes. The protocol carries the financial
event (type, status, amount, timing and causal link), not the execution mechanics.

## Example

Order response excerpt:

```json
{
  "id": "ord_789",
  "fulfillment": {
    "events": [
      {
        "id": "ev_9",
        "type": "delivered",
        "occurred_at": "2026-07-01T16:20:00-03:00",
        "line_items": [{ "id": "li_1", "quantity": 1 }]
      }
    ]
  },
  "adjustments": [
    {
      "id": "adj_1",
      "type": "return",
      "status": "pending",
      "occurred_at": "2026-07-03T10:00:00-03:00",
      "reason": "withdrawal",
      "acknowledged_at": "2026-07-03T10:04:00-03:00",
      "reverse_shipping_code": "BR123456789XX",
      "carrier": "Correios",
      "deadline": "2026-07-13T23:59:59-03:00",
      "line_items": [{ "id": "li_1", "quantity": -1 }]
    },
    {
      "id": "refund_1",
      "type": "refund",
      "status": "completed",
      "occurred_at": "2026-07-03T10:05:00-03:00",
      "related_adjustment_ids": ["adj_1"],
      "totals": [
        { "type": "refund", "display_text": "Full refund", "amount": -10000 }
      ]
    }
  ]
}
```

The return stays `pending` while the product travels back, and the refund is already
`completed`: the two lifecycles run in parallel. The refund carries no PSP identifier and no
settlement data, which belong to reconciliation between the business and its provider.
