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

# Capacidade do carrinho

* **Nome do recurso:** `br.dev.bcp.shopping.cart`

## Visão geral

O recurso Carrinho permite a construção de cestas sem a complexidade da finalização da compra.
Embora [Checkout](checkout.md) gerencie manipuladores de pagamento, ciclo de vida de status e
finalização do pedido, o carrinho fornece uma interface CRUD leve para a coleta
de itens antes que a intenção de compra seja estabelecida.

**Quando usar Carrinho vs Checkout:**

* **Carrinho**: O usuário está explorando, comparando e salvando itens para mais tarde. Nenhuma
  configuração de pagamento é necessária. A plataforma/agente pode adicionar, remover e atualizar itens livremente.
* **Checkout**: o usuário expressou intenção de compra. Os manipuladores de pagamento são
  configurados, o ciclo de vida do status começa, a sessão avança para a conclusão.

O fluxo típico: `cart session` → `checkout session` → `order`

Suporte para carrinhos:

* **Construção incremental**: adicione/remova itens entre sessões
* **Estimativas localizadas**: preços baseados no contexto sem sobrecarga total de checkout
* **Compartilhamento**: `continue_url` permite compartilhamento e recuperação de carrinho

## Carrinho vs Check-out

| Aspecto | Carrinho | Finalizar compra |
| ------ | ---- | -------- |
| **Objetivo** | Exploração pré-compra | Finalização de compra |
| **Pagamento** | Nenhum | Obrigatório (manipuladores, instrumentos) |
| **Status** | Binário (existe/não encontrado) | Ciclo de Vida (`incomplete` → `completed`) |
| **Operação Completa** | Não | Sim |
| **Totais** | Estimativas (podem ser parciais) | Preço final |

## Conversão do carrinho para finalização da compra

Quando a capacidade do carrinho é negociada, as plataformas podem converter um carrinho em checkout
fornecendo `cart_id` na solicitação Criar Checkout. O conteúdo do carrinho
(`line_items`, `context`, `buyer`) inicializa a sessão de checkout.

<!-- ucp:example schema=shopping/cart def=checkout op=create direction=request -->
```json
{
  "cart_id": "cart_abc123",
  "line_items": []
}
```

A empresa DEVE usar o conteúdo do carrinho e DEVE ignorar campos sobrepostos na carga útil do checkout.
O parâmetro `cart_id` só está disponível quando a capacidade do carrinho é anunciada
no perfil empresarial.

**Conversão idempotente:**

Caso já exista um checkout incompleto para o determinado `cart_id`, a empresa
DEVE retornar a sessão de checkout existente em vez de criar uma nova. Isto
garante um único checkout ativo por carrinho e evita sessões conflitantes.

**Ciclo de vida do carrinho após a conversão:**

Quando o checkout é inicializado via `cart_id`, o carrinho e a sessão de checkout
**DEVEM** permanecer vinculados durante a finalização da compra.

* **Durante a finalização da compra ativa** — A empresa DEVE manter o carrinho e refletir
    nele as modificações relevantes feitas no checkout (alterações de quantidade,
    remoções de itens). Isso oferece suporte a fluxos de retorno à vitrine
    enquanto os compradores transitam entre o checkout e a vitrine.

* **Após a conclusão da compra** — A empresa PODE limpar o carrinho com base no TTL,
    na conclusão da finalização da compra ou em outra lógica de negócios. Operações
    subsequentes sobre um ID de carrinho liberado retornam `not_found`; a
    plataforma pode iniciar uma nova sessão com `create_cart`.

## Escopos

O recurso Carrinho define os seguintes escopos conhecidos para
acesso autenticado pelo usuário:

| Escopo | Descrição |
| :--- | :--- |
| `br.dev.bcp.shopping.cart:manage` | Todas as operações do carrinho em nome do usuário autenticado – criar, ler, atualizar, persistir. |

Declaração de escopo, derivação e regras para estender este conjunto com
escopos personalizados são definidos em [Vinculação de identidade — Escopos](identity-linking.md#escopos).

## Diretrizes

### Plataforma

* **PODE** usar carrinhos para exploração pré-compra e persistência de sessão.
* **DEVE** converter o carrinho em finalização da compra quando o usuário expressar intenção de compra.
* **PODE** exibir `continue_url` para transferência para a UI comercial.
* **DEVE** lidar com `not_found` normalmente quando o carrinho expira ou é cancelado.

### Negócios

* **DEVERIA** fornecer `continue_url` para transferência do carrinho e recuperação da sessão.
* TODO: discuta o destino `continue_url` - carrinho vs checkout.
* **DEVE** fornecer totais estimados quando calculáveis.
* **PODE** omitir os totais de cumprimento até a finalização da compra quando o endereço for desconhecido.
* **DEVE** retornar mensagens informativas para avisos de validação.
* **PODE** definir a expiração do carrinho via `expires_at`.
* **DEVE** seguir [requisitos de ciclo de vida do carrinho](#conversao-do-carrinho-para-finalizacao-da-compra)
    quando o checkout é inicializado via `cart_id`.

## Definição do esquema do carrinho

{{ schema_fields('cart_resp', 'cart') }}

## Operações

O recurso Carrinho define as seguintes operações lógicas.

| Operação | Descrição |
| :--- | :--- |
| **Criar carrinho** | Cria uma nova sessão de carrinho. |
| **Obter carrinho** | Recupera o estado atual de uma sessão de carrinho. |
| **Atualizar carrinho** | Atualiza uma sessão de carrinho. |
| **Cancelar carrinho** | Cancela uma sessão de carrinho. |

### Criar carrinho

Cria uma nova sessão de carrinho com itens de linha e comprador/contexto opcional
informações para estimativas de preços localizadas.

Quando **todos** os itens solicitados estiverem indisponíveis, a empresa PODE devolver uma
resposta de erro em vez de criar um recurso de carrinho. `ucp.status` é o
discriminador primário; a ausência de `id` é um indicador secundário
consistente:

<!-- ucp:example schema=common/types/error_response op=read -->
```json
{
  "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
  "messages": [
    {
      "type": "error",
      "code": "out_of_stock",
      "content": "All requested items are currently out of stock",
      "severity": "unrecoverable"
    }
  ],
  "continue_url": "https://merchant.com/"
}
```

* REST Binding (não incluído nesta versão do BCP)
* [Vinculação MCP](cart-mcp.md#create_cart)

### Obter carrinho

Recupera o estado mais recente de uma sessão de carrinho. Retorna `not_found` se o carrinho
não existe, expirou ou foi cancelado.

* REST Binding (não incluído nesta versão do BCP)
* [Vinculação MCP](cart-mcp.md#get_cart)

### Atualizar carrinho

Executa uma substituição completa da sessão do carrinho. A plataforma **DEVE** enviar
todo o recurso do carrinho. O recurso fornecido substitui o estado existente
da sessão do carrinho no lado da empresa.

* REST Binding (não incluído nesta versão do BCP)
* [Vinculação MCP](cart-mcp.md#update_cart)

### Cancelar carrinho

Cancela uma sessão de carrinho. A empresa DEVE retornar o estado do carrinho antes da exclusão.
As operações subsequentes para este ID do carrinho DEVEM retornar `not_found`.

* REST Binding (não incluído nesta versão do BCP)
* [Vinculação MCP](cart-mcp.md#cancel_cart)

## Entidades

Cart reutiliza os mesmos esquemas de entidade que [Checkout](checkout.md). Isso garante
estruturas de dados consistentes ao converter um carrinho em uma sessão de checkout.

### Carrinho de resposta BCP {: #ucp-response-cart-schema }

{{ extension_schema_fields('ucp.json#/$defs/response_cart_schema', 'cart') }}

### Item de linha

#### Solicitação de criação de item de linha

{{ schema_fields('types/line_item_create_req', 'checkout') }}

#### Solicitação de atualização de item de linha

{{ schema_fields('types/line_item_update_req', 'checkout') }}

#### Item de linha

{{ schema_fields('types/line_item_resp', 'cart') }}

#### Artigo

{{ schema_fields('types/item_resp', 'cart') }}

### Comprador

{{ schema_fields('buyer', 'checkout') }}

### Contexto

{{ schema_fields('context', 'checkout') }}

### Sinais

Dados ambientais fornecidos pela plataforma para apoiar a autorização
e prevenção de abusos. Os valores do sinal NÃO DEVEM ser reivindicações afirmadas pelo comprador. Veja
[Sinais](overview.md#sinais) para detalhes e privacidade
requisitos.

{{ schema_fields('types/signals', 'checkout') }}

### Atribuição

Contexto de referência e evento de conversão fornecido pela plataforma – IDs de campanha,
identificadores de clique e marcadores de origem/mídia comunicados pela plataforma.
Consulte [Atribuição](overview.md#atribuicao) para obter detalhes e consentimento
requisitos.

{{ schema_fields('types/attribution', 'checkout') }}

### Total

O mesmo contrato de totais se aplica ao carrinho e ao checkout. Veja
[Checkout Totals](checkout.md#totais) para o contrato de renderização, contabilidade
identidade, tipos bem conhecidos, tipos repetidos e semântica de sublinhado.

{{ schema_fields('types/total_resp', 'checkout') }}

Os impostos PODEM ser incluídos quando calculáveis. As plataformas DEVEM assumir os totais do carrinho
são estimativas; impostos precisos são calculados na finalização da compra.

### Mensagem

{{ schema_fields('message', 'checkout') }}

#### Erro de mensagem

{{ schema_fields('types/message_error', 'checkout') }}

#### Informações da mensagem

{{ schema_fields('types/message_info', 'checkout') }}

#### Aviso de mensagem

{{ schema_fields('types/message_warning', 'checkout') }}

### Ligação

{{ schema_fields('types/link', 'checkout') }}
