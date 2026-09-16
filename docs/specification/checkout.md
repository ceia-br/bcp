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

# Capacidade de check-out

* **Nome do recurso:** `br.dev.bcp.shopping.checkout`

## Visão geral

Permite que plataformas facilitem sessões de checkout. A finalização da compra deve ser
concluída manualmente pelo usuário por meio de uma UI confiável, a menos que a extensão
AP2 seja compatível.

A empresa continua sendo a Merchant of Record (MoR) e não precisa ser compatível com
PCI DSS para aceitar pagamentos com cartão por meio deste recurso.

### Visão geral do fluxo

![Diagrama de sequência de fluxo de checkout de alto nível](site:specification/images/ucp-checkout-flow.png)

### Pagamentos

Os manipuladores de pagamento são descobertos no perfil BCP da empresa em
`/.well-known/bcp` e em `checkout.ucp.payment_handlers`. Os manipuladores definem
as especificações de processamento para cobrança de instrumentos de pagamento
(por exemplo, Pix via `br.dev.bcp.pix` ou um gateway de cartão). Quando o comprador
envia o pagamento, a plataforma preenche a matriz `payment.instruments` com os dados
do instrumento coletados.

O objeto `payment` é opcional na criação do checkout e pode ser omitido para
casos de uso que não exigem processamento de pagamento (por exemplo, geração de cotação,
gestão de carrinho).

### Cumprimento

O cumprimento é modelado como uma extensão no BCP para dar conta de diversos casos de uso.

O cumprimento é opcional no objeto checkout. Isso permite que uma plataforma
realize o checkout de produtos digitais sem precisar fornecer detalhes de
cumprimento mais relevantes para bens físicos.

### Ciclo de vida do status do checkout

O campo checkout `status` indica a fase atual da sessão e
determina qual ação será necessária a seguir. A empresa define o status; o
plataforma recebe mensagens indicando o que é necessário para progredir.

```text
       +------------+                         +---------------------+
       | incomplete |<----------------------->

| requires_escalation |
       +-----+------+                         |   (buyer handoff    |
             |                                |  via continue_url)  |
             | all info collected             +----------+----------+
             v                                           |
    +------------------+                                 |
    |ready_for_complete|                                 |
    |                  |                                 |
    | (platform can    |                                 | continue_url
    | call Complete    |                                 |
    |   Checkout)      |                                 |
    +--------+---------+                                 |
             |                                           |
             | Complete Checkout                         |
             v                                           |
   +--------------------+                                |
   |complete_in_progress|                                |
   +---------+----------+                                |
             |                                           |
             +-----------------------+-------------------+
                                     v
                               +-------------+
                               |  completed  |
                               +-------------+

                               +-------------+
                               |  canceled   |
                               +-------------+
          (session invalid/expired - can occur from any state)
```

### Valores de status

* **`incomplete`**: A sessão de checkout não contém informações obrigatórias ou
    tem questões que precisam de resolução. A plataforma deve inspecionar a
    matriz `messages` para obter contexto e deve tentar resolvê-las por meio
    de Update Checkout.

* **`requires_escalation`**: A sessão de checkout requer informações que não
    podem ser fornecidas via API ou que exigem a contribuição do comprador. A
    plataforma deve inspecionar `messages` para entender o que é necessário
    (consulte Tratamento de erros abaixo). Se existir algum erro
    `recoverable`, resolva-o primeiro. Em seguida, entregue a sessão ao
    comprador via `continue_url`.

* **`ready_for_complete`**: A sessão de checkout contém todas as informações
    necessárias e pode ser finalizada programaticamente. A plataforma pode
    chamar Complete Checkout.

* **`complete_in_progress`**: A empresa está processando a solicitação de
    Complete Checkout.

* **`completed`**: Pedido realizado com sucesso.

* **`canceled`**: A sessão de checkout é inválida ou expirou. A plataforma
    deve iniciar uma nova sessão de checkout, se necessário.

### Tratamento de erros

A matriz `messages` contém erros, avisos e mensagens informativas
sobre o estado de checkout. `ucp.status` é o discriminador de forma —
`"success"` significa que a resposta carrega a carga esperada, `"error"`
significa que ela carrega informações de erro. Cada mensagem de erro carrega um `type`,
`code`, `severity`, `content` e um `path` opcional que identifica o
campo ou item de linha específico ao qual a mensagem se refere (consulte [O campo `path`](#o-campo-path) abaixo).
O campo `severity` prescreve a ação recomendada da plataforma:

| Gravidade | Significado | Ação da plataforma |
| :---------------------- | :---------------------------------------------------------- | :---------------------------------------------------------------- |
| `recoverable` | Plataforma pode resolver modificando inputs via API | Atualizar recurso e tentar novamente |
| `requires_buyer_input` | O negócio requer entrada não disponível via API | Transferência via `continue_url` |
| `requires_buyer_review` | É necessária revisão e autorização do comprador | Transferência via `continue_url` |
| `unrecoverable` | Não existe nenhum recurso para agir | Tente novamente com novos recursos ou entradas ou transfira via `continue_url` |

Erros com gravidade `requires_*` contribuem para `status: requires_escalation`.
Ambos resultam na transferência do comprador, mas representam diferentes estados de checkout.

* `requires_buyer_input` significa que a finalização da compra está **incompleta** — a empresa
requer informações que a API não é capaz de coletar de forma programática.
* `requires_buyer_review` significa que a finalização da compra está **completa** — mas política,
regras regulatórias ou de direitos exigem autorização do comprador antes da
colocação do pedido (por exemplo, aprovação de pedidos de alto valor, política de primeira compra).

Quando a empresa não consegue criar um novo recurso ou o recurso solicitado
não existe mais, a resposta contém `ucp.status: "error"` com
`messages` descrevendo a falha — nenhum recurso está incluído no
corpo de resposta. Quando não existe nenhum recurso para agir, as mensagens DEVEM usar
`severity: "unrecoverable"`.
Por exemplo, uma empresa pode rejeitar uma solicitação de criação de checkout em que todos
itens não estão disponíveis:

<!-- ucp:example schema=shopping/types/error_response op=read -->
```json
{
  "ucp": { "version": "2026-01-11", "status": "error" },
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

Consulte os exemplos de vinculação REST (não incluído nesta versão do BCP) e
[MCP](checkout-mcp.md#create_checkout).

#### Algoritmo de processamento de erros

Quando o status for `incomplete` ou `requires_escalation`, as plataformas deverão processar
erros como uma pilha priorizada. O exemplo abaixo ilustra um checkout com
três tipos de erro: um erro recuperável (telefone inválido), um requisito de
entrada do comprador (agendamento de entrega) e um requisito de revisão (pedido de alto valor).
Os dois últimos exigem transferência e servem como sinais explícitos para a plataforma.
As empresas **DEVERÃO** divulgar essas mensagens o mais cedo possível, e as plataformas
**DEVEM** priorizar a resolução de erros recuperáveis antes de iniciar a transferência.

<!-- ucp:example schema=shopping/checkout target=$.messages op=read -->
```json
[
  {
    "type": "error",
    "code": "invalid_phone",
    "severity": "recoverable",
    "path": "$.buyer.phone_number",
    "content": "Phone number format is invalid"
  },
  {
    "type": "error",
    "code": "schedule_delivery",
    "severity": "requires_buyer_input",
    "content": "Select delivery window for your purchase"
  },
  {
    "type": "error",
    "code": "high_value_order",
    "severity": "requires_buyer_review",
    "content": "Orders over $500 require additional verification"
  }
]
```

Exemplo de algoritmo de processamento de erros:

```text
GIVEN response with messages array

FILTER errors FROM messages WHERE type = "error"

PARTITION errors INTO
  recoverable           WHERE severity = "recoverable"
  requires_buyer_input  WHERE severity = "requires_buyer_input"
  requires_buyer_review WHERE severity = "requires_buyer_review"
  unrecoverable         WHERE severity = "unrecoverable"

IF unrecoverable is not empty
  RETRY with new resource or inputs, or hand off via continue_url
  RETURN

IF recoverable is not empty
  FOR EACH error IN recoverable
    IF error.path is present
      IDENTIFY the field at error.path in the request payload
      ATTEMPT to fix that field (e.g., reformat phone at $.buyer.phone_number)
    ELSE
      ATTEMPT generic fix based on error.code
  CALL Update Checkout
  RETURN and re-evaluate response

IF requires_buyer_input is not empty
  handoff_context = "incomplete, additional input from buyer is required"
ELSE IF requires_buyer_review is not empty
  handoff_context = "ready for final review by the buyer"
```

#### Erros padrão

Erros padrão são códigos de erro padronizados que as plataformas devem
tratar com uma UX específica e apropriada, em vez de um tratamento de erro genérico.

| Código | Descrição |
| :---------------------- | :----------------------------------------------------------------------------------- |
| `out_of_stock` | Item ou variante específica não está disponível |
| `item_unavailable` | O item não pode ser comprado (por exemplo, removido da lista) |
| `address_undeliverable` | Não é possível entregar no endereço fornecido |
| `payment_failed` | Falha no processamento do pagamento |
| `eligibility_invalid` | A reivindicação de elegibilidade não pôde ser verificada na conclusão |

As empresas **DEVERÃO** marcar os erros padrão com `severity: recoverable` para
sinalizar que as plataformas devem fornecer UX apropriada (mensagens de falta de estoque,
avisos de validação de endereço, alterações na forma de pagamento) em vez de
mensagens de erro genéricas ou adiar a conclusão da compra.

Exemplo: `out_of_stock` requer uma UX inicial específica, enquanto
`payment_failed` pode ser tratado genericamente no momento da submissão.

#### O Campo `path`

O campo opcional `path` em uma mensagem ancora o erro em um
componente da carga útil da resposta. As plataformas o usam para associar
mensagens de erro ao campo de entrada ou item de linha que as causou — por
exemplo, destacando um campo específico do comprador em um formulário ou
sinalizando uma linha específica do carrinho.

`path` **DEVE** ser uma expressão JSONPath [RFC 9535](https://www.rfc-editor.org/rfc/rfc9535)
relativa à raiz do objeto de resposta BCP.
Os nomes de propriedades **DEVEM** usar snake_case correspondente ao esquema de solicitação.
Quando `path` é omitido, a mensagem se aplica à resposta como um todo.

**Referência de campo simples:**

<!-- ucp:example skip reason="path schema example" -->
```json
{ "path": "$.buyer.email" }
```

**Elemento de matriz indexado:**

<!-- ucp:example skip reason="path schema example" -->
```json
{ "path": "$.line_items[0].quantity" }
```

**Expressão de filtro (opcional, ao referenciar um item específico por ID):**

<!-- ucp:example skip reason="path schema example" -->
```json
{ "path": "$.line_items[?(@.id=='line-item-uuid')].quantity" }
```

As expressões de filtro têm sintaxe RFC 9535 válida e **PODEM** ser usadas quando
referenciar um item de linha específico por `id` é mais claro que seu índice.
Os caminhos baseados em índice são igualmente válidos; a empresa retorna índices que
são inequívocos na resposta.

**Regra de especificidade:** um caminho para um campo específico (por exemplo,
`$.line_items[0].quantity`) tem precedência sobre um caminho para seu pai
(por exemplo, `$.line_items[0]`). Quando vários erros se aplicam ao mesmo campo,
cada mensagem **DEVE** conter o caminho mais específico aplicável.

#### Verificação de elegibilidade na conclusão

As plataformas fornecem `context.eligibility` — reivindicações do comprador sobre benefícios elegíveis
como associação de fidelidade, vantagens de instrumentos de pagamento e similares. Estes são
reivindicações, não fatos verificados. As empresas **PODEM** agir de acordo com reivindicações reconhecidas durante
a sessão (ajuste de preços, concessão de acesso ao produto, aplicação de
descontos), mas todas as reivindicações aceitas **DEVEM** ser resolvidas antes que
a transação possa ser concluída.

Reivindicações não reconhecidas ou inaplicáveis **NÃO DEVEM** bloquear a finalização da compra.
As empresas **DEVERÃO** notificar o comprador via `messages` com `type: "warning"`
quando uma reivindicação não for aceita, e **PODEM** usar `type: "info"` para explicar
os efeitos das reivindicações aceitas. Na conclusão, as reivindicações aceitas que
permanecerem não verificadas **DEVEM** resultar em `type: "error"` com
`code: "eligibility_invalid"` (veja abaixo).

**Códigos de mensagem de elegibilidade:**

| Tipo | Código | Quando |
| --------- | -------------------------- | -------------------------------------------------- |
| `warning` | `eligibility_not_accepted` | Alegação não reconhecida ou não aplicável |
| `info` | `eligibility_accepted` | Efeito de uma reclamação aceite |
| `error` | `eligibility_invalid` | A reivindicação aceita não pôde ser verificada na conclusão |

Uma reivindicação é resolvida quando é **verificada** ou **rescindida**:

* **Verificada**: A Empresa confirma a reivindicação com base em uma prova
  fornecida no momento da conclusão. O BCP não prescreve como ocorre a
  verificação — a prova pode vir da credencial de pagamento, de um recurso de
  verificação de identidade, ou de qualquer outro mecanismo negociado entre a
  Plataforma e o Negócio.
* **Rescindida**: A Plataforma remove a reivindicação de `context.eligibility`
  antes da conclusão (por exemplo, o comprador altera a forma de pagamento ou
  retira uma reivindicação de adesão). Uma vez removida, a Empresa recalcula
  sem ela.

As empresas **NÃO DEVEM** concluir uma transação com reivindicações de
elegibilidade não resolvidas. Reivindicações não verificadas podem resultar em
preços incorretos ou acesso a produtos restritos.

**Quando a verificação falha:**

A falha na verificação **DEVE** afetar apenas o array `messages`. A
empresa **DEVE** retornar um erro em `messages` com
`code: "eligibility_invalid"` e `severity: "recoverable"`. As mensagens
**DEVERIAM** usar o campo `path` para identificar quais reivindicações específicas
não puderam ser verificadas. A Plataforma **PODE** fornecer provas válidas e
reenviar, reestruturar o checkout (por exemplo, remover itens inelegíveis, atualizar
reivindicações) ou abandonar a tentativa.

Por exemplo, a Plataforma reivindica um benefício de cartão de loja por meio de
`context.eligibility`. A Empresa aplica preços para membros durante a sessão.
Na conclusão, a credencial de pagamento não corresponde ao instrumento reivindicado:

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { "version": "2026-01-11", "status": "success", "payment_handlers": { ... } },
  "id": "checkout_abc",
  "status": "ready_for_complete",
  "currency": "...",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "messages": [
    {
      "type": "error",
      "code": "eligibility_invalid",
      "severity": "recoverable",
      "content": "Payment credential does not match the claimed store card benefit.",
      "path": "$.context.eligibility[0]"
    }
  ]
}
```

A Plataforma pode resolver isso fazendo com que o comprador mude para o produto qualificado
instrumento de pagamento, ou removendo a reclamação de `context.eligibility` para
renegociar o checkout (obter preços atualizados, disponibilidade, etc.)
e, em seguida, reenviando para conclusão.

### Apresentação de aviso

O campo `presentation` nas mensagens de aviso controla a renderização
contratar a plataforma **DEVE** seguir. Quando omitido, o padrão é
`"notice"`.

| | `notice` (padrão) | `disclosure` |
| :--- | :--- | :--- |
| Exibir conteúdo | **DEVE** | **DEVE** |
| Proximidade de `path` | **PODE** | **DEVE** |
| Dispensável | **PODE** | **NÃO DEVE** |
| Renderização `image_url` | **PODE** | **DEVE** |
| Renderização `url` | **PODE** | **DEVE** |
| Escalar se não puder honrar | — | **DEVE** via `continue_url` |

#### `notice` (padrão)

O contrato de renderização padrão para avisos. Plataformas **DEVEM** ser exibidas
o conteúdo do aviso ao comprador. As plataformas **PODEM** renderizar avisos em um
banner, bandeja ou brinde, e **PODE** permitir que o comprador os dispense.

#### `disclosure`

Avisos com `presentation: "disclosure"` carregam avisos - segurança
avisos, declarações de alérgenos, conteúdo de conformidade, etc.
**DEVE** seguir o contrato de renderização prescrito abaixo.

**Requisitos da plataforma:**

* **DEVE** exibir o aviso `content` ao comprador.
* **DEVE** exibir o aviso próximo ao componente referenciado
  por `path`, preservando a associação entre a divulgação e sua
  assunto. Quando `path` for omitido, a divulgação se aplica à resposta
  como um todo.
* **NÃO DEVE** ocultar, recolher ou ignorar automaticamente o aviso.
* **DEVE** renderizar `image_url` quando presente (por exemplo, símbolo de aviso,
  etiqueta de classe energética).
* **DEVE** renderizar `url` como um link de referência navegável, quando presente.

Avisos com `presentation: "disclosure"` **DEVEM** ter prioridade de renderização
sobre avisos do tipo `notice`.

Plataformas que não conseguem honrar o contrato de renderização da divulgação
**DEVEM** escalar para a UI do comerciante via `continue_url`, em vez de
rebaixá-la silenciosamente para um `notice`.

**Requisitos de negócios:**

* **DEVE** definir `presentation: "disclosure"` quando o conteúdo do aviso deve
  ser exibido ao lado de um componente específico e não deve ser oculto ou
  descartado automaticamente.
* **DEVE** utilizar o campo `path` para associar as divulgações ao
  componente relevante na resposta.
* **DEVE** fornecer um `code` que identifique a categoria de divulgação
  (por exemplo, `prop65`, `allergens`, `energy_label`).
* **DEVE** fornecer `image_url` quando a divulgação tiver um associado
  elemento visual (por exemplo, símbolo de advertência, etiqueta de classe energética).
* **DEVE** fornecer `url` quando um link de referência estiver disponível para o
  comprador para saber mais.

#### Divulgação e Reconhecimento

O campo `presentation` controla como o aviso é renderizado, não se o checkout
pode prosseguir. Quando também for necessário o reconhecimento afirmativo do
comprador ou uma autorização, a empresa **PODE** combinar a divulgação com os
mecanismos de escalonamento descritos no
[Ciclo de vida do status do checkout](#ciclo-de-vida-do-status-do-checkout) para garantir
que a manifestação apropriada do comprador seja obtida.

#### Jurisdição e aplicabilidade

É responsabilidade da empresa determinar quais divulgações se aplicam a uma
determinada sessão e retornar apenas aquelas que são relevantes. As empresas
**DEVEM** usar dados fornecidos pelo comprador (`context` e outras informações) e
atributos do produto para resolver requisitos específicos da jurisdição.
As plataformas não afetam nem resolvem a aplicabilidade da divulgação — elas
apenas apresentam o que recebem da empresa.

#### Exemplo

Uma resposta de checkout contendo um erro recuperável e uma divulgação
aviso em um item de linha:

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { "version": "{{ bcp_schema_version }}", "status": "success", "payment_handlers": { ... } },
  "id": "chk_abc123",
  "status": "incomplete",
  "currency": "BRL",
  "line_items": [
    {
      "id": "li_1",
      "item": { "id": "item_456", "title": "Artisan Nut Butter Collection", "price": 1299, "image_url": "https://merchant.com/nut-butter.jpg" },
      "quantity": 1,
      "totals": [
        { "type": "subtotal", "amount": 1299 },
        { "type": "total", "amount": 1299 }
      ]
    }
  ],
  "totals": [
    { "type": "subtotal", "amount": 1299 },
    { "type": "total", "amount": 1299 }
  ],
  "messages": [
    {
      "type": "error",
      "code": "field_required",
      "path": "$.buyer.email",
      "content": "Buyer email is required",
      "severity": "recoverable"
    },
    {
      "type": "warning",
      "code": "allergens",
      "path": "$.line_items[0]",
      "content": "**Contains: tree nuts.** Produced in a facility that also processes peanuts, milk, and soy.",
      "content_type": "markdown",
      "presentation": "disclosure",
      "image_url": "https://merchant.com/allergen-tree-nuts.svg",
      "url": "https://merchant.com/allergen-info"
    }
  ],
  "links": []
}
```

A plataforma resolve o erro recuperável programaticamente enquanto
tornando a divulgação do alérgeno próxima à linha referenciada
artigo.

## Continuar URL

O campo `continue_url` permite a transferência de checkout da plataforma para a interface de negócios,
permitindo que o comprador continue e finalize a sessão de checkout.

### Disponibilidade

As empresas **DEVEM** fornecer `continue_url` ao retornar `status` =
`requires_escalation`. Para todos os outros status não terminais (`incomplete`,
`ready_for_complete`, `complete_in_progress`), as empresas **DEVERÃO** fornecer
`continue_url`. Para estados terminais (`completed`, `canceled`), `continue_url`
**DEVE** ser omitido.

### Formato

O `continue_url` **DEVE** ser um URL HTTPS absoluto e **DEVE** preservar
estado de checkout para transferência perfeita. As empresas **PODEM** implementar o estado
preservação usando qualquer uma das abordagens:

#### Estado do lado do servidor (recomendado)

Um URL opaco apoiado pelo estado de checkout do lado do servidor:

```text
https://business.example.com/checkout-sessions/{checkout_id}
```

* Servidor mantém estado de checkout vinculado a `checkout_id`
* Simples, seguro, recomendado para a maioria das implementações
* Vida útil do URL normalmente vinculada a `expires_at`

#### Link permanente de check-out

Uma URL sem estado que codifica diretamente o estado de checkout, permitindo a
reconstrução sem persistência do lado do servidor. As empresas **DEVERÃO**
implementar suporte para este formato para facilitar a entrega do checkout e
a entrada acelerada — por exemplo, um fluxo de "comprar agora" em que a
plataforma preenche previamente o estado de checkout ao iniciá-lo.

> **Observação:** Links permanentes de checkout são uma construção específica do REST que estende a
> ligação de transporte REST (não incluída nesta versão do BCP). Acessar um link permanente retorna um
> redirecionamento para a UI de checkout ou renderiza a página de checkout diretamente.

## Escopos

O recurso Checkout define os seguintes escopos conhecidos para
acesso autenticado pelo usuário:

| Escopo | Descrição |
| :--- | :--- |
| `br.dev.bcp.shopping.checkout:manage` | Todas as operações de checkout em nome do usuário autenticado — criar, atualizar, concluir e cancelar sessões de checkout. |

Declaração de escopo, derivação e regras para estender este conjunto com
escopos personalizados são definidos em [Vinculação de identidade — Escopos](identity-linking.md#escopos).

## Diretrizes

(Além das diretrizes gerais)

### Plataforma

* **PODE** contratar um agente para facilitar a sessão de checkout (por exemplo,
    adicionar itens à sessão de checkout, selecionar o endereço de cumprimento).
    No entanto, o agente deve entregar a sessão de checkout a uma UI confiável e
    determinística para que o usuário revise os detalhes do checkout e faça o
    pedido.
* **PODE** enviar o usuário da UI confiável e determinística de volta ao agente
    a qualquer momento. Por exemplo, quando o usuário decide sair da tela de checkout
    para continuar adicionando itens ao carrinho.
* **PODE** fornecer contexto ao agente quando a plataforma indicar que a solicitação
    foi feita por um agente.
* **DEVE** usar `continue_url` quando o status de checkout for `requires_escalation`.
* **PODE** usar `continue_url` para transferir para a UI comercial em outras situações.
* Ao realizar a transferência, **DEVE** preferir o `continue_url` fornecido pela
    empresa em vez de links permanentes de checkout construídos pela plataforma.

### Negócios

* **DEVE** enviar um e-mail de confirmação após a finalização da compra.
* **DEVE** fornecer mensagens de erro precisas.
* A lógica que trata as sessões de checkout **DEVE** ser determinística.
* **DEVE** fornecer `continue_url` ao retornar `status` =
    `requires_escalation`.
* **DEVE** incluir pelo menos uma mensagem com `severity` de
    `requires_buyer_input` ou `requires_buyer_review` no retorno
    `status` = `requires_escalation`.
* **DEVE** fornecer `continue_url` em todas as respostas de checkout não terminais.
* Após uma sessão de checkout atingir o status `completed`, ela é considerada
    imutável.

## Definição do esquema de capacidade <span id="checkout"></span>

{{ schema_fields('checkout_resp', 'checkout') }}

## Operações

O recurso Checkout define as seguintes operações lógicas.

| Operação | Descrição |
| :-------------------- | :------------------------------------------------------------------------------------------------ |
| **Criar check-out** | Inicia uma nova sessão de checkout. Chamado assim que um usuário adiciona um item ao carrinho. |
| **Fazer check-out** | Recupera o estado atual de uma sessão de checkout.                                 |
| **Atualizar Check-out** | Atualiza uma sessão de checkout.                                                        |
| **Concluir Check-out** | Finaliza o checkout e faz o pedido.                                       |
| **Cancelar check-out** | Cancela uma sessão de checkout.                                                        |

### Criar check-out

Deve ser invocada pela plataforma quando o usuário manifestar intenção de compra
(por exemplo, ao clicar em "Comprar") para iniciar a sessão de checkout com os
detalhes do item.

**Recomendação**: para minimizar discrepâncias e simplificar a experiência do
usuário, os dados do produto (preço, título etc.) fornecidos pela empresa por
meio dos feeds **DEVEM** corresponder aos atributos reais retornados na resposta.

Quando o recurso [Cart](cart.md) é negociado, a carga útil da solicitação
**DEVE** aceitar um campo `cart_id` adicional para conversão do carrinho em
checkout. Veja [Carrinho → Conversão do carrinho para checkout](cart.md#conversao-do-carrinho-para-finalizacao-da-compra)
para o contrato de campo.

**Campos de solicitação**

{{ schema_fields('checkout_create_req', 'checkout') }}

**Campos de resposta**

{{ schema_fields('checkout_resp', 'checkout') }}

### Obter check-out

Fornece o estado mais recente do recurso de checkout. Após o cancelamento ou a
conclusão, cabe à empresa decidir o que devolver — ou seja, o estado pode
permanecer disponível por um longo período ou expirar após um TTL específico,
resultando em um erro `not_found`. A plataforma não impõe um TTL próprio para
o checkout.

A plataforma respeita o TTL fornecido pela empresa via `expires_at` no momento
da criação da sessão de checkout.

**Campos de resposta**

{{ schema_fields('checkout_resp', 'checkout') }}

### Atualizar check-out

Executa uma substituição completa do recurso de checkout. A plataforma **DEVE**
enviar o recurso de checkout completo, incluindo quaisquer atualizações em
campos somente-gravação. O recurso fornecido na solicitação substitui o estado
da sessão de checkout existente no lado da empresa.

**Campos de solicitação**

{{ schema_fields('checkout_update_req', 'checkout') }}

**Campos de resposta**

{{ schema_fields('checkout_resp', 'checkout') }}

### Concluir check-out

Esta é a chamada final de finalização do checkout. Deve ser invocada quando o
usuário se comprometer a pagar e fazer o pedido dos itens escolhidos. A resposta
dessa chamada é o objeto checkout com o campo `order` preenchido. O `order`
retornado fornece os identificadores necessários, como `id` e `permalink_url`,
que podem ser usados para referenciar o estado completo do pedido criado.
Os campos do `Checkout` **PODEM** ser usados no momento da persistência do
pedido para construir sua representação (ou seja, informações como
`line_items` e `fulfillment` são usadas para criar a representação inicial
do pedido).

Após essa chamada, outros detalhes são atualizados em eventos subsequentes
à medida que o pedido e seus itens associados avançam pela cadeia de suprimentos.

**Campos de solicitação**

{{ schema_fields('checkout_complete_req', 'checkout') }}

**Campos de resposta**

{{ schema_fields('checkout_resp', 'checkout') }}

### Cancelar check-out

Esta operação é usada para cancelar uma sessão de checkout, caso ela possa ser
cancelada. Se a sessão de checkout não puder ser cancelada (por exemplo, se já
estiver cancelada ou concluída), a empresa **DEVERÁ** retornar um erro
indicando que a operação não é permitida. Qualquer sessão de checkout com
status diferente de `completed` ou `canceled` **DEVE** ser cancelável.

**Campos de resposta**

{{ schema_fields('checkout_resp', 'checkout') }}

## Ligações de transporte

As operações abstratas acima estão vinculadas a protocolos de transporte específicos como
definido abaixo:

* REST Binding (não incluído nesta versão do BCP): mapeamento de API RESTful usando verbos HTTP padrão e cargas JSON.
* [MCP Binding](checkout-mcp.md): Mapeamento do protocolo de contexto do modelo para interação de agente.
* [A2A Binding](checkout-a2a.md): Mapeamento de protocolo agente para agente para interações de agente.
* [Embedded Checkout Binding](embedded-checkout.md): JSON-RPC para ativar o checkout incorporado.

## Entidades

### Comprador

{{ schema_fields('buyer', 'checkout') }}

### Contexto

Os sinais de contexto são dados provisórios e não oficiais. As empresas DEVEM usar
esses valores quando as entradas verificadas (por exemplo, endereço de entrega) estão ausentes e PODEM
ignore ou rebaixe-os se for inconsistente com sinais de maior confiança
(conta autenticada, detecção de risco) ou restrições regulatórias (exportação
controles). A elegibilidade e a aplicação da política DEVEM ocorrer no momento da finalização da compra usando
dados de transação vinculativos.

{{ schema_fields('context', 'checkout') }}

### Sinais

Dados ambientais fornecidos pela plataforma para apoiar a autorização
e prevenção de abusos. Ao contrário de `context` (preferências declaradas pelo comprador) e `buyer`
(identidade autodeclarada), os valores de sinal NÃO DEVEM ser declarações afirmadas pelo comprador -
plataformas fornecem sinais baseados na observação direta ou na retransmissão
atestados de terceiros verificáveis de forma independente. Veja
[Sinais](overview.md#sinais) para detalhes e privacidade
requisitos.

{{ schema_fields('types/signals', 'checkout') }}

### Atribuição

Contexto de referência e evento de conversão fornecido pela plataforma – IDs de campanha,
identificadores de clique e marcadores de origem/mídia comunicados pela plataforma.
Consulte [Atribuição](overview.md#atribuicao) para obter detalhes e consentimento
requisitos.

{{ schema_fields('types/attribution', 'checkout') }}

### Artigo

#### Solicitação de criação de item

{{ schema_fields('types/item_create_req', 'checkout') }}

#### Solicitação de atualização de item

{{ schema_fields('types/item_update_req', 'checkout') }}

#### Artigo

{{ schema_fields('types/item_resp', 'checkout') }}

### Item de linha

#### Solicitação de criação de item de linha

{{ schema_fields('types/line_item_create_req', 'checkout') }}

#### Solicitação de atualização de item de linha

{{ schema_fields('types/line_item_update_req', 'checkout') }}

#### Item de linha

{{ schema_fields('types/line_item_resp', 'checkout') }}

### Ligação

{{ schema_fields('types/link', 'checkout') }}

#### Tipos de links conhecidos

As empresas **DEVERÃO** fornecer todos os links relevantes para a transação. O
a seguir estão os tipos conhecidos recomendados:

| Tipo | Descrição |
| :----------------- | :------------------------------------------------ |
| `privacy_policy` | Link para a política de privacidade da empresa |
| `terms_of_service` | Link para os termos de serviço da empresa |
| `refund_policy` | Link para a política de reembolso da empresa |
| `shipping_policy` | Link para a política de envio da empresa |
| `faq` | Link para as perguntas mais frequentes da empresa |

As empresas **PODEM** definir tipos personalizados para necessidades específicas de domínio. Plataformas
**DEVE** lidar com tipos desconhecidos normalmente, exibindo-os usando o `title`
campo ou omitindo-os.

### Mensagem

{{ schema_fields('message', 'checkout') }}

### Erro de mensagem

{{ schema_fields('types/message_error', 'checkout') }}

#### Código de erro

{{ schema_fields('types/error_code', 'checkout') }}

### Informações da mensagem

{{ schema_fields('types/message_info', 'checkout') }}

### Aviso de mensagem

{{ schema_fields('types/message_warning', 'checkout') }}

### Pagamento

{{ schema_fields('payment', 'checkout') }}

#### Instrumento de pagamento selecionado

{{ extension_schema_fields('types/payment_instrument.json#/$defs/selected_payment_instrument', 'checkout') }}

### Credencial de pagamento

{{ schema_fields('payment_credential', 'checkout') }}

### Endereço postal

{{ schema_fields('postal_address', 'checkout') }}

### Resposta

{{ extension_schema_fields('capability.json#/$defs/response_schema', 'checkout') }}

### Total {: #totais }

{{ schema_fields('types/total_resp', 'checkout') }}

#### Contrato de Renderização

As empresas são a fonte oficial dos totais apresentados — seu conteúdo e a
ordem de exibição — porque a apresentação correta está sujeita a regiões,
produtos e requisitos regulatórios que a empresa é obrigada a atender (por
exemplo, discriminação de impostos multijurisdicionais, divulgações de taxas
obrigatórias).

As plataformas DEVEM renderizar todas as entradas de nível superior na ordem fornecida:

```python
for entry in totals:
    render_line(entry.display_text, entry.amount)
```

As plataformas PODEM renderizar as sublinhas como detalhes suplementares:

```python
for entry in totals:
    render_line(entry.display_text, entry.amount)
    if entry.lines:
        for sub in entry.lines:
            render_detail_line(sub.display_text, sub.amount)
```

As plataformas NÃO DEVEM interpretar, filtrar, reordenar, agregar ou aplicar
lógica de exibição própria.

Invariantes de `totals[]`:

* Cada entrada traz um `type` e um `amount`. Plataformas DEVEM usar
  `display_text` quando fornecido. Tipos conhecidos têm rótulos de exibição padrão
  como alternativa (ver tabela abaixo); tipos desconhecidos DEVEM incluir `display_text`.
* Os valores são números inteiros assinados — os valores negativos são subtrativos (por exemplo,
  descontos), os valores positivos são aditivos. O sinal É a direção.
* Exatamente um `type: "subtotal"` DEVE estar presente.
* Exatamente um `type: "total"` DEVE estar presente.

#### Verificação

As plataformas NÃO DEVEM substituir os totais fornecidos pela empresa por
valores calculados por conta própria. As plataformas PODEM verificar os totais fornecidos:

```python
assert sum(e.amount for e in totals if e.type != "total") == total_entry.amount
```

Caso a soma computada não corresponda à entrada `type: "total"`, a plataforma
NÃO DEVE alterar a saída renderizada — os totais apresentados pela empresa são
autorizados para exibição. No entanto, as plataformas NÃO DEVEM concluir
autonomamente um checkout com totais incompatíveis. As plataformas DEVEM
rejeitar o checkout ou encaminhá-lo e solicitar a avaliação do comprador via
`continue_url`.

#### Tipos bem conhecidos

| Tipo | Assinar | Etiqueta padrão | Significado |
| ----------------- | ---- | ---------------- | ----------------------------------------- |
| `subtotal` | + | Subtotal | Soma dos preços dos itens de linha |
| `discount` | − | Desconto | Desconto em nível de pedido ou item de linha |
| `items_discount` | − | Descontos em itens | Acúmulo de descontos em itens de linha |
| `fulfillment` | + | Envio | Taxas de envio, entrega ou coleta |
| `tax` | + | Imposto | Encargos fiscais |
| `fee` | + | Taxa | Taxas e sobretaxas |
| `total` | = | Total | Total geral oficial (exatamente um) |

Quando `display_text` é fornecido, as plataformas DEVEM utilizá-lo. Quando
omitido em um tipo bem conhecido, as plataformas DEVEM usar o rótulo padrão
acima. A convenção de sinal para os tipos bem conhecidos é imposta pelo esquema:
tipos subtrativos (`discount`, `items_discount`) DEVEM ter valores negativos;
tipos aditivos (`subtotal`, `fulfillment`, `tax`, `fee`) DEVEM ter valores
não negativos.

O campo `type` é uma string aberta — as empresas PODEM usar valores além do
conjunto bem conhecido. Tipos desconhecidos DEVEM incluir `display_text` (aplicado por esquema)
e o sinal do valor é autodescritivo.

#### Tipos de repetição

Todos os tipos, exceto `subtotal` e `total`, PODEM aparecer várias vezes —
por exemplo, linhas fiscais multijurisdicionais ou taxas discriminadas.

#### Sublinhas (`lines`)

Cada entrada de nível superior PODE incluir uma matriz `lines`. As sublinhas
compartilham a mesma forma básica das entradas de nível superior — `display_text`
e `amount` — fornecendo um detalhamento discriminado sob a entrada pai.

**Invariante:** `sum(lines[].amount)` DEVE ser igual ao `amount` da entrada pai.

A empresa controla o que DEVE ser renderizado (entradas de nível superior)
e o que PODE ser opcionalmente exposto (sublinhas). As plataformas DEVEM
renderizar as sublinhas quando fornecidas.

#### Exemplos

**Imposto dividido, discriminado em nível superior:**

<!-- ucp:example schema=shopping/checkout target=$.totals op=read -->
```json
[
  { "type": "subtotal",    "display_text": "Subtotal",    "amount": 5750 },
  { "type": "fulfillment", "display_text": "Shipping",    "amount": 899 },
  { "type": "tax",         "display_text": "Federal Tax", "amount": 332 },
  { "type": "tax",         "display_text": "State Tax",   "amount": 465 },
  { "type": "total",       "display_text": "Total",       "amount": 7446 }
]
```

**Taxas recolhidas com detalhamento opcional:**

<!-- ucp:example schema=shopping/checkout target=$.totals op=read -->
```json
[
  { "type": "subtotal", "display_text": "Subtotal", "amount": 4999 },
  {
    "type": "fee", "display_text": "Fees", "amount": 549,
    "lines": [
      { "display_text": "Service Fee", "amount": 399 },
      { "display_text": "Recycling Fee", "amount": 150 }
    ]
  },
  { "type": "tax",   "display_text": "Tax",   "amount": 444 },
  { "type": "total", "display_text": "Total", "amount": 5992 }
]
```

**Desconto e crédito em conta — valores negativos:**

<!-- ucp:example schema=shopping/checkout target=$.totals op=read -->
```json
[
  { "type": "subtotal",       "display_text": "Subtotal",       "amount": 10000 },
  { "type": "discount",       "display_text": "Summer Sale",    "amount": -1500 },
  { "type": "tax",            "display_text": "Tax",            "amount": 680 },
  { "type": "account_credit", "display_text": "Account Credit", "amount": -2500 },
  { "type": "total",          "display_text": "Amount Due",     "amount": 6680 }
]
```

### Verificação de resposta BCP {: #ucp-response-checkout-schema }

{{ extension_schema_fields('ucp.json#/$defs/response_checkout_schema', 'checkout') }}

### Confirmação do pedido

{{ schema_fields('order_confirmation', 'checkout') }}

### Resposta de erro <span id="error-response"></span>

{{ schema_fields('types/error_response', 'checkout') }}
