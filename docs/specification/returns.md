# Extensão de Devoluções

`br.dev.bcp.shopping.returns` estende `order` e declara política de devolução no
perfil empresarial.

## Visão geral

Esta extensão abrange os retornos do comércio à distância brasileiro em duas partes:

- **Política no perfil de descoberta**: prazo de retirada e canal de solicitação,
  para que o consumidor possa ver os direitos de devolução antes da finalização da compra.
- **Registro de devolução no pedido**: BCP já modela alterações pós-venda como pedido
  `adjustments[]`; esta extensão adiciona motivo de devolução, prazos legais e
  campos de logística reversa.

O período de retirada de sete dias começa na entrega confirmada, representada pelo
evento de cumprimento `delivered` existente.

## Descoberta

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

## Composição do esquema

- As entradas `order.adjustments[]` são estendidas para dados específicos de retorno.
- A configuração da política é definida por `schemas/shopping/types/returns_config.json`.
- Esquema: `schemas/shopping/returns.json`.

## Campos

### Política `config`

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `withdrawal_period_days` | inteiro | Não | Prazo de retirada em dias corridos, mínimo 7, contados da entrega confirmada. |
| `request_channel` | corda | Não | Canal utilizado para solicitar devoluções; deve incluir o canal de compra. |

### Campos de ajuste de retorno

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `reason` | corda aberta | Não | Valores sugeridos: `withdrawal`, `defect`, `wrong_product`. |
| `acknowledged_at` | data-hora | Não | Quando o vendedor reconheceu o pedido. |
| `reverse_shipping_code` | corda | Não | Código de envio/postagem reverso. |
| `carrier` | corda | Não | Transportadora cuidando do fluxo reverso. |
| `deadline` | data-hora | Não | Prazo para o consumidor devolver o produto. |

### Campos de ajuste de reembolso

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `totals[].amount` | inteiro | Sim | Sempre negativo; representa dinheiro devolvido ao comprador. |

### Campos de qualquer ajuste do pedido

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `related_adjustment_ids` | lista de cordas | Não | Ids de ajustes relacionados por causalidade. Um reembolso causado por uma devolução referencia aqui o ajuste de devolução. |

## Normas Normativas

1. O direito de retirada **DEVE** ser divulgado antes da conclusão; política `config`
   é a fonte do protocolo para essa divulgação.
2. As transações BCP são transações de comércio à distância; regras de retirada se aplicam a
   todas as transações, a menos que uma extensão futura tenha escopo diferente.
3. O vendedor **DEVE** confirmar imediatamente o recebimento da manifestação de
   arrependimento. A confirmação não pode aguardar postagem, inspeção ou recebimento físico.
4. O refund por arrependimento **DEVE** ser solicitado imediatamente e incluir todos os
   valores pagos, inclusive frete, em adjustment `refund` separado e relacionado ao return.

## Relação entre return e refund

`return` representa o processo comercial e físico; `refund`, a restituição financeira. Eles
possuem lifecycles independentes, cada um com seu próprio `status`, e por isso são ajustes
distintos. Um refund causado por um return inclui o id deste em `related_adjustment_ids`.
Refunds parciais ou múltiplos são ajustes separados, sempre com totais negativos.

Os dados de execução do reembolso (identificadores do PSP, liquidação, mecanismo usado)
**NÃO DEVEM** trafegar no protocolo. Eles são conciliação entre o vendedor e seu PSP, que
os recebe pelo webhook do provedor, conforme o handler `br.dev.bcp.pix` descreve. O
protocolo carrega o evento financeiro (tipo, status, valor, momento e vínculo causal),
não a mecânica de execução.

## Exemplo

Trecho da resposta do pedido:

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
        { "type": "refund", "display_text": "Reembolso integral", "amount": -10000 }
      ]
    }
  ]
}
```

A devolução segue `pending` enquanto o produto não volta, e o reembolso já está `completed`:
os dois ciclos correm em paralelo. O reembolso não carrega identificador de PSP nem dado de
liquidação, que ficam na conciliação entre o vendedor e seu provedor.
