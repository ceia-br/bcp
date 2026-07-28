# Extensão Tax

`br.dev.bcp.shopping.tax` · estende `checkout` e `order`

## Visão geral

Carrega o detalhamento tributário brasileiro na transação: por item, o tipo do
tributo, a alíquota, a base de cálculo, o valor e o nível federativo de destino,
além da classificação fiscal do produto (NCM). Atende a transparência
de preço da Lei 12.741/2012 ("De Olho no Imposto") e do CDC art. 31.

O vocabulário de tipos de tributo é **aberto** de propósito: a transição da
Reforma Tributária (2026–2033) muda a composição ano a ano (ICMS/ISS/DIFAL
saindo; IBS/CBS/IS entrando), e um enum fechado quebraria o schema a cada
virada.

O campo `authority` expõe o **nível federativo** que cada tributo financia
(`federal`, `state`, `municipal`), para o consumidor enxergar quanto vai a cada
nível, como pede a transparência de preço (Lei 12.741/2012). São as três esferas
que a lei reconhece — não há um quarto nível a inventar. O IBS, embora seja um
tributo só, é **partilhado** entre estado e município com alíquotas próprias
(a calculadora da RFB devolve `gIBSUF` e `gIBSMun` separados, e a NF-e os destaca
em grupos distintos): ele entra como **duas entradas**, `state` e `municipal`,
cada uma com sua alíquota e seu valor. A mesma separabilidade serve de base ao
split payment do IBS/CBS na liquidação (LC 214/2025, a partir de 2027).

O campo `behavior` diz **onde o valor mora na aritmética do preço**: `inclusive`
quando o tributo já está contido no preço do item (ICMS, que é calculado "por
dentro" — LC 87/96 art. 13, §1º, I) e `exclusive` quando é cobrado por cima dele.
Sem essa distinção, `subtotal + Σtaxes` não reconcilia com `total`, e um agente
que somar os tributos ao subtotal superfatura a oferta. A transição torna isso
inescapável: entre 2026 e 2032 **o mesmo item carrega tributo dos dois sistemas**
— o ICMS por dentro do preço e o IBS/CBS calculados por fora (LC 214/2025 art. 12,
que os exclui da própria base) —, e só o vendedor sabe qual é qual.

Numa venda ao consumidor os preços são anunciados com tributo embutido (CDC
art. 31), então o normal no protocolo é `inclusive`, inclusive para IBS/CBS: o
vendedor faz o *gross-up* ao precificar, e a `base` da incidência fica **abaixo**
do preço do item. Daí `base` poder divergir de `price` sem que isso seja erro.

> **2026 é ano de teste.** As alíquotas de CBS (0,9%) e IBS (0,1%) são de ensaio:
> o destaque no documento fiscal é obrigatório, mas o recolhimento é dispensado
> para quem cumprir as obrigações acessórias, e o valor é compensável com
> PIS/Cofins — a carga não sobe ([RFB, Orientações 2026][rfb-2026]). O tributo
> aparece no protocolo, com `behavior: inclusive`, e o total ao consumidor não muda.

[rfb-2026]: https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-consumo/orientacoes-2026

## Descoberta

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

A capacidade não declara `config` de perfil: o cálculo roda atrás do port da
calculadora da RFB (config interna do vendedor) e o regime tributário, quando
relevante, é atributo de identidade do vendedor (AgentFacts), não do imposto.

## Composição de schema

- `checkout.line_items[]` e `order.line_items[]` → estendidos com `ncm` e
  `taxes[]` (composição sobre `types/line_item.json` e
  `types/order_line_item.json`).
- O total de tributos usa a categoria `tax` que o core **já suporta** em
  `totals` — a extensão não cria lugar novo, torna obrigatório o preenchimento
  (regra normativa 1).
- Schema: `schemas/shopping/tax.json`.

## Campos

### `tax_detail` (entradas de `line_item.taxes[]`)

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `type` | string (aberta) | sim | `icms`, `icms_st`, `difal`, `fcp`, `iss`, `ipi`, `pis`, `cofins` (sistema atual); `ibs`, `cbs`, `is` (Reforma) |
| `rate` | number | não | Alíquota como fração decimal (0.009 = 0,9%). Indicativa: quem manda é o `amount` |
| `base` | integer | não | Base de cálculo em centavos. Pode ser menor que o preço do item (tributo por fora dentro de preço com tributo embutido) |
| `amount` | integer | sim | Valor do tributo em centavos |
| `authority` | string (aberta) | não | `federal`, `state`, `municipal`. IBS entra como duas entradas (estado + município) |
| `behavior` | string (aberta) | **sim** | `inclusive` (já contido no preço) ou `exclusive` (cobrado por cima) |

### Campos novos no line item

| Campo | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `ncm` | string (8 dígitos) | não | Classificação fiscal Mercosul; insumo do cálculo, do Imposto Seletivo e da NF-e |
| `taxes` | array de `tax_detail` | não | Uma entrada por incidência |

## Regras normativas

1. Com a capacidade ativa, toda resposta de checkout e de pedido **DEVE**
   incluir ao menos uma linha de categoria `tax` em `totals`, com o valor
   aproximado do total de tributos (Lei 12.741/2012). A regra é normativa da
   especificação — não é expressa como constraint de JSON Schema para manter a
   geração de código limpa. Como o schema não a alcança, quem a faz valer é o
   binding (`bcp_infra/tax/bcp_mapping.py`), que falha rápido se a quote tem
   tributo e o total não tem a linha `tax`.
2. Preços apresentados ao consumidor **DEVEM** já incluir tributos (CDC art. 31).
3. Clientes **DEVEM** tolerar tipos de tributo desconhecidos (transição da Reforma).
4. Clientes **NÃO DEVEM** somar ao subtotal entradas com `behavior: inclusive`
   (elas já estão no preço), nem recomputar o `amount` a partir de `base × rate`
   (a alíquota é indicativa; o arredondamento é do vendedor).

## Exemplo (resposta de checkout, trecho)

```json
{
  "line_items": [
    {
      "id": "li_1",
      "item": { "id": "prod_1", "title": "Vaso de cerâmica", "price": 10000 },
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
    { "type": "tax", "display_text": "Tributos (Lei 12.741/2012)", "amount": 100 },
    { "type": "total", "amount": 10000 }
  ]
}
```
