# NF-e Extension

`br.dev.bcp.shopping.nfe` extends `order`.

## Overview

This extension carries an order-level reference to an issued Brazilian electronic
invoice (NF-e): access key, DANFE URL, authorized XML URL, and issue timestamp.
The invoice model and authorization protocol are already encoded in the access
key and XML, so they are not duplicated.

Only the reference travels on the wire. Buyer personal data remains in the
seller's fiscal systems, supporting LGPD data minimization while preserving the
seller's fiscal retention duties.

The block is optional in JSON Schema because the obligation to issue an NF-e
depends on seller regime and buyer type.

## Discovery

```json
{
  "capabilities": {
    "br.dev.bcp.shopping.nfe": [
      {
        "version": "{{ bcp_schema_version }}",
        "extends": "br.dev.bcp.shopping.order",
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/nfe",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/nfe.json"
      }
    ]
  }
}
```

## Schema Composition

- `order.nfe` is a new optional response-only object.
- Schema: `schemas/shopping/nfe.json`.

## Fields

| Field | Type | Required | Description |
| :---- | :--- | :------- | :---------- |
| `access_key` | string | Yes | 44-digit NF-e access key identifying the document at SEFAZ. |
| `danfe_url` | URI | No | Human-readable DANFE document, usually PDF. |
| `xml_url` | URI | No | Authorized XML document. |
| `issued_at` | date-time | No | Issue timestamp. |

## Normative Rules

1. When the seller is required to issue an NF-e, the order **MUST** receive the
   `nfe` block after document authorization.
2. The block **MUST NOT** carry buyer personal data. It carries only document
   references.
3. Issuance, signing, authorization, and bookkeeping are seller-side concerns
   outside the protocol wire format.

## Example

Order response excerpt:

```json
{
  "id": "ord_789",
  "nfe": {
    "access_key": "35260519131243000197550010000012341000012349",
    "danfe_url": "https://notas.example.com.br/danfe/12345.pdf",
    "xml_url": "https://notas.example.com.br/xml/12345.xml",
    "issued_at": "2026-07-03T14:30:00-03:00"
  }
}
```
