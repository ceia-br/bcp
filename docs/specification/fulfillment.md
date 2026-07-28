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

# Extensão de Cumprimento

## Visão geral

A extensão de atendimento permite que as empresas anunciem suporte para serviços físicos
atendimento de mercadorias (envio, coleta, etc).

Esta extensão adiciona um campo `fulfillment` ao Checkout e/ou Catálogo:

* **Checkout** (`br.dev.bcp.shopping.checkout`) — seleção e custo: qual
    os itens vão para onde, por qual método, a que preço e ETA.
* **Catálogo** (`br.dev.bcp.shopping.catalog.search` e
    `br.dev.bcp.shopping.catalog.lookup`) — descoberta: uma variante anuncia o
    opções de atendimento disponíveis para ele, com base no comprador fornecido
    contexto. Consulte [Descoberta de catálogo](#descoberta-de-catalogo).

No Checkout, o campo `fulfillment` contém:

* `methods[]` — métodos de atendimento aplicáveis aos itens do carrinho (envio, retirada, etc.)
    * `line_item_ids` — quais itens esse método atende
    * `destinations[]` — onde cumprir (endereço, localização da loja)
    * `groups[]` — pacotes gerados por negócios, cada um com `options[]` selecionável
* `available_methods[]` — disponibilidade de estoque por item (opcional)

**Modelo mental:**

* `methods[0]` Envio
    * `line_item_ids` 👕👖
    * `selected_destination_id` = `destinations[0].id` 🔘✅ 123 Fake St
    * `groups[0]` 📦👕👖
        * `selected_option_id` = `options[0].id` 🔘✅ Padrão $5
        * `options[1]` 🔘 Expresso $10
* `methods[1]` Retirada na loja
    * `line_item_ids` 👞
    * `selected_destination_id` = `destinations[0].id` 🔘✅ Loja Uptown
    * `groups[0]` 📦👞
        * `selected_option_id` = `options[0].id` 🔘✅ Retirada na loja
        * `options[1]` 🔘 Retirada na calçada

## Esquema

O cumprimento se aplica apenas a itens que exigem entrega física. Itens não
que exigem atendimento (por exemplo, bens digitais) não precisam ser atribuídos a um
método.

### Propriedades

{{ extension_fields('fulfillment', 'fulfillment') }}

### Entidades

#### Cumprimento

{{ schema_fields('types/fulfillment_resp', 'fulfillment') }}

#### Método de Cumprimento

{{ schema_fields('types/fulfillment_method_resp', 'fulfillment') }}

#### Destino de Cumprimento

{{ schema_fields('types/fulfillment_destination_resp', 'fulfillment') }}

#### Destino de Envio

{{ schema_fields('types/shipping_destination_resp', 'fulfillment') }}

#### Localização de varejo

{{ schema_fields('types/retail_location_resp', 'fulfillment') }}

#### Grupo de Cumprimento

{{ schema_fields('types/fulfillment_group_resp', 'fulfillment') }}

#### Opção de atendimento

{{ schema_fields('types/fulfillment_option_resp', 'fulfillment') }}

#### Método disponível de atendimento

{{ schema_fields('types/fulfillment_available_method_resp', 'fulfillment') }}

#### Total

{{ schema_fields('types/total_resp', 'fulfillment') }}

#### Endereço Postal

{{ schema_fields('postal_address', 'fulfillment') }}

### Exemplo

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "...",
  "status": "...",
  "currency": "...",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "fulfillment": {
    "methods": [
      {
        "id": "method_1",
        "type": "shipping",
        "line_item_ids": ["shirt", "pants"],
        "selected_destination_id": "dest_1",
        "destinations": [
          {
            "id": "dest_1",
            "street_address": "Rua das Flores, 123",
            "address_locality": "São Paulo",
            "address_region": "SP",
            "postal_code": "01310-100",
            "address_country": "BR"
          }
        ],
        "groups": [
          {
            "id": "package_1",
            "line_item_ids": ["shirt", "pants"],
            "selected_option_id": "standard",
            "options": [
              {
                "id": "standard",
                "title": "Frete Padrão",
                "description": { "plain": "Chega de 12 a 15 de dezembro pelos Correios" },
                "totals": [
                  {
                    "type": "total",
                    "amount": 500
                  }
                ]
              },
              {
                "id": "express",
                "title": "Frete Expresso",
                "description": { "plain": "Chega de 10 a 11 de dezembro por transportadora expressa" },
                "totals": [
                  {
                    "type": "total",
                    "amount": 1000
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

## Renderização

As opções de atendimento foram projetadas para **renderização independente de método**. Plataformas
não precisam entender tipos de métodos específicos (envio, coleta, etc.) para
apresentar opções de forma significativa. A empresa fornece dados pré-computados,
campos legíveis por humanos que as plataformas renderizam diretamente.

### Campos legíveis por humanos

| Localização | Campo | Obrigatório | Finalidade |
| --------------------- | ------------- | -------- | ------------------------------------------------------- |
| `groups[].options[]` | `title` | Sim | Rótulo primário que distingue dos irmãos |
| `groups[].options[]` | `description` | Não | Contexto complementar ao título |
| `groups[].options[]` | `totals` | Sim | Detalhamento de custos: um array de objetos `total` |
| `available_methods[]` | `description` | Não | Explicação independente da disponibilidade alternativa |

### Responsabilidades Empresariais

**Para `options[].title`:**

* **DEVE** distinguir esta opção de suas irmãs
* **DEVE** incluir método e velocidade (por exemplo, "Envio expresso", "Retirada na calçada")
* **DEVE** ser suficiente para a decisão do comprador se `description` estiver ausente

**Para `options[].description`:**

* **NÃO DEVE** repetir `title` ou `total` — fornece apenas contexto suplementar
* **DEVE** incluir horário, transportadora ou outros detalhes relevantes para a decisão
* **DEVE** ser uma frase completa (por exemplo, "Chega de 12 a 15 de dezembro pelos Correios")
* **PODE** ser omitido se o título for autoexplicativo

**Para `available_methods[].description`:**

* **DEVE** ser uma frase independente explicando o que, quando e onde
* **DEVE** ser utilizável literalmente no diálogo da plataforma (por exemplo, "Calças disponíveis
    para retirada na Downtown Store hoje às 14h")

**Quanto à ordenação:**

* As empresas **DEVERÃO** devolver `options[]` em uma ordem significativa (por exemplo, o mais barato
    primeiro, mais rápido primeiro)
* As plataformas **DEVEM** preservar essa ordem, mas **PODEM** reordená-la
    (por exemplo, para corresponder às preferências conhecidas do comprador ou à classificação específica da superfície);
    eles **DEVEM** preservar o agrupamento de métodos/opções

### Responsabilidades da plataforma

As plataformas **DEVERÃO** tratar o cumprimento como uma estrutura genérica e renderizável:

* Renderize cada opção como um cartão usando `title`, `description` e `total`
* Apresentar todos os métodos retornados – a seleção do método é uma decisão do comprador
* Preservar a estrutura de métodos e opções – não mesclar ou desduplicar;
    a plataforma escolhe o pedido
* Use `available_methods[].description` para apresentar alternativas ao comprador

As plataformas **PODEM** fornecer UX aprimorada para tipos de métodos reconhecidos (seletores de
loja para retirada, logotipos da transportadora para envio), mas isso é opcional. O contrato
básico é: **`title` + `description` + `total` é suficiente para renderizar qualquer
opção.**

Quando um comprador seleciona uma opção que a plataforma não consegue processar totalmente, a
plataforma **DEVE** usar `continue_url` para entregar no caixa da empresa.

## Métodos Disponíveis

Os métodos disponíveis indicam se um item pode ser atendido com um determinado
método e quando. Casos de uso:

* **Métodos alternativos**: "Essas calças também estão disponíveis para retirada na Downtown Store"
* **Atendimento mais tarde**: encomendas, envio de itens de um armazém distante, retirada quando a loja obtém estoque

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "...",
  "status": "...",
  "currency": "...",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "fulfillment": {
    "methods": [
      {
        "id": "shipping",
        "type": "shipping",
        "line_item_ids": ["shirt", "pants"]
      },
      {
        "id": "pickup",
        "type": "pickup",
        "line_item_ids": []
      }
    ],
    "available_methods": [
      {
        "type": "shipping",
        "line_item_ids": ["shirt", "pants"],
        "fulfillable_on": "now"
      },
      {
        "type": "pickup",
        "line_item_ids": ["pants"],
        "fulfillable_on": "2026-12-01T10:00:00Z",
        "description": "Disponível para retirada na Downtown Store hoje às 14h"
      }
    ]
  }
}
```

O campo `description` permite que as plataformas apresentem alternativas aos compradores:

> 🤖 A camisa e a calça são enviadas por R$ 5, chegando em 5 a 8 dias. Ou as calças podem
> ser retiradas na Downtown Store em 4 horas.

Se o comprador optar pela retirada, mas a plataforma não suportar atendimento dividido, a
plataforma **DEVE** usar `continue_url` para entregar ao checkout
da empresa.

## Descoberta de catálogo

Quando a extensão de atendimento estende a capacidade do Catálogo, cada variante
em uma resposta de catálogo carrega um objeto `fulfillment` listando os métodos de
atendimento disponíveis para essa variante e sua disponibilidade – portanto, um comprador
navegando no catálogo pode ver como um item pode ser atendido.

### Métodos

`fulfillment.methods[]` lista os métodos disponíveis para uma variante. Cada
método tem:

* `type` — o método de atendimento (por exemplo, `shipping`, `pickup`); veja
    [Tipos de métodos](#tipos-de-metodos).
* `description` — breve resumo voltado para o comprador sobre como a variante é
    cumprida através deste método (por exemplo, "Enviado em 2 a 4 dias úteis"). Diretamente
    renderizável; veja [Renderização](#renderizacao).
* `availability` — se a variante está disponível através deste método na
    localização especificada ou inferida.
* `location` — para métodos baseados em local (por exemplo, `pickup`), o ID do local resolvido
    e o identificador estável da empresa para esse local. Uma
    empresa que anuncia retirada em `location` DEVE aceitar o mesmo ID
    como `selected_destination_id` para esse método, portanto, um local descoberto
    pode ser usado no carrinho e na finalização da compra.
* `options` — escolhas concretas de atendimento dentro deste método (por exemplo
    Padrão, Expresso); veja [Opções](#opcoes). Opcional.

O catálogo informa a disponibilidade de um único local por método — aquele
especificado via `fulfills_to` ou inferido de `context`; a descoberta e
a comparação de outros locais são tratadas separadamente.

O `availability` em nível de variante indica se a variante é obtida através de
*qualquer* método; o `availability` do próprio método é a referência para
esse método. Quando um método indicar `availability`, os consumidores DEVEM usá-lo
para esse método e NÃO DEVEM inferir a disponibilidade por método a partir do
valor no nível da variante.

### Opções

Um método PODE carregar `options[]`, um subconjunto representativo de suas opções de
atendimento — não é uma lista exaustiva. Sem um destino ou um carrinho completo,
o catálogo DEVE apresentar um conjunto limitado e significativo de opções para o comprador
(por exemplo, mais barato, mais rápido); o conjunto completo e de alta resolução é negociado
no carrinho e na finalização da compra assim que forem conhecidos.

Cada opção traz um `id` e um `title` (uma pequena etiqueta que o distingue
de suas irmãs), além de uma `description` renderizável opcional para contexto. Essas
são uma base compartilhada: no checkout, a mesma opção é composta com custo e
prazo (`totals`, transportadora, prazos de atendimento). A opção é aberta, então
a empresa PODE anotá-la com campos adicionais. Um método também PODE não trazer
nenhuma opção, expondo apenas `type`, `description` e `availability`; as opções ficam
aninhadas diretamente sob o método, sem a camada de grupo (ao contrário do checkout
`methods[].groups[].options[]`).

O `id` de uma opção descoberta permite levar adiante a escolha do comprador: uma empresa
DEVE aceitar o mesmo id em `selected_option_id` no carrinho e na finalização da compra.
O id é um identificador de melhor esforço, não uma correspondência garantida – opções
descobertas para um único produto podem diferir em um carrinho, onde outros
produtos, quantidades e atendimento combinado modificam as opções.

### Formas

#### Contêiner de Cumprimento

{{ extension_schema_fields('fulfillment.json#/$defs/fulfillment', 'fulfillment') }}

#### Método de Cumprimento

{{ extension_schema_fields('fulfillment.json#/$defs/fulfillment_method', 'fulfillment') }}

#### Grupo de Cumprimento

{{ extension_schema_fields('fulfillment.json#/$defs/fulfillment_group', 'fulfillment') }}

#### Opção de atendimento

{{ extension_schema_fields('fulfillment.json#/$defs/fulfillment_option', 'fulfillment') }}

#### Método disponível de atendimento

{{ extension_schema_fields('fulfillment.json#/$defs/fulfillment_available_method', 'fulfillment') }}

### Localização e método: `context` e `filters`

* **`context`** (`address_country` / `address_region` / `postal_code`) é
    onde está o *comprador* — uma dica não vinculativa que a empresa usa para relatar
    `availability`. Em um catálogo com escopo de mercado, PODE restringir os resultados;
    caso contrário, ele os anota em vez de removê-los.
* **`filters.fulfills_to`** é onde o pedido é *atendido* — um único
    destino, nomeado por valor (um endereço aproximado: `address_country` /
    `address_region` / `postal_code`) ou por referência (um id `location` — uma
    loja, ponto de coleta ou endereço salvo). As plataformas **DEVERÃO** fornecer um
    ou outro, não ambos; se ambos estiverem presentes, uma empresa **DEVE** usar
    o mais específico — normalmente `location`. Ele restringe os resultados ao que
    pode ser atendido ali e inicializa a `availability` do método, que pode diferir
    de `context` (por exemplo, um presente).
* **`filters.methods`** restringe os resultados a tipos de métodos específicos (por exemplo,
    `["pickup"]`).

Forneça a localização uma vez: `context` para onde o comprador está, `fulfills_to` para
um destino explícito. Quando ambos estão presentes, `fulfills_to` substitui
`context`.

### Exemplo

Uma variante expõe dois métodos de atendimento: envio para o destinatário do comprador
e retire hoje em uma loja nomeada. Cada método carrega sua própria disponibilidade,
e `pickup` faz referência ao local resolvido por id.

<!-- ucp:example schema=shopping/fulfillment def=fulfillment_search_response op=read -->
```json
{
  "ucp": { "version": "{{ bcp_schema_version }}" },
  "products": [
    {
      "id": "prod_kettle",
      "title": "Electric Kettle",
      "description": { "plain": "1.7L electric kettle." },
      "price_range": {
        "min": { "amount": 4999, "currency": "BRL" },
        "max": { "amount": 4999, "currency": "BRL" }
      },
      "variants": [
        {
          "id": "var_ss",
          "title": "Stainless Steel",
          "description": { "plain": "Stainless steel finish." },
          "price": { "amount": 4999, "currency": "BRL" },
          "availability": { "available": true, "status": "in_stock" },
          "fulfillment": {
            "methods": [
              {
                "type": "shipping",
                "description": { "plain": "Ships to your address in 1–4 business days" },
                "availability": { "available": true, "status": "in_stock" },
                "options": [
                  {
                    "id": "std",
                    "title": "Standard",
                    "description": { "plain": "Arrives in 4 business days" }
                  },
                  {
                    "id": "exp",
                    "title": "Express",
                    "description": { "plain": "Next business day" }
                  }
                ]
              },
              {
                "type": "pickup",
                "description": { "plain": "Pickup today at Downtown Store" },
                "location": "loc_downtown",
                "availability": { "available": true, "status": "in_stock" }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

Cada método é uma maneira pela qual a variante pode ser cumprida, com seu próprio
`availability`. O `description` de cada método pode ser renderizado diretamente, então um
plataforma pode apresentá-lo sem reconhecer o `type` (ver
[Renderização](#renderizacao)). O `description` do método de envio visualiza o
faixa de entrega, e seu `options[]` a refina (Standard, Express); coleta
não carrega nenhum — `options` é opcional.

## Configuração

Empresas e plataformas declaram restrições de cumprimento em seus perfis.
As empresas buscam perfis de plataforma para adaptar as respostas de acordo.

A matriz `extends` lista os recursos aos quais esta extensão de atendimento se soma.
O checkout é a superfície transacional oficial; o catálogo é para
descoberta. Uma empresa lista os recursos do catálogo em `extends` para expor
atendimento no catálogo ou os omite para definir o escopo apenas para a finalização da compra.

### Perfil da plataforma

As plataformas declaram suas capacidades de renderização usando `platform_schema`:

{{ schema_fields('types/platform_fulfillment_config', 'fulfillment') }}

Plataformas que omitem configuração ou definem `supports_multi_group: false` recebem
respostas de grupo único. A forma da resposta é sempre
`methods[].groups[]` — a diferença é se `groups.length` pode exceder 1
dentro de cada método.

Declaração padrão (grupo único por método; cumprimento apareceu em
check-out e na descoberta do catálogo):

<!-- ucp:example schema=profile def=platform_schema target=$.ucp.capabilities -->
```json
{
  "br.dev.bcp.shopping.fulfillment": [
    {
      "version": "{{ bcp_schema_version }}",
      "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
      "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
      "extends": [
        "br.dev.bcp.shopping.checkout",
        "br.dev.bcp.shopping.catalog.search",
        "br.dev.bcp.shopping.catalog.lookup"
      ]
    }
  ]
}
```

Uma parte que não expõe a descoberta de catálogo PODE restringir `extends` a
`"br.dev.bcp.shopping.checkout"` (formato de string) ou para uma matriz de elemento único.

Declaração de aceitação (as empresas PODEM retornar vários grupos por método):

<!-- ucp:example schema=profile def=platform_schema target=$.ucp.capabilities -->
```json
{
  "br.dev.bcp.shopping.fulfillment": [
    {
      "version": "{{ bcp_schema_version }}",
      "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
      "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
      "extends": [
        "br.dev.bcp.shopping.checkout",
        "br.dev.bcp.shopping.catalog.search",
        "br.dev.bcp.shopping.catalog.lookup"
      ],
      "config": { "supports_multi_group": true }
    }
  ]
}
```

### Perfil da empresa

As empresas declaram quais configurações de atendimento suportam usando
`merchant_config`:

{{ schema_fields('types/merchant_fulfillment_config', 'fulfillment') }}

<!-- ucp:example schema=profile def=business_schema target=$.ucp.capabilities -->
```json
{
  "br.dev.bcp.shopping.fulfillment": [
    {
      "version": "{{ bcp_schema_version }}",
      "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
      "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
      "extends": [
        "br.dev.bcp.shopping.checkout",
        "br.dev.bcp.shopping.catalog.search",
        "br.dev.bcp.shopping.catalog.lookup"
      ],
      "config": {
        "multi_destination": [
          { "method": "shipping" }
        ],
        "method_combinations": [["shipping", "pickup"]]
      }
    }
  ]
}
```

Este exemplo diz: a remessa pode ir para vários endereços e os carrinhos podem misturar
envio+retirada.

### Comportamento de resposta comercial

**Quando `supports_multi_group: false` (padrão):**

* A empresa **DEVE** consolidar todos os itens em um **único grupo por método**
* A resposta ainda utiliza estrutura array: `methods[].groups[]` com `groups.length === 1`
* A empresa **PODE** ainda devolver vários métodos (por exemplo, frete + retirada) se
    os itens do carrinho exigirem isso

**Quando `supports_multi_group: true`:**

* As empresas **PODEM** retornar vários grupos por método com base no inventário,
    embalagem ou lógica de armazém
* A plataforma é responsável por renderizar a UI de seleção de grupo (por exemplo, escolher
    velocidade de envio por pacote)

### Tipos de métodos

`fulfillment_method.type` (checkout) e `catalog_fulfillment_method.type`
(catálogo) compartilham um vocabulário de corda aberta. A apresentação é independente de método:
plataformas **DEVERÃO** apresentar todos os métodos, renderizando `description` e
`availability` independentemente de seu `type` (veja [Renderização](#renderizacao)), e
**NÃO DEVEM** omitir um método apenas porque não reconhece seu `type`.
O reconhecimento de um `type` permite apenas UX opcional específico do tipo.

Um método é identificado por seu `type` e seu escopo de atendimento (o que ele
cumpre e onde). Uma empresa **DEVE** modelar variações no mesmo escopo (por exemplo,
Standard vs Express) como `options`, e **NÃO DEVE** emitir vários métodos
que diferem apenas em detalhes de nível de opção. Métodos com o mesmo `type` são válidos quando
seu escopo difere - por ex. checkout pode conter dois métodos `shipping` para
destinos diferentes. No catálogo, um método cobre uma única variante em um único
local resolvido por vez, então isso se reduz a no máximo um método por `type`.

**Valores conhecidos:**

| Valor | Significado |
| --- | --- |
| `shipping` | A transportadora envia para o endereço do comprador. |
| `pickup` | O comprador retira em local determinado. |
| `curbside` | O comprador retira no local sem sair do veículo (drive-up). |

**Adicionando tipos de métodos.** Como `type` é uma string aberta, uma empresa PODE
introduzir um novo valor a qualquer momento sem alteração do consumidor: anuncia o
valor (e o filtra via `filters.methods`), e os consumidores o apresentam
como qualquer outro método.

**Exemplo — adicionando `home_installation`.** Nenhuma alteração de esquema ou registro é
necessária. Emita o valor diretamente como `type` no catálogo e no checkout, e filtre
com `filters.methods: ["home_installation"]`. Para a negociação de carrinho e checkout,
declare seu comportamento no perfil comercial `config` — por exemplo,
incluindo `["shipping", "home_installation"]` em `method_combinations`
para que um carrinho possa misturar itens enviados e instalados (veja
[Perfil da empresa](#perfil-da-empresa)). No método de uma variante de catálogo:

<!-- ucp:example schema=shopping/fulfillment def=catalog_fulfillment_method op=read -->
```json
{
  "type": "home_installation",
  "description": { "plain": "Delivered and installed in your home" },
  "availability": {
    "available": true
  }
}
```

## Exemplos

### Básico

**Configuração:** Nenhuma necessária (comportamento padrão)

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "...",
  "status": "...",
  "currency": "...",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "fulfillment": {
    "methods": [
      {
        "id": "method_1",
        "type": "shipping",
        "line_item_ids": ["shirt", "pants"],
        "selected_destination_id": "dest_1",
        "destinations": [
          {
            "id": "dest_1",
            "street_address": "Rua das Flores, 123",
            "address_locality": "São Paulo",
            "address_region": "SP",
            "postal_code": "01310-100",
            "address_country": "BR"
          }
        ],
        "groups": [
          {
            "id": "package_1",
            "line_item_ids": ["shirt", "pants"],
            "selected_option_id": "standard",
            "options": [
              {
                "id": "standard",
                "title": "Frete Padrão",
                "description": { "plain": "Chega de 12 a 15 de dezembro pelos Correios" },
                "totals": [
                  {
                    "type": "total",
                    "amount": 500
                  }
                ]
              },
              {
                "id": "express",
                "title": "Frete Expresso",
                "description": { "plain": "Chega de 10 a 11 de dezembro por transportadora expressa" },
                "totals": [
                  {
                    "type": "total",
                    "amount": 1000
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Dividir grupos

**Configuração:** O perfil da plataforma requer `config.supports_multi_group: true`

A empresa divide os itens em vários pacotes; o comprador seleciona a taxa de envio por
pacote.

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "...",
  "status": "...",
  "currency": "...",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "fulfillment": {
    "methods": [
      {
        "id": "method_1",
        "type": "shipping",
        "line_item_ids": ["shirt", "pants"],
        "selected_destination_id": "dest_1",
        "destinations": [
          {
            "id": "dest_1",
            "street_address": "Rua das Flores, 123",
            "address_locality": "São Paulo",
            "address_region": "SP",
            "postal_code": "01310-100",
            "address_country": "BR"
          }
        ],
        "groups": [
          {
            "id": "package_1",
            "line_item_ids": ["shirt"],
            "selected_option_id": "standard",
            "options": [
              {
                "id": "standard",
                "title": "Standard",
                "totals": [ {"type": "total", "amount": 500} ]
              },
              {
                "id": "express",
                "title": "Express",
                "totals": [ {"type": "total", "amount": 1000} ]
              }
            ]
          },
          {
            "id": "package_2",
            "line_item_ids": ["pants"],
            "selected_option_id": "express",
            "options": [
              {
                "id": "standard",
                "title": "Standard",
                "totals": [ {"type": "total", "amount": 500} ]
              },
              {
                "id": "express",
                "title": "Express",
                "totals": [ {"type": "total", "amount": 1000} ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Dividir destinos

**Configuração:** O perfil comercial lista `shipping` em `config.multi_destination`

A camisa é enviada para a mãe (Brasil), as calças são enviadas para a avó (Hong Kong). Dois métodos do
mesmo tipo, cada um com seu destino.

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "...",
  "status": "...",
  "currency": "...",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "fulfillment": {
    "methods": [
      {
        "id": "method_1",
        "type": "shipping",
        "line_item_ids": ["shirt"],
        "selected_destination_id": "dest_mom",
        "destinations": [
          {
            "id": "dest_mom",
            "street_address": "Rua da Mamãe, 123",
            "address_locality": "São Paulo",
            "address_region": "SP",
            "postal_code": "01310-100",
            "address_country": "BR"
          }
        ],
        "groups": [
          {
            "id": "package_1",
            "line_item_ids": ["shirt"],
            "selected_option_id": "standard",
            "options": [
              {
                "id": "standard",
                "title": "Standard",
                "totals": [
                  {
                    "type": "total",
                    "amount": 500
                  }
                ]
              },
              {
                "id": "express",
                "title": "Express",
                "totals": [
                  {
                    "type": "total",
                    "amount": 1000
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "id": "method_2",
        "type": "shipping",
        "line_item_ids": ["pants"],
        "selected_destination_id": "dest_grandma",
        "destinations": [
          {
            "id": "dest_grandma",
            "street_address": "88 Queensway",
            "address_locality": "Hong Kong",
            "address_country": "HK"
          }
        ],
        "groups": [
          {
            "id": "package_2",
            "line_item_ids": ["pants"],
            "selected_option_id": "standard",
            "options": [
              {
                "id": "standard",
                "title": "Standard",
                "totals": [
                  {
                    "type": "total",
                    "amount": 500
                  }
                ]
              },
              {
                "id": "express",
                "title": "Express",
                "totals": [
                  {
                    "type": "total",
                    "amount": 1000
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```
