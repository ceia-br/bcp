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

# Capacidade de pedido

* **Nome do recurso:** `br.dev.bcp.shopping.order`

## Visão geral

Os pedidos representam transações confirmadas resultantes de uma finalização de compra bem-sucedida
submissão. Eles fornecem um registro completo do que foi comprado, como
será entregue e o que aconteceu desde a colocação do pedido.

### Conceitos-chave

Os pedidos têm três componentes principais:

**Itens de linha** — o que foi comprado na finalização da compra:

* Inclui contagens de quantidade atuais (total, cumprido)
* Pode alterar pós-pedido (ex.: edições de pedidos, trocas); **DEVE** incluir todos os
  itens de linha que já existiram no pedido, independentemente de edições ou alterações

**Atendimento** — como os itens são entregues:

* **Expectativas** — *promessas* voltadas para o comprador sobre quando/como os itens chegarão
* **Eventos** (registro somente anexado) — o que realmente aconteceu (por exemplo, 👕 foi enviado)

**Ajustes** — eventos pós-pedido independentes do atendimento:

* Normalmente movimentos de dinheiro (reembolsos, devoluções, créditos, disputas, cancelamentos)
* Pode ser qualquer alteração pós-pedido
* Pode acontecer antes, durante ou depois do cumprimento
* As empresas **DEVERÃO** acrescentar novas entradas em vez de alterar as existentes;
  o livro razão somente anexado é o preferido. Empresas que não mantêm histórico de
  ajustes **PODEM** realizar atualizações locais de entradas existentes
  (por exemplo, um único ajuste `return` pode fazer a transição de `pending` para `completed`)

## Modelo de dados

### Itens de linha

Os itens de linha refletem o que foi comprado na finalização da compra e seu estado atual:

* Detalhes do item (produto, preço, quantidade encomendada)
* Contagens de quantidade e status de cumprimento

### Cumprimento

O atendimento rastreia como os itens são entregues ao comprador.

#### Expectativas

**Expectativas** são agrupamentos de itens voltados para o comprador (por exemplo, "pacote 📦"). Eles representam:

* Quais itens estão agrupados
* Para onde eles estão indo (`destination`)
* Como estão sendo entregues (`method_type`)
* Quando chegarão (`description`, `fulfillable_on`)

As expectativas podem ser divididas, mescladas ou ajustadas após o pedido. Por exemplo:

* Agrupe tudo por data de entrega: "o que vem quando"
* Use uma única expectativa com um amplo intervalo de datas para flexibilidade
* O objetivo é **definir as expectativas do comprador** – para obter a melhor experiência do comprador

#### Eventos de Cumprimento

**Eventos de atendimento** são um registro apenas anexado que rastreia remessas físicas:

* Itens de linha de referência por ID e quantidade
* Incluir informações de rastreamento
* O tipo é um campo de string aberto – as empresas podem usar qualquer valor que faça sentido
  (exemplos comuns: `processing`, `shipped`, `in_transit`, `delivered`,
  `failed_attempt`, `canceled`, `undeliverable`, `returned_to_sender`)

### Atribuição

As empresas PODEM exibir um instantâneo do checkout de origem
`attribution` no pedido. Somente leitura no pedido – os agentes não escrevem
`order.attribution`. Consulte [Atribuição](overview.md#atribuicao) para
contrato subjacente.

### Ajustes

**Ajustes** são eventos pós-pedido que existem independentemente de
cumprimento:

* O tipo é um campo de string aberto – as empresas podem usar qualquer valor que faça sentido
  (normalmente movimentos de dinheiro como `refund`, `return`, `credit`,
  `price_adjustment`, `dispute`, `cancellation`)
* Pode ser qualquer alteração pós-pedido
* Opcionalmente, vincule a itens de linha (ou ao nível do pedido para itens como reembolsos de frete)
* Quantidades e valores são assinados – negativo para reduções (devoluções, reembolsos),
  positivo para adições (trocas)
* Incluir detalhamento dos totais quando relevante
* Pode acontecer a qualquer momento, independentemente do status de cumprimento

## Esquema

### Pedido

{{ schema_fields('order', 'order') }}

### Item de linha do pedido

Os itens de linha refletem o que foi comprado na finalização da compra e seu estado atual.

{{ schema_fields('order_line_item', 'order') }}

**Estrutura quantitativa:**

<!-- ucp:example schema=shopping/types/order_line_item target=$.quantity -->
```json
{
  "original": 3,   // Quantity from the original checkout
  "total": 3,      // Current total (may differ after edits/exchanges)
  "fulfilled": 2   // What has been fulfilled
}
```

**Derivação de status:**

```text
if (total == 0) → "removed"
else if (fulfilled == total) → "fulfilled"
else if (fulfilled > 0) → "partial"
else → "processing"
```

### Expectativa

As expectativas são agrupamentos voltados para o comprador que representam quando/como os itens serão
entregue. Eles representam a promessa atual ao comprador e podem ser
pós-ordem dividida, mesclada ou ajustada.

{{ schema_fields('expectation', 'order') }}

### Evento de Cumprimento

Os eventos são registros somente anexados que rastreiam remessas reais. O campo `type` é
uma cadeia aberta - as empresas podem usar quaisquer valores que façam sentido para seus
processo de cumprimento.

{{ schema_fields('fulfillment_event', 'order') }}

Exemplos: `processing`, `shipped`, `in_transit`, `delivered`, `failed_attempt`,
`canceled`, `undeliverable`, `returned_to_sender`, etc.

### Ajuste

Os ajustes são eventos polimórficos que existem independentemente da realização.
O campo `type` é uma string aberta - as empresas podem usar qualquer valor que faça
sentido para eles.

{{ schema_fields('adjustment', 'order') }}

Exemplos: `refund`, `return`, `credit`, `price_adjustment`, `dispute`,
`cancellation`, etc.

## Exemplo

<!-- ucp:example schema=shopping/order op=read -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "capabilities": {
      "br.dev.bcp.shopping.order": [{"version": "{{ bcp_schema_version }}"}]
    }
  },
  "id": "order_abc123",
  "checkout_id": "checkout_xyz789",
  "permalink_url": "https://business.example.com/orders/abc123",
  "currency": "BRL",
  "line_items": [
    {
      "id": "li_shoes",
      "item": { "id": "prod_shoes", "title": "Running Shoes", "price": 3000 },
      "quantity": { "original": 3, "total": 3, "fulfilled": 3 },
      "totals": [
        {"type": "subtotal", "amount": 9000},
        {"type": "total", "amount": 9000}
      ],
      "status": "fulfilled"
    },
    {
      "id": "li_shirts",
      "item": { "id": "prod_shirts", "title": "Cotton T-Shirt", "price": 2000 },
      "quantity": { "original": 2, "total": 2, "fulfilled": 0 },
      "totals": [
        {"type": "subtotal", "amount": 4000},
        {"type": "total", "amount": 4000}
      ],
      "status": "processing"
    }
  ],
  "fulfillment": {
    "expectations": [
      {
        "id": "exp_1",
        "line_items": [{ "id": "li_shoes", "quantity": 3 }],
        "method_type": "shipping",
        "destination": {
          "street_address": "Rua das Flores, 123",
          "address_locality": "São Paulo",
          "address_region": "SP",
          "address_country": "BR",
          "postal_code": "01310-100"
        },
        "description": "Chega em 2 a 3 dias úteis",
        "fulfillable_on": "now"
      },
      {
        "id": "exp_2",
        "line_items": [{ "id": "li_shirts", "quantity": 2 }],
        "method_type": "shipping",
        "destination": {
          "street_address": "Rua das Flores, 123",
          "address_locality": "São Paulo",
          "address_region": "SP",
          "address_country": "BR",
          "postal_code": "01310-100"
        },
        "description": "Em espera - envio em 15 de janeiro, chega em 7 a 10 dias",
        "fulfillable_on": "2025-01-15T00:00:00Z"
      }
    ],
    "events": [
      {
        "id": "evt_1",
        "occurred_at": "2025-01-08T10:30:00Z",
        "type": "delivered",
        "line_items": [{ "id": "li_shoes", "quantity": 3 }],
        "tracking_number": "BR123456789BR",
        "tracking_url": "https://rastreamento.correios.com.br/app/index.php?objetos=BR123456789BR",
        "description": "Entregue na portaria"
      }
    ]
  },
  "adjustments": [
    {
      "id": "adj_1",
      "type": "refund",
      "occurred_at": "2025-01-10T14:30:00Z",
      "status": "completed",
      "line_items": [{ "id": "li_shoes", "quantity": -1 }],
      "totals": [
        { "type": "total", "amount": -3000 }
      ],
      "description": "Item com defeito"
    }
  ],
  "totals": [
    { "type": "subtotal", "amount": 13000 },
    { "type": "fulfillment", "amount": 1200 },
    { "type": "tax", "amount": 1142 },
    { "type": "total", "amount": 15342 }
  ]
}
```

## Escopos

O recurso Order define os seguintes escopos conhecidos para
acesso autenticado pelo usuário:

| Escopo | Descrição |
| :--- | :--- |
| `br.dev.bcp.shopping.order:read` | Acesso de leitura aos pedidos do usuário — Obtenha pedidos nos recursos pertencentes ao usuário autenticado. |
| `br.dev.bcp.shopping.order:manage` | Operações pós-compra nos pedidos do usuário — cancelamento, devoluções e outras modificações. |

Declaração de escopo, derivação e regras para estender este conjunto com
escopos personalizados são definidos em [Vinculação de identidade — Escopos](identity-linking.md#escopos).

## Operações {: #operacoes }

A entidade do pedido é um **instantâneo do estado atual**: o estado mais recente
do pedido no momento da recuperação ou entrega. As empresas **DEVEM**
retornar a entidade completa do pedido em cada resposta. O mesmo esquema é usado
para recuperação síncrona (esta seção) e entrega de evento assíncrono
(veja [Eventos](#events)).

O `permalink_url` é a referência oficial para a experiência completa do
pedido — cronograma, operações pós-compra, devoluções. A API fornece
acesso programático ao estado atual para casos de uso conversacionais e
operacionais.

| Operação | Método | Ponto final | Descrição |
| :-------------------------------------- | :----- | :------------ | :-------------------------------------- |
| [Obter pedido](#get-order) | `GET` | `/orders/{id}` | A plataforma recupera o estado atual do pedido. |

Para obter detalhes específicos do transporte, consulte Ligação REST (não incluída nesta versão do BCP) e
[Vinculação MCP](order-mcp.md)

### Obter pedido {: #get-order }

Retorna o instantâneo do estado atual de um pedido.

#### Autorização {: #autorizacao }

A empresa **DEVE** autenticar as solicitações de dados do pedido antes de retornar um
resposta, usando qualquer mecanismo BCP compatível - chaves de API, OAuth 2.0, mútuo
TLS ou assinaturas de mensagens HTTP (consulte
Identidade e Autenticação (não incluídas nesta versão do BCP)). O
O método de autenticação determina quais pedidos são acessíveis ao
chamador:

| Autenticação | Pedidos acessíveis |
| :------------ | :---------------------- |
| Credenciais da plataforma | Pedidos originados pela plataforma |
| Autorização do comprador | Pedidos de propriedade do comprador, sujeitos aos escopos OAuth concedidos |

**Credenciais da plataforma** (chave de API, assinaturas, credenciais do cliente OAuth) -
as empresas **PODEM** permitir o acesso para pedidos originados pela plataforma. O
plataforma forneceu informações do comprador e de pagamento durante o fluxo de checkout,
observou a confirmação do pedido e está recuperando o estado mais recente de um
pedido para o qual já tem contexto.

**Autorização do comprador** - a plataforma obtém autorização do comprador via
[Identity Linking](identity-linking.md) com os escopos necessários, ou um
mecanismo semelhante. Isso concede acesso aos pedidos do comprador, independentemente de
qual plataforma os originou.

As empresas **PODEM** definir políticas de acesso adicionais (por exemplo, parceiro confiável
acordos), impor restrições de disponibilidade de dados (por exemplo, retenção
janelas, eliminação regulatória) e omitir ou redigir campos opcionais da resposta
com base no contexto, política comercial ou outros requisitos - independentemente
de autorização.

#### Respostas de erro

Quando a empresa não consegue devolver um pedido, a resposta retorna um erro
que inclui uma matriz `messages` descrevendo o resultado:

**Pedido não encontrado:**

<!-- ucp:example schema=common/types/error_response op=read -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "status": "error",
    "capabilities": {
      "br.dev.bcp.shopping.order": [{"version": "{{ bcp_schema_version }}"}]
    }
  },
  "messages": [
    {
      "type": "error",
      "code": "not_found",
      "severity": "unrecoverable",
      "content": "Order not found."
    }
  ]
}
```

**Não autorizado:**

<!-- ucp:example schema=common/types/error_response op=read -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "status": "error",
    "capabilities": {
      "br.dev.bcp.shopping.order": [{"version": "{{ bcp_schema_version }}"}]
    }
  },
  "messages": [
    {
      "type": "error",
      "code": "unauthorized",
      "severity": "unrecoverable",
      "content": "Not authorized to access this order."
    }
  ]
}
```

### Diretrizes {: #operations-guidelines }

**Plataforma:**

* **DEVE** incluir o cabeçalho `BCP-Agent` com URL do perfil em todas as solicitações
* **DEVERIA** contar com webhooks (consulte [Eventos](#events)) como canal principal de atualização de pedidos
  e usar Obter Pedido para reconciliação ou recuperação sob demanda
* **DEVE** tratar os dados do pedido como efêmeros e descartá-los quando não forem mais necessários
  para fluxos de comércio ativos

**Negócios:**

* **DEVE** autenticar as solicitações de dados do pedido antes de retornar uma resposta
  (veja [Autorização](#autorizacao))

## Eventos {: #events }

As empresas enviam atualizações do ciclo de vida dos pedidos para a plataforma por meio de webhooks.
A carga útil é o mesmo **instantâneo do estado atual** descrito em
[Operações](#operacoes) — a entidade completa do pedido.

| Evento | Método | Ponto final | Descrição |
| :------------------------------------------ | :----- | :-------------------- | :----------------------------------------------------- |
| [Webhook de evento de pedido](#webhook-de-evento-de-pedido) | `POST` | URL fornecido pela plataforma | A empresa envia eventos do ciclo de vida do pedido para a plataforma. |

### Webhook de evento de pedido

As empresas enviam eventos de pedido via POST para uma URL de webhook fornecida pela plataforma
durante a integração do parceiro. O formato da URL é específico da plataforma.

Os cabeçalhos seguem **[Webhooks padrão](https://www.standardwebhooks.com/){ target="_blank" }**;
exceto para assinatura de solicitação, que segue [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421).
Consulte [Assinaturas de mensagens](signatures.md) para obter mais detalhes.

**Cabeçalhos obrigatórios:**

| Cabeçalho | Descrição |
| :------------------- | :------------------------------------------ |
| `Webhook-Timestamp` | Carimbo de data e hora da ocorrência do evento (unix) |
| `Webhook-Id` | Identificador único do evento |

A descrição do serviço OpenAPI para webhooks de pedidos não está publicada nesta versão do
BCP. O corpo do webhook usa o envelope de resposta do pedido e os mesmos requisitos de
assinatura descritos nesta seção.

### Configuração de URL do webhook

A plataforma fornece seu URL de webhook no campo `config` do recurso de pedido
durante a negociação de capacidade. A empresa descobre esse URL no
perfil da plataforma e o utiliza para enviar eventos do ciclo de vida do pedido.

{{ extension_schema_fields('order.json#/$defs/platform_schema', 'order') }}

**Exemplo:**

<!-- ucp:example schema=profile def=platform_schema target=$.ucp.capabilities -->
```json
{
  "br.dev.bcp.shopping.order": [
    {
      "version": "{{ bcp_schema_version }}",
      "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/order",
      "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/order.json",
      "config": {
        "webhook_url": "https://platform.example.com/webhooks/bcp/orders"
      }
    }
  ]
}
```

### Verificação de assinatura de webhook

As cargas úteis do webhook **DEVEM** ser assinadas pela empresa e verificadas pela plataforma
para garantir autenticidade e integridade. As assinaturas seguem a especificação de
[Assinaturas de mensagens](signatures.md) usando a ligação REST
(RFC 9421).

**Cabeçalhos obrigatórios:**

| Cabeçalho | Descrição |
| :--------------- | :-------------------------------------------- |
| `BCP-Agent` | URL do perfil comercial (Dicionário RFC 8941) |
| `Signature-Input`| Descreve componentes assinados |
| `Signature` | Contém o valor da assinatura |
| `Content-Digest` | Resumo corporal (RFC 9530) |

**Exemplo de solicitação de webhook:**

```http
POST /webhooks/bcp/orders HTTP/1.1
Host: platform.example.com
Content-Type: application/json
BCP-Agent: profile="https://merchant.example/.well-known/bcp"
Content-Digest: sha-256=:X48E9q...:
Signature-Input: sig1=("@method" "@authority" "@path" "content-digest" "content-type");keyid="merchant-2026"
Signature: sig1=:MEUCIQDTxNq8h7LGHpvVZQp1iHkFp9+3N8Mxk2zH1wK4YuVN8w...:

{"id":"order_abc123","event_id":"evt_123","created_time":"2026-01-15T12:00:00Z",...}
```

#### Assinatura (Negócios)

1. Calcule o resumo SHA-256 do corpo da solicitação bruta e defina o cabeçalho `Content-Digest`
2. Construa a base de assinatura de acordo com [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421)
3. Assine usando uma chave de `keys` no perfil BCP da empresa
4. Defina os cabeçalhos `Signature-Input` e `Signature`

Consulte [Assinaturas de mensagens - Assinatura de solicitação REST](signatures.md#assinatura-de-solicitacao-rest)
para algoritmo completo.

#### Verificação (plataforma)

**Autenticação** (verificação de assinatura):

1. Analise `Signature-Input` para extrair `keyid` e componentes assinados
2. Obtenha o perfil BCP da empresa em `/.well-known/bcp` (cache conforme apropriado)
3. Localize a chave em `keys` com `kid` correspondente
4. Verifique se `Content-Digest` corresponde a SHA-256 do corpo bruto
5. Reconstrua a base de assinatura e verifique a assinatura

Consulte [Assinaturas de mensagens - Verificação de solicitação REST](signatures.md#verificacao-de-solicitacao-rest)
para algoritmo completo.

**Autorização** (propriedade do pedido):

Depois de verificar a assinatura, a plataforma **DEVE** confirmar que o signatário está
autorizado a enviar eventos para o pedido referenciado:

1. Extraia o ID do pedido da carga útil do webhook
2. Verifique se o pedido foi criado com esta empresa (o URL do perfil corresponde)
3. Rejeite webhooks em que o perfil do signatário não corresponda ao negócio do pedido

Isso evita que uma empresa mal-intencionada envie eventos falsos para pedidos de
outro negócio, mesmo com uma assinatura válida.

#### Rotação de chaves

Consulte [Assinaturas de mensagens - rotação de chaves](signatures.md#rotacao-de-chaves) para
procedimentos de rotação de chaves com tempo de inatividade zero.

### Diretrizes {: #events-guidelines }

**Plataforma:**

* **DEVE** responder rapidamente com um código de status HTTP 2xx para confirmar o
  recebimento do webhook; processar os eventos de forma assíncrona após responder

**Negócios:**

* **DEVE** incluir o cabeçalho `BCP-Agent` com URL do perfil para identificação do signatário
* **DEVE** assinar todas as cargas úteis do webhook de acordo com a
  especificação de [Assinaturas de mensagens](signatures.md), usando os cabeçalhos RFC 9421
  (`Signature`, `Signature-Input`, `Content-Digest`)
* **DEVE** enviar o evento "Pedido criado" com a entidade do pedido totalmente preenchida
* **DEVE** enviar a entidade completa do pedido nas atualizações (não deltas incrementais)
* **DEVE** tentar novamente entregas de webhook com falha

## Entidades

### Item

{{ schema_fields('types/item_resp', 'order') }}

### Endereço postal

{{ schema_fields('postal_address', 'order') }}

### Resposta

{{ extension_schema_fields('capability.json#/$defs/response_schema', 'order') }}

### Total

{{ schema_fields('types/total_resp', 'order') }}

### Esquema de pedido de resposta BCP <span id="ucp"></span> {: #ucp-response-order-schema }

{{ extension_schema_fields('ucp.json#/$defs/response_order_schema', 'order') }}
