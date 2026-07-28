# Tax Extension

`br.dev.bcp.shopping.tax` extends `checkout` and `order`.

## Overview

This extension carries the Brazilian tax breakdown in the transaction: per line
item, the tax type, rate, calculation base, amount, and destination federative
authority, plus the product's fiscal classification (NCM). It supports the
price-transparency requirements of Law 12,741/2012 ("De Olho no Imposto") and
Consumer Defense Code art. 31.

The tax type vocabulary is intentionally open. Brazil's 2026-2033 tax reform
changes the mix year over year (ICMS/ISS/DIFAL transitioning out; IBS/CBS/IS
transitioning in), and a closed enum would break the schema at every turn.

The `authority` field exposes the **federative level** each tax funds
(`federal`, `state`, `municipal`), so the consumer can see how much goes to
each level, as required by the price-transparency law (Law 12,741/2012).
These are the three spheres the law recognizes — there is no fourth level to
invent. IBS, although a single tax, is **split** between state and municipal
government with their own rates (the Federal Revenue calculator returns
`gIBSUF` and `gIBSMun` separately, and the NF-e breaks them out into distinct
groups): it is represented as **two entries**, `state` and `municipal`, each
with its own rate and amount. That same separability underlies IBS/CBS split
payment at settlement (LC 214/2025, from 2027).

The `behavior` field states **where the amount lives in the price
arithmetic**: `inclusive` when the tax is already contained in the item price
(ICMS, which is calculated "inside" the price — LC 87/96 art. 13, §1, I) and
`exclusive` when it is charged on top of it. Without this distinction,
`subtotal + Σtaxes` does not reconcile with `total`, and a consumer or agent
that adds the taxes to the subtotal overstates the price. The transition
makes this unavoidable: between 2026 and 2032 **the same item carries tax
from both systems** — ICMS inside the price and IBS/CBS calculated on top
(LC 214/2025 art. 12, which excludes them from their own base) — and only the
seller knows which is which.

In a consumer sale, prices are advertised with tax already included (Consumer
Defense Code art. 31), so the norm in the protocol is `inclusive`, including
for IBS/CBS: the seller grosses up the price at pricing time, and the
incidence `base` ends up **below** the item price. That is why `base` can
diverge from `price` without being an error.

> **2026 is a test year.** The CBS (0.9%) and IBS (0.1%) rates are trial
> rates: disclosure on the fiscal document is mandatory, but collection is
> waived for sellers that meet the accessory obligations, and the amount is
> offsettable against PIS/Cofins — the tax burden does not increase (Federal
> Revenue, 2026 Guidance). The tax appears in the protocol with
> `behavior: inclusive`, and the consumer-facing total does not change.

## Discovery

```json
{
  "capabilities": {
    "br.dev.bcp.shopping.tax": [
      {
        "version": "{{ bcp_schema_version }}",
        "extends": ["br.dev.bcp.shopping.checkout", "br.dev.bcp.shopping.order"],
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/tax",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/tax.json"
      }
    ]
  }
}
```

The capability does not declare profile `config`: calculation runs behind the
seller's Federal Revenue calculator port (internal seller configuration), and
the tax regime, where relevant, is a seller identity attribute (AgentFacts),
not a tax setting.

## Schema Composition

- `checkout.line_items[]` and `order.line_items[]` are extended with `ncm` and
  `taxes[]` (composed over `types/line_item.json` and
  `types/order_line_item.json`).
- Aggregated tax totals use the `tax` category the core **already supports**
  in `totals` — the extension does not create a new slot, it makes populating
  it mandatory (normative rule 1).
- Schema: `schemas/shopping/tax.json`.

## Fields

### `tax_detail` entries in `line_item.taxes[]`

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `type` | open string | Yes | `icms`, `icms_st`, `difal`, `fcp`, `iss`, `ipi`, `pis`, `cofins` (current system); `ibs`, `cbs`, `is` (Reform). |
| `rate` | number | No | Applied rate as a decimal fraction, such as `0.009` for 0.9%. Indicative only: `amount` is authoritative. |
| `base` | integer | No | Calculation base in minor currency units. May be lower than the item price (tax charged on top within a tax-inclusive price). |
| `amount` | integer | Yes | Tax amount in minor currency units. |
| `authority` | open string | No | `federal`, `state`, `municipal`. IBS is represented as two entries (state + municipal). |
| `behavior` | open string | **Yes** | `inclusive` (already contained in the price) or `exclusive` (charged on top). |

### New line item fields

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `ncm` | string (8 digits) | No | Mercosur fiscal classification; input to calculation, the Selective Tax, and the NF-e. |
| `taxes` | array of `tax_detail` | No | One entry per tax incidence. |

## Normative Rules

1. With this capability active, every checkout and order response **MUST**
   include at least one `tax`-category entry in `totals` with the approximate
   total tax amount (Law 12,741/2012). This rule is normative at the
   specification level — it is not expressed as a JSON Schema constraint, to
   keep code generation clean. Since the schema does not reach it, it is
   enforced by the binding (`bcp_infra/tax/bcp_mapping.py`), which fails fast
   if the quote carries tax but the total lacks the `tax` line.
2. Prices shown to consumers **MUST** already include taxes (Consumer Defense
   Code art. 31).
3. Clients **MUST** tolerate unknown tax `type` values (Reform transition).
4. Clients **MUST NOT** add entries with `behavior: inclusive` to the
   subtotal (they are already in the price), nor recompute `amount` from
   `base × rate` (the rate is indicative; rounding is the seller's).

## Example

Checkout response excerpt:

```json
{
  "line_items": [
    {
      "id": "li_1",
      "item": { "id": "prod_1", "title": "Ceramic vase", "price": 10000 },
      "quantity": 1,
      "ncm": "69120000",
      "taxes": [
        { "type": "cbs", "rate": 0.009, "base": 10000, "amount": 90, "authority": "federal", "behavior": "inclusive" },
        { "type": "ibs", "rate": 0.001, "base": 10000, "amount": 10, "authority": "state", "behavior": "inclusive" }
      ],
      "totals": [{ "type": "subtotal", "amount": 10000 }]
    }
  ],
  "totals": [
    { "type": "subtotal", "amount": 10000 },
    { "type": "tax", "display_text": "Taxes (Law 12,741/2012)", "amount": 100 },
    { "type": "total", "amount": 10000 }
  ]
}
```
