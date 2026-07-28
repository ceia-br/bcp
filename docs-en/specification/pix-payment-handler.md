# Pix Payment Handler

`br.dev.bcp.pix` version `{{ bcp_schema_version }}` uses schema
`schemas/handlers/pix/pix.json`.

## Overview

This handler models one-off Pix dynamic charges. The payee's PSP creates a fixed
amount dynamic charge; the payer pushes payment from any Pix-enabled financial
institution by scanning or copying the BR Code payload.

Pix reverses the usual card-handler flow. With cards, a platform often acquires a
credential and submits it to the business. With Pix, the charge is created by the
business side through its PSP and returned in the checkout response for display.
Settlement confirmation reaches the business through the PSP webhook.

This handler is limited to one-off charges. Recurring Pix or Open Finance payment
initiation requires a separate handler.

## Participants

| Participant | Role |
| :---------- | :--- |
| **Payer** | Pays in their bank app by scanning or copying the Pix payload. |
| **Platform** | Discovers the handler, selects Pix, and displays the charge. |
| **Business** | Creates the charge through its PSP, receives settlement notifications, and reconciles. |
| **Payee PSP** | Issues the dynamic charge and notifies the business after settlement. |

## Prerequisites

- **Business**: contracts a payee PSP and stores provider API credentials in its
  backend. PSP credentials never travel in discovery or response payloads.
- **Platform**: no PSP onboarding is required. The platform only needs to support
  displaying the returned Pix charge.

## Handler Declaration

Business discovery declaration:

```json
{
  "payment_handlers": {
    "br.dev.bcp.pix": [
      {
        "id": "pix_recebedor_001",
        "version": "{{ bcp_schema_version }}",
        "available_instruments": [{ "type": "pix" }],
        "config": {
          "environment": "production"
        }
      }
    ]
  }
}
```

Platform declaration:

```json
{
  "id": "pix_platform_001",
  "version": "{{ bcp_schema_version }}",
  "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/pix-payment-handler",
  "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/handlers/pix/pix.json",
  "available_instruments": [{ "type": "pix" }],
  "config": { "environment": "production", "platform_id": "plat_abc" }
}
```

Response declarations carry runtime configuration. The actual charge travels as
a `pix_payment_instrument` in `payment.instruments`.

## Instrument Acquisition

1. The platform selects Pix during checkout.
2. The business calls its PSP to create a dynamic charge for the checkout total.
3. The PSP returns `provider_payment_id`, `copia_e_cola`, and `expires_at`.
4. The business returns a Pix payment instrument with credential type
   `pix_charge`.
5. The platform displays the QR or copy-and-paste payload until `expires_at`.

The `copia_e_cola` payload is a BR Code (EMV) payload that already encodes payee
and amount. Reconciliation uses `provider_payment_id`.

## Processing

1. The payer completes the Pix in their bank app.
2. The Pix network settles to the payee PSP.
3. The PSP notifies the business by webhook.
4. The business verifies the binding and amount before accepting settlement.
5. The order advances after settlement confirmation.

### Error Mapping

| Situation | Suggested `error_code` |
| :-------- | :--------------------- |
| Charge expired without payment | `payment_expired` |
| Settled amount mismatch or generic failure | `payment_failed` |
| Payee PSP unavailable | `processor_unavailable` |

Refund state is represented by the returns capability, not by this handler.

## Security

- The credential can include `binding` to associate the Pix charge with the
  checkout and payee identity.
- PSP API credentials stay in the business backend and never enter discovery,
  schema, or response payloads.
- Platforms **MUST NOT** present a charge after `expires_at`.
