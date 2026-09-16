# Fiscal Identity Extension

`br.dev.bcp.shopping.fiscal_identity` extends `checkout` and `order`.

## Overview

This extension carries the fiscal identity of both parties in a Brazilian
transaction:

- **Buyer**: CPF or CNPJ in `buyer.taxpayer_id`, used when an identified NF-e must be
  issued.
- **Seller**: CNPJ, legal name, and address in `seller_identity`, required for
  consumer-facing offers, pre-closing summaries, and receipts under Brazilian
  consumer law.

The seller identity lives inside the transaction payload, not only in the
discovery profile, because signed checkouts and orders are the durable purchase
records. Profiles are mutable and may not be shown to the consumer. Freezing the
seller identity in the transaction binds the offer to that CNPJ at that moment.

## Discovery

Businesses declare the capability in the profile (`/.well-known/bcp`). The
declaration `config` MAY carry static seller identity data used as an onboarding
validation baseline:

```json
{
  "capabilities": {
    "br.dev.bcp.shopping.fiscal_identity": [
      {
        "version": "{{ bcp_schema_version }}",
        "extends": ["br.dev.bcp.shopping.checkout", "br.dev.bcp.shopping.order"],
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fiscal-identity",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fiscal_identity.json"
      }
    ]
  }
}
```

## Schema Composition

- `checkout.buyer` is extended with `taxpayer_id`.
- `checkout.seller_identity` and `order.seller_identity` are top-level objects
  required in every response while the capability is active.
- Schema: `schemas/shopping/fiscal_identity.json`.

## Fields

### `taxpayer_id` on `buyer`

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `kind` | closed enum | Yes | `cpf` (natural person), `cnpj` (legal entity), or `id_estrangeiro` (buyer without CPF/CNPJ). |
| `value` | string | Yes | Punctuation-free: 11 digits for CPF, 14 for CNPJ (alphanumeric from 2026), free-form for `id_estrangeiro`. |

### `seller_identity` on `checkout` and `order`

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `cnpj` | string | Yes | Seller CNPJ, 14 digits, identifying the invoice issuer. |
| `legal_name` | string | Yes | Seller legal name. |
| `address` | `postal_address` | No | Physical address for consumer disclosure. |

## Normative Rules

1. `seller_identity` **MUST** be present in every checkout and order response
   while this capability is active.
2. Buyer agents **MUST** present the seller CNPJ and legal name to the consumer
   before completion and on the receipt.
3. `buyer.taxpayer_id` **MUST** be collected by `complete` when the sale requires an
   identified NF-e. See [NF-e](nfe.md).

## Example

Checkout response excerpt:

```json
{
  "id": "chk_123",
  "buyer": {
    "first_name": "Ana",
    "taxpayer_id": { "kind": "cpf", "value": "39053344705" }
  },
  "seller_identity": {
    "cnpj": "19131243000197",
    "legal_name": "Loja Exemplo Comercio de Artesanato Ltda"
  }
}
```
