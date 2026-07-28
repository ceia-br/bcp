# Extensão de Identidade Fiscal

`br.dev.bcp.shopping.fiscal_identity` estende `checkout` e `order`.

## Visão geral

Esta extensão carrega a identidade fiscal de ambas as partes em uma transação
brasileira:

- **Comprador**: CPF ou CNPJ em `buyer.tax_id`, utilizado quando uma NF-e identificada deve ser
  emitida.
- **Vendedor**: CNPJ, razão social e endereço em `seller_identity`, obrigatório para
  ofertas voltadas ao consumidor, resumos pré-fechamento e recibos no âmbito do
  direito do consumidor brasileiro.

A identidade do vendedor reside dentro da carga útil da transação, não apenas no
perfil de descoberta, porque checkouts e pedidos assinados são o registro durável
da compra. Perfis são mutáveis e não servem como prova estável para o consumidor.
Ao congelar a identidade do vendedor na transação, a oferta fica vinculada àquele
CNPJ naquele momento.

## Descoberta

As empresas declaram a capacidade no perfil (`/.well-known/bcp`). A
declaração `config` PODE transportar dados estáticos de identidade do vendedor usados como
linha de base de validação:

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

## Composição do esquema

- `checkout.buyer` é estendido com `tax_id`.
- `checkout.seller_identity` e `order.seller_identity` são objetos de nível superior
  exigidos em cada resposta enquanto o recurso estiver ativo.
- Esquema: `schemas/shopping/fiscal_identity.json`.

## Campos

### `tax_id` em `buyer`

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `kind` | string aberta | Sim | `cpf` para pessoas físicas ou `cnpj` para pessoas jurídicas. |
| `value` | string | Sim | Apenas dígitos: 11 para CPF ou 14 para CNPJ. |

### `seller_identity` em `checkout` e `order`

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `cnpj` | string | Sim | CNPJ do vendedor, 14 dígitos, identificando o emissor da nota fiscal. |
| `legal_name` | string | Sim | Razão social do vendedor. |
| `address` | `postal_address` | Não | Endereço físico para divulgação ao consumidor. |

## Regras normativas

1. `seller_identity` **DEVE** estar presente em todos os checkouts e respostas de pedidos
   enquanto esse recurso estiver ativo.
2. Os agentes compradores **DEVEM** apresentar o CNPJ e a razão social do vendedor ao consumidor
   antes da conclusão e no recebimento.
3. `buyer.tax_id` **DEVE** ser recolhido por `complete` quando a venda exigir um
   NF-e identificada. Veja [NF-e](nfe.md).

## Exemplo

Trecho da resposta de checkout:

```json
{
  "id": "chk_123",
  "buyer": {
    "first_name": "Ana",
    "tax_id": { "kind": "cpf", "value": "39053344705" }
  },
  "seller_identity": {
    "cnpj": "19131243000197",
    "legal_name": "Loja Exemplo Comercio de Artesanato Ltda"
  }
}
```
