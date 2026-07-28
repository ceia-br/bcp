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

# Extensão de desconto

## Visão geral

A extensão de desconto permite que as empresas indiquem que apoiam códigos de
desconto nas sessões de carrinho e checkout, e especifica como os códigos de desconto são
compartilhados entre a plataforma e o negócio.

**Principais recursos:**

- Envie um ou mais códigos de desconto
- Receba descontos aplicados com títulos e valores legíveis por humanos
- Códigos rejeitados comunicados via `messages[]` com códigos de erro detalhados
- Descontos automáticos coexistem com descontos baseados em código

**Dependências:**

- Capacidade de carrinho ou capacidade de checkout

## Descoberta

As empresas anunciam suporte a descontos em seus perfis. A capacidade pode
estender carrinho, checkout ou ambos:

<!-- ucp:example schema=profile def=business_schema extract=$.ucp.capabilities target=$.ucp.capabilities -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "capabilities": {
      "br.dev.bcp.shopping.discount": [
        {
          "version": "{{ bcp_schema_version }}",
          "extends": ["br.dev.bcp.shopping.cart", "br.dev.bcp.shopping.checkout"],
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/discount",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/discount.json"
        }
      ]
    }
  }
}
```

As empresas PODEM anunciar suporte a desconto apenas para carrinho, apenas para checkout ou
para ambos. As plataformas DEVEM verificar quais recursos são estendidos antes de enviar
códigos de desconto.

## Esquema

Quando esse recurso está ativo, o carrinho e/ou checkout são estendidos com um
objeto `discounts`.

### Objeto de descontos

{{ extension_schema_fields('discount.json#/$defs/discounts_object', 'discount') }}

### Desconto Aplicado

{{ extension_schema_fields('discount.json#/$defs/applied_discount', 'discount') }}

### Alocação

{{ extension_schema_fields('discount.json#/$defs/allocation', 'discount') }}

## Detalhes de alocação

A matriz `applied` explica como os descontos foram calculados e distribuídos.
O `applied[].amount` descreve a magnitude do desconto aplicado (sempre
positivo); o valor da entrada `totals[]` correspondente representa seu efeito, com
sinal, sobre o total (negativo para descontos).

### Método de alocação

O campo `method` indica como foi calculado o desconto:

| Método | Significado | Exemplo |
| -------- | --------------------------------------- | ------------------------------------------------ |
| `each` | Aplicado de forma independente por item elegível | “10% de desconto em cada item” → 10% × preço do item |
| `across` | Dividir proporcionalmente por valor | "Desconto de $ 10 no pedido" → item de $ 6 a $ 60, item de $ 4 a $ 40 |

### Ordem de empilhamento

Quando são aplicados descontos múltiplos, `priority` indica a ordem de cálculo.
Números mais baixos são aplicados primeiro:

```text
Cart: $100
Discount A (priority: 1): 20% off → $100 × 0.8 = $80
Discount B (priority: 2): $10 off → $80 - $10 = $70
```

A ordem é importante porque os descontos percentuais são compostos de forma diferente dependendo
quando eles são aplicados.

### Matriz de Alocações

A matriz `allocations` divide onde cada dólar de desconto foi parar, usando
JSONPath para identificar alvos:

| Padrão de caminho | Alvo |
| ------------------- | ---------------- |
| `$.line_items[0]` | Item de primeira linha |
| `$.line_items[1]` | Segunda linha |
| `$.totals.shipping` | Custos de envio |

Isso permite que as plataformas expliquem exatamente quanto cada desconto contribuiu para
cada item de linha, mesmo quando vários descontos se acumulam.

**Invariante:** Soma de `allocations[].amount` é igual a `applied_discount.amount`.

## Operações

Os códigos de desconto são enviados por meio das operações padrão de criação/atualização
de carrinho ou checkout. A mesma semântica se aplica a ambos os recursos.

**Solicitar comportamento:**

- **Semântica de substituição**: o envio de `discounts.codes` substitui quaisquer códigos enviados anteriormente
- **Limpar códigos**: Envie o array vazio `"codes": []` para remover todos os códigos de desconto
- **Não diferencia maiúsculas de minúsculas**: os códigos são correspondidos sem distinção entre maiúsculas e minúsculas por empresa

**Comportamento de resposta:**

- `discounts.applied` contém todos os descontos ativos (baseados em código + automáticos)
- Códigos rejeitados comunicados via `messages[]` (veja abaixo)
- Valores de desconto refletidos em `totals[]` e `line_items[].totals[]`

**Continuidade do carrinho até o checkout:** quando um carrinho é convertido em checkout por
meio do campo `cart_id` da capacidade do carrinho, as empresas DEVEM transferir quaisquer
códigos de desconto que foram aplicados ao carrinho. Códigos que não são mais válidos no
momento do checkout (por exemplo, expirado, inelegível) DEVEM ser comunicados via
`messages[]` usando códigos de rejeição padrão.

## Códigos rejeitados

Quando um código de desconto enviado não pode ser aplicado, as empresas comunicam isso
através da matriz `messages[]`:

<!-- ucp:example schema=shopping/cart target=$.messages -->
```json
[
  {
    "type": "warning",
    "code": "discount_code_expired",
    "path": "$.discounts.codes[0]",
    "content": "Code 'SUMMER20' expired on December 1st"
  }
]
```

> **Orientação de implementação:** Operações que afetam os totais dos pedidos ou a
> expectativa do usuário em relação ao total **DEVEM** usar `type: "warning"` para garantir
> que eles sejam apresentados ao usuário, em vez de manipulados silenciosamente pelas plataformas.
> Descontos rejeitados são um excelente exemplo: o usuário espera um desconto, mas não o
> recebe, por isso deve ser informado.

**Códigos de erro para descontos rejeitados:**

| Código | Descrição |
| -------------------------------------- | ------------------------------------------- |
| `discount_code_expired` | O código expirou |
| `discount_code_invalid` | Código não encontrado ou malformado |
| `discount_code_already_applied` | O código já está aplicado |
| `discount_code_combination_disallowed` | Não acumulável com outro desconto ativo |
| `discount_code_user_not_logged_in` | O código requer usuário autenticado |
| `discount_code_user_ineligible` | O usuário não atende aos critérios de elegibilidade |

## Descontos Automáticos

As empresas podem aplicar descontos automaticamente com base no conteúdo do carrinho, segmento
de cliente ou regras promocionais:

- Aparece em `discounts.applied` com `automatic: true` e sem campo `code`
- Aplicado sem ação de plataforma
- Não pode ser removido pela plataforma
- Apresentado para transparência (a plataforma pode explicar ao usuário por que o desconto foi aplicado)

## Reivindicações de elegibilidade

As reivindicações de elegibilidade são reivindicações do comprador sobre benefícios elegíveis (consulte
[Contexto](checkout.md#contexto)), como associação de fidelidade, vantagens de
instrumento de pagamento e similares. Quando a extensão de desconto está ativa, as
empresas que optarem por aceitar reivindicações de elegibilidade **DEVEM** revelar seu
efeito nos preços como descontos provisórios na matriz `applied`. Plataformas **DEVEM**
exibir descontos provisórios ao comprador.

### Comportamento de desconto

As plataformas enviam reclamações do comprador via `context.eligibility` nas
solicitações de carrinho ou checkout (consulte [Contexto](checkout.md#contexto)). Quando
uma empresa reconhece uma reivindicação que afeta o preço, ela **DEVE** apresentar um
desconto provisório correspondente na matriz `discounts.applied`. Isto dá à plataforma
atribuição estruturada para exibir ao comprador.

Os descontos acionados por elegibilidade usam os seguintes campos:

| Campo | Valor | Finalidade |
| ------------- | -------------------------- | --------------------------------------- |
| `automatic` | `true` | Nenhum código necessário |
| `provisional` | `true` | Requer verificação na conclusão |
| `eligibility` | `"com.example.store_card"` | A reivindicação aceita |
| `code` | *(omitido)* | Não baseado em código |

Os campos padrão `priority`, `method` e `allocations` aplicam-se ao empilhamento com
outros descontos.

### Verificação no checkout

Os descontos de reivindicações aceitas, mas não verificadas, são `provisional: true`.
Os descontos provisórios permanecem até que a reclamação seja verificada, rescindida ou
substituída durante a sessão. Na conclusão do checkout, todas as reivindicações
provisórias restantes **DEVEM** ser resolvidas (consulte
[Verificação de elegibilidade na conclusão](checkout.md#verificacao-de-elegibilidade-na-conclusao)).

### Exemplo: Desconto Provisório com Atribuição

Com base no exemplo do cartão da loja de
[Verificação de elegibilidade na conclusão](checkout.md#verificacao-de-elegibilidade-na-conclusao),
a extensão de desconto fornece atribuição estruturada. A plataforma reivindica um
benefício do cartão da loja; a empresa apresenta o desconto provisório com detalhes
completos de empilhamento e alocação:

=== "Solicitação"

    <!-- ucp:example schema=shopping/cart op=create direction=request -->
    ```json
    {
      "context": {
        "eligibility": ["com.example.store_card"]
      },
      "line_items": [
        {
          "item": {
            "id": "prod_shirt"
          },
          "quantity": 2
        }
      ]
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read -->
    ```json
    {
      "ucp": { ... },
      "id": "...",
      "currency": "...",
      "line_items": [ ... ],
      "discounts": {
        "applied": [
          {
            "title": "Store Card 5% Off",
            "amount": 250,
            "automatic": true,
            "provisional": true,
            "eligibility": "com.example.store_card",
            "priority": 1,
            "method": "each",
            "allocations": [
              {"path": "$.line_items[0]", "amount": 250}
            ]
          }
        ]
      },
      "totals": [
        {"type": "subtotal", "display_text": "Subtotal", "amount": 5000},
        {"type": "items_discount", "display_text": "Discounts", "amount": -250},
        {"type": "total", "display_text": "Total", "amount": 4750}
      ]
    }
    ```

A plataforma agora pode renderizar: "Cartão da loja com 5% de desconto: -$2,50 *(verificado em
compra)*" com total confiança na atribuição, valor e alocação.

## Impacto em itens de linha e totais

Os descontos aplicados são refletidos nos campos principais do carrinho ou checkout usando dois
tipos totais distintos:

| Tipo total | Quando usar |
| ---------------- | --------------------------------------------------------- |
| `items_discount` | Descontos atribuídos a itens de linha (`$.line_items[*]`) |
| `discount` | Descontos no nível do pedido (frete, taxas, valor fixo do pedido) |

**Determinando o tipo:** Se um desconto tiver `allocations` apontando para itens de
linha, contribui para `items_discount`. Descontos sem alocações, ou com alocações
para frete/taxas, contribuem para `discount`.

| Tipo de desconto | Onde refletido |
| -------------------- | ------------------------------------------ |
| Desconto em itens de linha | `line_items[].totals[type=items_discount]` |
| Desconto no nível do pedido | `totals[type=discount]` |

**Invariante:** `totals[type=items_discount].amount` é igual
`sum(line_items[].totals[type=items_discount].amount)`.

A matriz `discounts.applied` mostra **o que** foi aplicado. O `totals[]` e
`line_items[].totals[]` mostra **onde** e **quanto**.

**Convenção de valor:** Os valores de desconto em `discounts.applied` são inteiros
positivos (o valor do desconto). As entradas de desconto em `totals[]` são negativas
(o efeito no recibo) — o sinal é aplicado pelo esquema.

## Exemplos

### Carrinho com códigos de desconto

Códigos de desconto aplicados durante a exploração do carrinho. A resposta do carrinho inclui
valores estimados de desconto, dando ao comprador visibilidade sobre a economia antes de
prosseguir para o checkout.

=== "Solicitação"

    <!-- ucp:example schema=shopping/cart op=create direction=request -->
    ```json
    {
      "line_items": [
        {
          "item": {
            "id": "prod_1"
          },
          "quantity": 2
        }
      ],
      "discounts": {
        "codes": ["SUMMER20"]
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read -->
    ```json
    {
      "ucp": { ... },
      "id": "cart_abc123",
      "currency": "BRL",
      "line_items": [
        {
          "id": "li_1",
          "item": {
            "id": "prod_1",
            "title": "T-Shirt",
            "price": 2000
          },
          "quantity": 2,
          "totals": [
            {"type": "subtotal", "amount": 4000},
            {"type": "items_discount", "amount": -800},
            {"type": "total", "amount": 3200}
          ]
        }
      ],
      "discounts": {
        "codes": ["SUMMER20"],
        "applied": [
          {
            "code": "SUMMER20",
            "title": "Summer Sale 20% Off",
            "amount": 800,
            "method": "each",
            "allocations": [
              {"path": "$.line_items[0]", "amount": 800}
            ]
          }
        ]
      },
      "totals": [
        {"type": "subtotal", "display_text": "Subtotal", "amount": 4000},
        {"type": "items_discount", "display_text": "Item Discounts", "amount": -800},
        {"type": "total", "display_text": "Estimated Total", "amount": 3200}
      ]
    }
    ```

### Desconto no nível do pedido

Um desconto fixo aplicado ao total do pedido. Sem alocações – o desconto se aplica
ao pedido como um todo e utiliza `type: "discount"` nos totais.

=== "Solicitação"

    <!-- ucp:example schema=shopping/cart op=update direction=request -->
    ```json
    {
      "id": "...",
      "line_items": [ ... ],
      "discounts": {
        "codes": ["SAVE10"]
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read -->
    ```json
    {
      "ucp": { ... },
      "id": "...",
      "currency": "...",
      "line_items": [ ... ],
      "discounts": {
        "codes": ["SAVE10"],
        "applied": [
          {
            "code": "SAVE10",
            "title": "$10 Off Your Order",
            "amount": 1000
          }
        ]
      },
      "totals": [
        {"type": "subtotal", "display_text": "Subtotal", "amount": 5000},
        {"type": "discount", "display_text": "Order Discount", "amount": -1000},
        {"type": "total", "display_text": "Total", "amount": 4000}
      ]
    }
    ```

### Descontos mistos (item + nível do pedido)

Este exemplo mostra os dois tipos de desconto: um desconto por item (20% de desconto) alocado
para itens de linha e um desconto de frete automático no nível do pedido.

=== "Solicitação"

    <!-- ucp:example schema=shopping/cart op=update direction=request -->
    ```json
    {
      "id": "...",
      "line_items": [ ... ],
      "discounts": {
        "codes": ["SUMMER20"]
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read -->
    ```json
    {
      "ucp": { ... },
      "id": "...",
      "currency": "...",
      "line_items": [
        {
          "id": "li_1",
          "item": {
            "id": "prod_1",
            "title": "T-Shirt",
            "price": 2000
          },
          "quantity": 2,
          "totals": [
            {"type": "subtotal", "amount": 4000},
            {"type": "items_discount", "amount": -800},
            {"type": "total", "amount": 3200}
          ]
        }
      ],
      "discounts": {
        "codes": ["SUMMER20"],
        "applied": [
          {
            "code": "SUMMER20",
            "title": "Summer Sale 20% Off",
            "amount": 800,
            "allocations": [
              {"path": "$.line_items[0]", "amount": 800}
            ]
          },
          {
            "title": "Free shipping on orders over $30",
            "amount": 599,
            "automatic": true
          }
        ]
      },
      "totals": [
        {"type": "subtotal", "display_text": "Subtotal", "amount": 4000},
        {"type": "items_discount", "display_text": "Item Discounts", "amount": -800},
        {"type": "discount", "display_text": "Order Discounts", "amount": -599},
        {"type": "fulfillment", "display_text": "Shipping", "amount": 0},
        {"type": "total", "display_text": "Total", "amount": 2601}
      ]
    }
    ```

### Código de desconto rejeitado

Quando não for possível aplicar um código de desconto, a rejeição é comunicada através da
matriz `messages[]`. O código ainda aparece em `discounts.codes` (ecoado de volta)
mas não em `discounts.applied`.

=== "Solicitação"

    <!-- ucp:example schema=shopping/cart op=update direction=request -->
    ```json
    {
      "id": "...",
      "line_items": [ ... ],
      "discounts": {
        "codes": ["SAVE10", "EXPIRED50"]
      }
    }
    ```

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read -->
    ```json
    {
      "ucp": { ... },
      "id": "...",
      "currency": "...",
      "line_items": [ ... ],
      "discounts": {
        "codes": ["SAVE10", "EXPIRED50"],
        "applied": [
          {
            "code": "SAVE10",
            "title": "$10 Off Your Order",
            "amount": 1000
          }
        ]
      },
      "totals": [
        {"type": "subtotal", "display_text": "Subtotal", "amount": 5000},
        {"type": "discount", "display_text": "Order Discount", "amount": -1000},
        {"type": "total", "display_text": "Total", "amount": 4000}
      ],
      "messages": [
        {
          "type": "warning",
          "code": "discount_code_expired",
          "path": "$.discounts.codes[1]",
          "content": "Code 'EXPIRED50' expired on December 1st"
        }
      ]
    }
    ```

### Descontos acumulados com alocações

Vários descontos aplicados com detalhamento total da alocação:

=== "Resposta"

    <!-- ucp:example schema=shopping/cart op=read -->
    ```json
    {
      "ucp": { ... },
      "id": "...",
      "currency": "...",
      "line_items": [
        {
          "id": "li_1",
          "item": {
            "id": "prod_1",
            "title": "T-Shirt",
            "price": 6000
          },
          "quantity": 1,
          "totals": [
            {"type": "subtotal", "amount": 6000},
            {"type": "items_discount", "amount": -1500},
            {"type": "total", "amount": 4500}
          ]
        },
        {
          "id": "li_2",
          "item": {
            "id": "prod_2",
            "title": "Socks",
            "price": 4000
          },
          "quantity": 1,
          "totals": [
            {"type": "subtotal", "amount": 4000},
            {"type": "items_discount", "amount": -1000},
            {"type": "total", "amount": 3000}
          ]
        }
      ],
      "discounts": {
        "codes": ["SUMMER20", "LOYALTY5"],
        "applied": [
          {
            "code": "SUMMER20",
            "title": "Summer Sale 20% Off",
            "amount": 2000,
            "method": "each",
            "priority": 1,
            "allocations": [
              {"path": "$.line_items[0]", "amount": 1200},
              {"path": "$.line_items[1]", "amount": 800}
            ]
          },
          {
            "code": "LOYALTY5",
            "title": "$5 Loyalty Reward",
            "amount": 500,
            "method": "across",
            "priority": 2,
            "allocations": [
              {"path": "$.line_items[0]", "amount": 300},
              {"path": "$.line_items[1]", "amount": 200}
            ]
          }
        ]
      },
      "totals": [
        {"type": "subtotal", "display_text": "Subtotal", "amount": 10000},
        {"type": "items_discount", "display_text": "Item Discounts", "amount": -2500},
        {"type": "total", "display_text": "Total", "amount": 7500}
      ]
    }
    ```

Com esses dados, um agente pode explicar:
> "Sua camiseta (US$ 60) ganhou US$ 12 de desconto na promoção de verão de 20%, mais US$ 3 da sua
> recompensa de fidelidade (dividida proporcionalmente). Economia total neste item: US$ 15.
