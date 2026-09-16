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

# Capacidade de checkout - Vinculação EP

## Introdução

O Embedded Checkout Protocol (ECP) é uma implementação específica de checkout da
Ligação de transporte do Protocolo Incorporado (EP) do BCP que permite que um
**host** incorpore uma interface de checkout de **empresa**, receba eventos conforme
o comprador interage com o checkout e delegue ações importantes do usuário, como endereço
e seleção de pagamento. O ECP é uma ligação de transporte (como REST) — ela define
**como** se comunicar, não **quais** dados existem.

### Alinhamento conceitual da solicitação de pagamento do W3C

A ECP inspira-se na
**[API de solicitação de pagamento W3C](https://www.w3.org/TR/payment-request/){ target="_blank" }**,
adaptando seu modelo mental para cenários de checkout incorporados. Desenvolvedores familiarizados
com Payment Request reconhecerão padrões semelhantes, embora o modelo de execução
seja diferente:

**Solicitação de pagamento W3C:** Controlado pelo navegador. A empresa se chama `show()` e o
o navegador renderiza uma planilha de pagamento nativa. Os eventos fluem do manipulador de pagamento para
o negócio.

**Check-out incorporado:** Controlado pela empresa. O anfitrião incorpora o negócio
UI de checkout em um iframe/webview. Os eventos fluem bidirecionalmente, com opção
delegação permitindo que o host lide com interações específicas nativamente.<!-- cSpell:ignore paymentmethodchange -->

| Conceito | Solicitação de pagamento W3C | Check-out incorporado |
| :----------------------- | :------------------------------------------ | :-------------------------------------------------------------------------------- |
| **Inicialização** | `new PaymentRequest()` | Carregar contexto incorporado com `continue_url` |
| **UI pronta** | `show()` retorna Promessa | Notificação `ec.start` |
| **Alteração da forma de pagamento** | Evento `paymentmethodchange` | Notificação `ec.payment.change` |
| **Alteração de endereço** | Evento `shippingaddresschange` | `ec.fulfillment.change` e `ec.fulfillment.address_change_request` |
| **Enviar pagamento** | O usuário aceita → `PaymentResponse` | Delegado `ec.payment.credential_request` |
| **Conclusão** | `response.complete()` | Notificação `ec.complete` |
| **Erros/Mensagens** | Rejeição de promessa | Notificação `ec.messages.change` |

**Principal diferença:** Na solicitação de pagamento W3C, o navegador orquestra
o fluxo de pagamento. No Embedded Checkout, a empresa orquestra dentro do
contexto do Embedded Checkout, delegando opcionalmente UI específica (seleção
de método de pagamento, seletor de endereço) ao host para experiências nativas.

## Terminologia e atores

### Funções comerciais

- **Negócios:** O vendedor que fornece bens/serviços e a finalização da compra
    experiência.
- **Comprador:** o usuário final que faz uma compra.

### Componentes Técnicos

- **Host:** O aplicativo que incorpora o checkout (por exemplo, aplicativo AI Agent,
    Super
    Aplicativo, navegador). Responsável pelo **Manipulador de Pagamentos** e usuário
    autenticação.
- **Checkout incorporado:** a interface de checkout da empresa renderizada em um
    iframe ou webview. Responsável pelo fluxo de checkout e criação de pedidos.
- **Payment Handler:** O componente seguro que realiza a autenticação do usuário
    (biométrico/PIN) e emissão de credenciais.

## Requisitos

### Descoberta

A disponibilidade do ECP é sinalizada em dois níveis: a descoberta em nível de
serviço declara a capacidade, e as respostas de checkout confirmam a
disponibilidade e a configuração permitida por sessão.

#### Descoberta de nível de serviço

Quando uma empresa anuncia o transporte `embedded` em seu perfil
`/.well-known/bcp`, ela declara suporte ao Embedded Checkout Protocol.

**Exemplo de descoberta de serviço:**

<!-- ucp:example schema=profile def=business_schema extract=$.services target=$.ucp.services -->
```json
{
    "services": {
        "br.dev.bcp.shopping": [
            {
                "version": "{{ bcp_schema_version }}",
                "transport": "rest",
                "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/rest.openapi.json",
                "endpoint": "https://merchant.example.com/bcp/v1"
            },
            {
                "version": "{{ bcp_schema_version }}",
                "transport": "mcp",
                "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/mcp.openrpc.json",
                "endpoint": "https://merchant.example.com/bcp/mcp"
            },
            {
                "version": "{{ bcp_schema_version }}",
                "transport": "embedded",
                "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/embedded.openrpc.json"
            }
        ]
    }
}
```

Quando `embedded` estiver ausente da definição de serviço, o negócio apenas
suporta continuação de checkout baseada em redirecionamento via `continue_url`.

#### Configuração por checkout

A descoberta em nível de serviço declara que uma empresa oferece suporte ao ECP, mas não
garante que cada sessão de checkout vá habilitá-lo. As empresas **DEVEM** incluir
uma ligação de serviço incorporada com `config.delegate` nas respostas de checkout para
indicar a disponibilidade do ECP e permitir delegações para uma sessão específica.

**Exemplo de resposta de checkout:**

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.ucp.services target=$.ucp.services -->
```json
{
    "id": "checkout_abc123",
    "status": "open",
    "continue_url": "https://merchant.example.com/checkout/abc123",
    "ucp": {
        "version": "{{ bcp_schema_version }}",
        "services": {
            "br.dev.bcp.shopping": [
                {
                    "version": "{{ bcp_schema_version }}",
                    "transport": "embedded",
                    "config": {
                        "delegate": ["payment.credential", "fulfillment.address_change", "window.open"]
                    }
                }
            ]
        },
        "capabilities": {...},
        "payment_handlers": {...}
    }
}
```

A matriz `config.delegate` confirma as delegações que o negócio aceitou para
esta sessão de checkout - a interseção do que o anfitrião solicitou por meio de
`ec_delegate` e o que o negócio permite. Isso pode variar com base em:

- **Conteúdo do carrinho**: alguns produtos podem exigir fluxos de pagamento gerenciados pela empresa
- **Autorização do agente**: agentes autenticados podem receber mais delegações
- **Política comercial**: regras de risco, restrições regionais, etc.

Quando uma ligação de serviço integrada com `config.delegate` estiver presente:

- O ECP está disponível para este checkout via `continue_url`
- `config.delegate` confirma quais delegações o negócio aceitou
- Isso espelha o campo `delegate` no handshake `ec.ready`

Quando a ligação de serviço incorporada está ausente de uma resposta de checkout (mesmo que
a descoberta em nível de serviço anuncie suporte incorporado), o checkout suporta apenas
continuação baseada em redirecionamento via `continue_url`.

### Carregando um URL de checkout incorporado

Quando um host recebe uma resposta de checkout com uma ligação de serviço incorporada, ele
**PODE** iniciar uma sessão ECP carregando o `continue_url` em um
contexto incorporado.

Antes de carregar o contexto incorporado, o host **DEVE**:

1. Verificar `config.delegate` para saber quais delegações estão disponíveis
2. Preparar manipuladores para as delegações que o anfitrião deseja suportar
3. Opcionalmente, preparar credenciais de autenticação, se exigidas pela empresa

Para iniciar a sessão, o host **DEVE** aumentar o `continue_url` com parâmetros
de consulta do ECP usando o prefixo `ec_`.

Todos os parâmetros ECP são passados por meio de string de consulta de URL, e não por cabeçalhos HTTP, para garantir
compatibilidade máxima em diferentes ambientes de incorporação. Os parâmetros usam
o prefixo `ec_` para evitar a poluição do namespace e distinguir claramente os
parâmetros do ECP dos parâmetros de consulta específicos do negócio:

- `ec_version` (string, **OBRIGATÓRIO**): A versão BCP para esta sessão
    (formato: `YYYY-MM-DD`). Deve corresponder à versão da resposta de checkout.
    A versão é negociada na inicialização da sessão e **DEVE** permanecer
    constante durante toda a sessão do ECP - nenhuma das partes pode alterar
    a versão após o aperto de mão.
- `ec_auth` (string, **OPCIONAL**): Token de autenticação em ambiente definido pelo negócio
    formato
- `ec_delegate` (string, **OPCIONAL**): lista de delegações delimitada por vírgulas
    o host deseja lidar. **DEVE** ser um subconjunto de `config.delegate`
    da ligação de serviço incorporada.
- `ec_color_scheme` (string, **OPCIONAL**): A preferência do esquema de cores para
    a IU de checkout. Valores válidos: `light`, `dark`. Quando não fornecido, o
    O Checkout incorporado segue as preferências do sistema.

#### Autenticação

**Formato de token:**

- O formato do parâmetro `auth` é totalmente definido pelo negócio
- Os formatos comuns incluem JWT, tokens OAuth, chaves de API ou identificadores de sessão
- As empresas **DEVEM** documentar o formato de token esperado e o processo de validação

**Exemplo (informativo - baseado em JWT):**

```text
// One possible implementation using JWT
{
  "alg": "HS256",
  "typ": "JWT"
}
{
  "iat": 1234567890,
  "exp": 1234568190,
  "jti": "unique-id",
  // ... business-specific claims ...
}
```

As empresas **DEVEM** validar a autenticação de acordo com seus requisitos de
segurança.

**Exemplo de inicialização com autenticação:**

```text
https://example.com/checkout/abc123?ec_version=2026-01-11&ec_auth=eyJ...
```

Observação: todos os valores dos parâmetros de consulta devem ser codificados em URL corretamente de acordo com RFC 3986.

#### Delegação

O parâmetro opcional `ec_delegate` declara quais operações o host deseja
tratar nativamente, em vez de deixar o comprador lidar com elas na UI do
Embedded Checkout. Cada identificador de delegação é mapeado para uma mensagem
`_request` correspondente, seguindo um padrão consistente: `ec.{delegation}_request`

**Exemplos de identificadores de delegação:**

| Valor `ec_delegate` | Mensagem correspondente |
| ---------------------------- | --------------------------------------- |
| `payment.instruments_change` | `ec.payment.instruments_change_request` |
| `payment.credential` | `ec.payment.credential_request` |
| `fulfillment.address_change` | `ec.fulfillment.address_change_request` |
| `window.open` | `ec.window.open_request` |

As extensões definem seus próprios identificadores de delegação; veja cada extensão
especificação das opções disponíveis.

```text
?ec_version=2026-01-11&ec_delegate=payment.instruments_change,payment.credential,fulfillment.address_change,window.open
```

#### Esquema de cores

O parâmetro opcional `ec_color_scheme` permite que o host especifique qual cor
esquema que o Embedded Checkout deve usar, permitindo consistência visual entre
o aplicativo host e a UI de checkout.

**Valores válidos:**

| Valor | Descrição |
| :------ | :---------------------------------------------------------------- |
| `light` | Use esquema de cores claras (fundo claro, texto escuro) |
| `dark` | Use esquema de cores escuras (fundo escuro, texto claro) |

**Comportamento padrão:**

Quando não for fornecido `ec_color_scheme`, o Checkout Incorporado poderá
use a preferência de sistema do comprador por meio do
[`prefers-color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)
consulta de mídia ou o
[`Sec-CH-Prefers-Color-Scheme`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Sec-CH-Prefers-Color-Scheme)
Dica do cliente HTTP e **DEVE** ouvir as alterações e atualizar de acordo.

**Notas de implementação:**

- Por padrão, o Checkout Incorporado **DEVE** respeitar a preferência de esquema
  de cores do sistema do comprador e ouvir as alterações para atualizar adequadamente
- Quando `ec_color_scheme` é fornecido explicitamente, ele **DEVE** substituir a
  preferência do sistema, ser aplicado imediatamente após o carregamento e
  permanecer em vigor durante toda a sessão.
- As empresas **PODEM** ignorar valores não suportados

**Exemplo:**

```text
https://example.com/checkout/abc123?ec_version=2026-01-11&ec_color_scheme=dark
```

#### Negociação de Delegação

A delegação segue uma cadeia estreita desde a política comercial até a aceitação final:

```text
config.delegate ⊇ ec_delegate ⊇ ec.ready delegate
```

1. **O negócio permite** (`config.delegate` na resposta do checkout): O conjunto de
    delegações as licenças comerciais para esta sessão de checkout
2. **Solicitações de host** (parâmetro URL `ec_delegate`): O subconjunto que o host deseja
    para lidar nativamente
3. **ECP aceita** (`delegate` em `ec.ready`): O subconjunto final do Embedded
    O checkout irá realmente delegar

Cada estágio é um subconjunto do anterior:

- O anfitrião **DEVE** solicitar apenas delegações presentes em `config.delegate`
- A empresa **NÃO DEVE** aceitar delegações não presentes em
    `config.delegate` e **DEVE** confirmar as delegações aceitas em `ec.ready`

### Contrato de Delegação

A delegação cria um contrato vinculativo entre o host e o Embedded Checkout.
No entanto, o Embedded Checkout **PODE** restringir a delegação a hosts
autenticados ou aprovados com base na política comercial.

#### Aceitação de Delegação

O Embedded Checkout determina quais delegações honrar com base em:

- Status de autenticação (via parâmetro `ec_auth`)
- nível de autorização do host
- Política empresarial

O Checkout Incorporado **DEVE** indicar as delegações aceitas na solicitação
`ec.ready`, por meio do campo `delegate` (ver [`ec.ready`](#ecready)). Se uma
delegação solicitada não for aceita, o Embedded Checkout **DEVE** tratar essa
ação usando sua própria UI.

#### Requisitos de vinculação

**Assim que a delegação for aceita**, ambas as partes firmam um contrato vinculativo:

**Responsabilidades do Checkout incorporado:**

1. **DEVE** disparar a mensagem `{action}_request` apropriada quando essa ação for
    acionada
2. **DEVE** aguardar a resposta do anfitrião antes de prosseguir
3. **NÃO DEVE** mostrar sua própria UI para essa ação delegada

**Responsabilidades do anfitrião:**

1. **DEVE** responder a cada mensagem `{action}_request` que receber
2. **DEVE** responder com um erro apropriado se o usuário cancelar
3. **DEVE** mostrar estados de carregamento/processamento ao lidar com a delegação

#### Fluxo de delegação

1. **Solicitação**: o Checkout Incorporado envia uma mensagem
    `ec.{domain}.{action}_request` com o estado atual (inclui `id`)
2. **UI nativa**: o host apresenta UI nativa para a ação delegada
3. **Resposta**: o host envia de volta uma resposta JSON-RPC com `id` correspondente e
    `result` ou `error`
4. **Atualização**: o Embedded Checkout atualiza seu estado e pode enviar
    notificações de alteração subsequentes

Consulte [Extensão de pagamento](#extensao-de-pagamento),
[Extensão de Cumprimento](#extensao-de-cumprimento) e
[Extensão de janela](#extensao-da-janela) para
detalhes de delegação específicos do domínio.

### Restrições de navegação

Quando o checkout é renderizado em modo incorporado, a implementação **DEVE**
evitar a navegação para fora do checkout, a fim de manter uma experiência de checkout focada.
A visualização incorporada tem como objetivo oferecer um fluxo de checkout, não um
fluxo de navegação de uso geral.

**Requisitos de navegação:**

- O checkout incorporado **DEVE** bloquear ou interceptar tentativas de navegação para
    URLs fora do fluxo de checkout
- O checkout incorporado **DEVE** remover ou desativar elementos de UI que
    permitam sair do checkout (por exemplo, links externos, barras de navegação)
- O incorporador **PODE** implementar restrições de navegação adicionais no
    nível do contêiner

**Exceções permitidas:** Os seguintes cenários de navegação **PODEM** ser permitidos
quando necessário para a conclusão do checkout:

- Redirecionamentos de provedores de pagamento: fluxos de pagamento externos
- Verificação 3D Secure: quadros de autenticação de cartão e redirecionamentos
- Autorização bancária: open banking ou fluxos de autorização similares
- Verificação de identidade: verificações de conformidade KYC/AML quando necessário

Essas exceções **DEVERÃO** retornar o usuário ao fluxo de checkout após
conclusão.

## Transporte e mensagens

O ECP usa a camada de transporte EP compartilhada. Veja
[Protocolo incorporado – Transporte e mensagens](embedded-protocol.md#transporte-e-mensagens)
para formato de mensagem, tipos de mensagem e convenções de tratamento de resposta.

O `ucp.version` em todas as respostas **DEVE** ecoar o `ec_version` negociado
durante a inicialização da sessão e confirmado pelo host no `ec.ready`
resposta. A versão está vinculada à sessão — **NÃO DEVE** ser alterada durante o período
da sessão do ECP.

### Canais de Comunicação

O ECP segue o modelo de canal de comunicação EP compartilhado. Veja
[Protocolo Incorporado – Canais de Comunicação](embedded-protocol.md#canais-de-comunicacao)
para o padrão geral.

Para hosts nativos, os globais específicos do checkout são:

- `window.EmbeddedCheckoutProtocolConsumer` (preferencial)
- `window.webkit.messageHandlers.EmbeddedCheckoutProtocolConsumer`
- `window.EmbeddedCheckoutProtocol` (Host → Check-out incorporado)

## Referência da API de mensagens

### Categorias de mensagens

#### Mensagens principais

As mensagens principais são definidas pela especificação ECP e **DEVEM** ser suportadas por
todas as implementações. Todas as mensagens são enviadas do Embedded Checkout para o host.

| Categoria | Finalidade | Padrão | Mensagens principais |
| :---------------- | :---------------------------------------------------------------------------------- | :----------- | :----------------------------------------------------------------------------------------------------------------- |
| **Aperto de mão** | Estabeleça conexão entre o host e o Embedded Checkout | Solicitação | `ec.ready` |
| **Autenticação**| Comunique trocas de dados de autenticação entre o Embedded Checkout e o host.   | Solicitação | `ec.auth` |
| **Ciclo de vida** | Informar sobre transições de estado de checkout | Notificação | `ec.start`, `ec.complete` |
| **Mudança de estado** | Informar sobre alterações nos campos de checkout | Notificação | `ec.line_items.change`, `ec.buyer.change`, `ec.payment.change`, `ec.messages.change`, `ec.totals.change` |
| **Erro de sessão** | Sinalizar um erro no nível da sessão não relacionado ao recurso de checkout | Notificação | `ec.error` |

#### Mensagens de extensão

As extensões **PODEM** estender o protocolo incorporado definindo mensagens adicionais.
As mensagens de extensão **DEVEM** seguir a convenção de nomenclatura:

- **Notificações**: `ec.{domain}.change` — notificações de mudança de estado (sem
    `id`)
- **Solicitações de delegação**: `ec.{domain}.{action}_request` — requer
    resposta (tem `id`)

Onde:

- `{domain}` corresponde ao identificador de domínio da descoberta (por exemplo, `payment`,
    `fulfillment`, `window`)
- `{action}` descreve a ação específica que está sendo delegada (por exemplo,
    `instruments_change`, `address_change`)
- O sufixo `_request` sinaliza que este é um ponto de delegação que requer uma resposta

### Mensagens de aperto de mão

#### `ec.ready`

Após a renderização, o Embedded Checkout **DEVE** transmitir a prontidão para o
contexto pai usando a mensagem `ec.ready`. Esta mensagem inicializa um canal
de comunicação seguro entre o host e o Embedded Checkout, comunica quais
delegações foram aceitas, informa se é necessária uma troca de autenticação
adicional e permite que o host forneça um estado adicional, somente para
exibição, para o checkout — estado que não foi comunicado por meio das ações
de checkout do BCP.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `delegate` (array de strings, **OBRIGATÓRIO**): Lista de identificadores de
        delegação aceitos pelo Checkout Incorporado. **DEVE** ser um subconjunto de
        tanto `ec_delegate` (o que o host solicitou) quanto `config.delegate` da
        resposta de checkout (o que o negócio permite). Uma matriz vazia significa
        que nenhuma delegação foi aceita.
    - `auth` (objeto, **OPCIONAL**): Quando o parâmetro URL `ec_auth` não é suficiente
        nem aplicável devido a considerações adicionais, a empresa pode solicitar
        autorização durante o handshake inicial especificando a string `type`
        dentro deste objeto. Este valor de string `type` é um espelho do conteúdo da carga útil
        incluído em [`ec.auth`](#ecauth).

**Exemplo de mensagem (nenhuma delegação aceita):**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "method": "ec.ready",
    "params": {
        "delegate": [],
        "auth": {
            "type": "oauth"
        }
    }
}
```

**Exemplo de mensagem (delegações aceitas):**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "method": "ec.ready",
    "params": {
        "delegate": ["payment.credential", "fulfillment.address_change", "window.open"],
        "auth": {
            "type": "oauth"
        }
    }
}
```

A mensagem `ec.ready` é uma solicitação, o que significa que o host **DEVE** responder
para completar o aperto de mão.

- **Direção:** Host → Check-out incorporado
- **Tipo:** Resposta
- **Carga útil do resultado:**
    - `ucp` (objeto, **OBRIGATÓRIO**): metadados do protocolo BCP. O `version`
        confirma o `ec_version` negociado e `status` **DEVERÁ** ser
        `"success"`. Esta versão é vinculada à sessão — o host confirma
        explicitamente a versão do protocolo aqui e ela **NÃO DEVE** mudar
        durante a sessão.
    - `upgrade` (objeto, **OPCIONAL**): Um objeto que descreve como o Checkout
        Incorporado deve atualizar o canal de comunicação que usa para se
        comunicar com o anfitrião. Quando presente, o host **NÃO DEVE** incluir
        `credential` — o canal será restabelecido e qualquer credencial
        enviada aqui será descartada.
    - `credential` (string, **OPCIONAL**): Os dados de autorização solicitados,
        que podem estar na forma de um token OAuth, JWT, chaves de API, etc. **DEVE** ser
        definido se `auth` estiver presente na solicitação. **NÃO DEVE** ser definido se
        `upgrade` está presente.
    - `checkout` (objeto, **OPCIONAL**): Estado adicional somente de exibição para
        o checkout que não foi comunicado nas ações de checkout do BCP. Isso
        é usado para preencher a UI de checkout e só pode ser usado para preencher
        os seguintes campos, sob condições específicas:
        - `payment.instruments`: pode ser sobrescrito quando o Host e o
            Checkout Incorporado aceitam a delegação `payment.instruments_change`.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=response -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "credential": "fake_identity_linking_oauth_token"
    }
}
```

Os hosts **PODEM** responder com um campo `upgrade` para atualizar a comunicação
canal entre o host e o Embedded Checkout. Atualmente, este objeto suporta apenas
um campo `port`, que **DEVE** ser um objeto `MessagePort` e **DEVE** ser
transferido para o contexto de checkout incorporado (por exemplo, com `{transfer: [port2]}`
na chamada `iframe.contentWindow.postMessage()` do host):

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=response -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "upgrade": {
            "port": "[Transferable MessagePort]"
        }
    }
}
```

Quando o host responde com um objeto `upgrade`, o Checkout Incorporado **DEVE**
descartar qualquer outra informação da mensagem, enviar uma nova mensagem `ec.ready`
através do canal de comunicação atualizado e aguarde uma nova resposta. Todos
mensagens subsequentes **DEVEM** ser enviadas somente pela comunicação atualizada
canal.

O host **PODE** também responder com um objeto `checkout`, que será usado para
preencher a UI de checkout de acordo com o contrato de delegação entre o host e
negócio.

**Exemplo de mensagem: Fornecimento de instrumentos de pagamento, incluindo exibição
informações:**

O exemplo abaixo usa o manipulador padrão do BCP,
[`br.dev.bcp.pix`](pix-payment-handler.md), cuja cobrança já vem
totalmente resolvida nesta etapa — ao contrário de manipuladores baseados
em tokenização (cartão, carteiras digitais), que anexam a credencial depois,
via `ec.payment.credential_request` (veja abaixo).

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.result.checkout.payment target=$.payment -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "checkout": {
            "payment": {
                // The instrument structure is defined by the handler's instrument schema
                "instruments": [
                    {
                        "id": "payment_instrument_123",
                        "handler_id": "pix_recebedor_001",
                        "type": "pix",
                        "selected": true,
                        "display": {
                            "payee_name": "Loja Exemplo LTDA",
                            "description": "Pix de R$ 249,90 · expira em 30 minutos"
                        },
                        "credential": {
                            "type": "pix_charge",
                            "provider_payment_id": "psp_9f2c1a",
                            "copia_e_cola": "00020126580014br.gov.bcb.pix...6304ABCD",
                            "expires_at": "2026-07-20T15:30:00-03:00"
                        }
                    }
                ]
            }
        }
    }
}
```

**Exemplo de resposta de erro:**

Se o host não puder completar o handshake (por exemplo, falha na validação de origem ou
violação do estado do protocolo), ele **DEVE** responder com um resultado `error_response`:

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
        "messages": [
            {
                "type": "error",
                "code": "security_error",
                "content": "Host origin validation failed.",
                "severity": "unrecoverable"
            }
        ]
    }
}
```

Quando o host responde com um erro, a sessão não pode prosseguir. O anfitrião
**DEVE** eliminar o contexto incorporado e **PODE** redirecionar o comprador para
`continue_url` se presente. O Checkout Incorporado **NÃO DEVE** ser enviado posteriormente
mensagens após receber um erro de handshake.

### Autenticação

#### `ec.auth`

`ec.auth` implementa o padrão de autenticação EP compartilhado — veja
[Protocolo Incorporado - Autenticação](embedded-protocol.md#autenticacao) para
o contrato de solicitação/resposta, exemplos e fluxo de escalonamento de erros.

- **Método:** `ec.auth`
- **Direção:** Checkout Incorporado → Host (solicitação); Host → Check-out incorporado (resposta)

Quando o escalonamento de erros é necessário, o Embedded Checkout **DEVE** emitir uma
Notificação `ec.error` de acordo com o
[padrão de erro de sessão](embedded-protocol.md#erro-de-sessao).

### Mensagens do ciclo de vida

As notificações do ciclo de vida seguem o padrão EP compartilhado — consulte
[Protocolo incorporado - Ciclo de vida](embedded-protocol.md#ciclo-de-vida). Todo o ciclo de vida
notificações carregam o objeto `checkout` completo como carga útil.

#### `ec.start`

Sinaliza que o checkout está visível e pronto para interação. Enviado depois de um
handshake `ec.ready` bem-sucedido.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado atual completo do checkout.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.start",
    "params": {
        "checkout": {
            "id": "checkout_123",
            "status": "incomplete",
            "messages": [
                {
                    "type": "error",
                    "code": "missing",
                    "path": "$.buyer.shipping_address",
                    "content": "Shipping address is required",
                    "severity": "recoverable"
                }
            ],
            "totals": [ ... ],
            "line_items": [ ... ],
            "buyer": { ... },
            "payment": { ... }
            // ... other checkout fields
        }
    }
}
```

#### `ec.complete`

Indica a conclusão bem-sucedida da finalização da compra.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado final do checkout,
        incluindo o objeto `order` resultante.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.complete",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // ... other checkout fields
            "order": {
                "id": "ord_99887766",
                "permalink_url": "https://merchant.com/orders/ord_99887766"
            }
        }
    }
}
```

### Mensagens de mudança de estado

As notificações de mudança de estado seguem o padrão EP compartilhado – consulte
[Protocolo Incorporado - Mudança de Estado](embedded-protocol.md#mudanca-de-estado). Todos os estados
notificações de alteração são enviadas do Embedded Checkout para o host e transportadas
o objeto `checkout` completo como sua carga útil.

#### `ec.line_items.change`

Os itens de linha foram modificados (quantidade alterada, itens adicionados/removidos).

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado atual completo do checkout.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.line_items.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the updated line items and totals
            "totals": [ ... ],
            "line_items": [ ... ]
            // ...
        }
    }
}
```

#### `ec.buyer.change`

As informações do comprador foram atualizadas (e-mail, telefone, endereço).

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado atual completo do checkout.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.buyer.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the updated buyer information
            "buyer": { ... }
            // ...
        }
    }
}
```

#### `ec.messages.change`

As mensagens de checkout foram atualizadas. As mensagens incluem erros, avisos e
avisos informativos sobre o estado do checkout.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado atual completo do checkout.

**Exemplo de mensagem:**

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.params.checkout.messages target=$.messages -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.messages.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            "messages": [
                {
                    "type": "error",
                    "code": "invalid_address",
                    "path": "$.buyer.shipping_address",
                    "content": "We cannot ship to this address",
                    "severity": "recoverable"
                },
                {
                    "type": "info",
                    "code": "free_shipping",
                    "content": "Free shipping applied!"
                }
            ]
            // ...
        }
    }
}
```

#### `ec.totals.change`

Os totais de checkout foram atualizados. Esta mensagem cobre todas as alterações totais de linha
incluindo impostos, taxas, descontos e custos de cumprimento – muitos dos quais não têm
outra mensagem de alteração específica do domínio. As empresas **DEVEM** enviar esta mensagem
sempre que `checkout.totals` for alterado por qualquer motivo.

Quando uma alteração também aciona uma mensagem específica do domínio (por exemplo,
`ec.line_items.change`, `ec.buyer.change` ou `ec.payment.change`), o negócio
**DEVE** enviar primeiro a mensagem específica do domínio e, em seguida, enviar
`ec.totals.change`.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado atual completo do checkout.

**Exemplo de mensagem:**

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.params.checkout.totals target=$.totals -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.totals.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the updated totals
            "totals": [
                {
                    "type": "subtotal",
                    "display_text": "Subtotal",
                    "amount": 4000
                },
                {
                    "type": "fulfillment",
                    "display_text": "Shipping",
                    "amount": 599
                },
                {
                    "type": "tax",
                    "display_text": "Tax",
                    "amount": 382
                },
                {
                    "type": "total",
                    "display_text": "Total",
                    "amount": 4981
                }
            ]
            // ...
        }
    }
}
```

#### `ec.payment.change`

O estado do pagamento foi atualizado. Veja o
[Extensão de pagamento](#extensao-de-pagamento) para obter a documentação completa.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout` (objeto, **OBRIGATÓRIO**): O estado atual completo do checkout.

### Mensagens de erro de sessão

#### `ec.error`

`ec.error` implementa o padrão de erro de sessão EP compartilhada — veja
[Protocolo incorporado - erro de sessão](embedded-protocol.md#erro-de-sessao) para o
especificação de carga útil e requisitos de manipulação de host.

## Extensão de pagamento

A extensão de pagamento define como um anfitrião pode usar notificações de mudança de estado e
solicitações de delegação para orquestrar fluxos de escalonamento de usuários. Quando um URL de checkout
inclui `ec_delegate=payment.instruments_change,payment.credential`, o host
ganha controle sobre a seleção do método de pagamento e aquisição de tokens, fornecendo
atualizações de estado no Embedded Checkout em resposta.

### Visão geral do pagamento e escolha do anfitrião

A delegação de pagamento permite dois padrões diferentes de orquestração do host
e check-out incorporado:

**Opção A: o host delega ao Embedded Checkout** O host NÃO inclui
delegação de pagamento na URL. O Embedded Checkout lida com a seleção de pagamento
e processamento usando sua própria UI e fluxos de pagamento. Este é o padrão,
fluxo não delegado.

**Opção B: O anfitrião assume o controle** O anfitrião inclui
`ec_delegate=payment.instruments_change,payment.credential` na URL de checkout,
informando o Embedded Checkout para delegar UI de pagamento e aquisição de token para
o anfitrião. Quando delegado:

- **Responsabilidades do Checkout incorporado**:
    - Exibir a forma de pagamento atual com uma intenção de alteração (por exemplo, "Alterar
        botão Método de pagamento")
    - Aguarde resposta à mensagem `ec.payment.credential_request`
        antes de enviar o pagamento
- **Responsabilidades do anfitrião**:
    - Responder ao `ec.payment.instruments_change_request` renderizando
        UI nativa para o comprador selecionar métodos de pagamento alternativos e, em seguida,
        responder com o método selecionado
    - Responder ao `ec.payment.credential_request` obtendo um pagamento
        token para o método de pagamento selecionado e enviar esse token para o
        Check-out incorporado

### Referência da API de mensagens de pagamento

#### `ec.payment.change`

Informa ao anfitrião que algo mudou na seção de pagamento do
UI de checkout, como uma nova forma de pagamento sendo selecionada.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout`: O último estado do checkout

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.payment.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the updated payment details
            "payment": {
                "instruments": [
                    {
                        "id": "payment_instrument_123",
                        "selected": true
                        // ... additional instrument fields
                    }
                ]
            }
            // ...
        }
    }
}
```

#### `ec.payment.instruments_change_request`

Solicita que o host apresente a IU de seleção do instrumento de pagamento.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `checkout`: O último estado do checkout

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "id": "payment_instruments_change_request_1",
    "method": "ec.payment.instruments_change_request",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the current payment details
            "payment": { ... }
            // ...
        }
    }
}
```

O anfitrião **DEVE** responder com um erro ou com o pagamento recém-selecionado
instrumentos. Em respostas bem-sucedidas, o anfitrião **DEVE** responder com uma resposta parcial
atualização para o objeto `checkout`, sendo atualizado apenas o campo `payment.instruments`. O check-out incorporado **DEVE**
trate esta atualização como uma mudança no estilo PUT, substituindo totalmente o estado existente
para os campos fornecidos, em vez de tentar mesclar os novos dados com
estado existente.

- **Direção:** Host → Check-out incorporado
- **Tipo:** Resposta
- **Carga útil:**
    - `ucp`: metadados do protocolo BCP com `status: "success"`
    - `checkout`: A atualização a ser aplicada ao objeto checkout

**Exemplo de resposta de sucesso:**

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.result.checkout.payment target=$.payment -->
```json
{
    "jsonrpc": "2.0",
    "id": "payment_instruments_change_request_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "checkout": {
            "payment": {
                // The instrument structure is defined by the handler's instrument schema
                "instruments": [
                    {
                        "id": "payment_instrument_123",
                        "handler_id": "merchant_psp_handler_123",
                        "type": "card",
                        "selected": true,
                        "display": {
                            "brand": "visa",
                            "expiry_month": 12,
                            "expiry_year": 2026,
                            "last_digits": "1111",
                            "description": "Visa •••• 1111",
                            "card_art": "https://host.com/cards/visa-gold.png"
                        }
                        // No `credential` yet; it will be attached in the `ec.payment.credential_request` response
                    }
                ]
            }
        }
    }
}
```

**Exemplo de resposta de erro:**

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result -->
```json
{
    "jsonrpc": "2.0",
    "id": "payment_instruments_change_request_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
        "messages": [
            {
                "type": "error",
                "code": "abort_error",
                "content": "User closed the payment sheet without authorizing.",
                "severity": "recoverable"
            }
        ]
    }
}
```

#### `ec.payment.credential_request`

Solicita uma credencial para o instrumento de pagamento selecionado durante a finalização da compra
submissão.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `checkout`: O último estado do checkout

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "id": "payment_credential_request_1",
    "method": "ec.payment.credential_request",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the current payment details
            "payment": {
                "instruments": [
                    {
                        "id": "payment_instrument_123",
                        "selected": true
                        // ... additional instrument fields
                    }
                ]
            }
            // ...
        }
    }
}
```

O host **DEVE** responder com um erro ou com a credencial para o
instrumento de pagamento selecionado. Em respostas bem-sucedidas, o anfitrião **DEVE** fornecer um
atualização parcial do objeto `checkout`, atualizando o instrumento com
`selected: true` com o novo campo `credentials`. O check-out incorporado
**DEVE** tratar esta atualização como uma mudança no estilo PUT, substituindo totalmente o
estado existente para `payment.instruments`, em vez de tentar mesclar o
novos dados com o estado existente.

- **Direção:** Host → Check-out incorporado
- **Tipo:** Resposta
- **Carga útil:**
    - `ucp`: metadados do protocolo BCP com `status: "success"`
    - `checkout`: A atualização a ser aplicada ao objeto checkout

**Exemplo de resposta de sucesso:**

<!-- ucp:example schema=shopping/checkout op=read direction=response extract=$.result.checkout.payment target=$.payment -->
```json
{
    "jsonrpc": "2.0",
    "id": "payment_credential_request_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "checkout": {
            "payment": {
                "instruments": [
                    {
                        "id": "payment_instrument_123",
                        "handler_id": "merchant_psp_handler_123",
                        "type": "card",
                        "selected": true,
                        "display": {
                            "brand": "visa",
                            "expiry_month": 12,
                            "expiry_year": 2026,
                            "last_digits": "1111",
                            "description": "Visa •••• 1111",
                            "card_art": "https://host.com/cards/visa-gold.png"
                        },
                        // The credential structure is defined by the handler's instrument schema
                        "credential": {
                            "type": "token",
                            "token": "tok_123"
                        }
                    }
                ]
            }
        }
    }
}
```

**Exemplo de resposta de erro:**

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result -->
```json
{
    "jsonrpc": "2.0",
    "id": "payment_credential_request_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
        "messages": [
            {
                "type": "error",
                "code": "abort_error",
                "content": "User closed the payment sheet without authorizing.",
                "severity": "recoverable"
            }
        ]
    }
}
```

**Responsabilidades do anfitrião durante a delegação de token de pagamento:**

1. **Confirmação:** O organizador exibe a UI de pagamento confiável (folha de pagamento/
    Alerta biométrico). O host **NÃO DEVE** liberar silenciosamente um token baseado
    exclusivamente na mensagem.
2. **Auth:** o host realiza a autorização do usuário por meio do manipulador de pagamento.
3. **Integração AP2 (Opcional):** Se `ucp.ap2_mandate` estiver ativo (ver
    **[extensão AP2](https://ap2-extension.org/)**), o host gera o
    `payment_mandate` aqui usando uma interface de usuário confiável.

## Extensão de Cumprimento

A extensão de cumprimento define como um host pode delegar a seleção de endereço para
fornecer uma experiência nativa de seletor de endereço. Quando um URL de checkout inclui
`ec_delegate=fulfillment.address_change`, o host ganha controle sobre o envio
seleção de endereço, fornecendo atualizações de endereço para o Embedded Checkout em
resposta.

### Visão geral do cumprimento e escolha do anfitrião

A delegação de cumprimento permite dois padrões diferentes:

**Opção A: o host delega ao Embedded Checkout** O host NÃO inclui
delegação de cumprimento no URL. O Embedded Checkout lida com a entrada de endereço
usando sua própria interface de usuário e formulários de endereço. Este é o fluxo padrão não delegado.

**Opção B: o anfitrião assume o controle** O anfitrião inclui
`ec_delegate=fulfillment.address_change` na URL de Checkout, informando o
Checkout incorporado para delegar a UI de seleção de endereço ao host. Quando delegado:

**Responsabilidades do Checkout incorporado**:

- Exibir o endereço de entrega atual com uma intenção de alteração (por exemplo, "Alterar
    botão "Endereço")
- Enviar `ec.fulfillment.address_change_request` quando o comprador acionar endereço
    mudar
- Atualize as opções de envio com base no endereço retornado pelo anfitrião

**Responsabilidades do anfitrião**:

- Responda ao `ec.fulfillment.address_change_request` renderizando nativo
    UI para o comprador selecionar ou inserir um endereço de entrega
- Responder com o endereço selecionado no formato BCP PostalAddress

### Referência da API de mensagens de cumprimento

#### `ec.fulfillment.change`

Informa ao anfitrião que os detalhes de cumprimento foram alterados na UI de
finalização da compra.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `checkout`: O último estado do checkout

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.fulfillment.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the updated fulfillment details
            "fulfillment": { ... }
            // ...
        }
    }
}
```

#### `ec.fulfillment.address_change_request`

Solicita que o host apresente a UI de seleção de endereço para um método de
cumprimento de remessa.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `checkout`: O último estado do checkout

**Exemplo de mensagem:**

<!-- ucp:example schema=shopping/checkout op=update direction=request extract=$.params.checkout.fulfillment target=$.fulfillment -->
```json
{
    "jsonrpc": "2.0",
    "id": "fulfillment_address_change_request_1",
    "method": "ec.fulfillment.address_change_request",
    "params": {
        "checkout": {
            "id": "checkout_123",
            // The entire checkout object is provided, including the current fulfillment details
            "fulfillment": {
                "methods": [
                    {
                        "id": "method_1",
                        "type": "shipping",
                        "selected_destination_id": "address_123",
                        "destinations": [
                            {
                                "id": "address_123",
                                "street_address": "456 Old Street"
                                // ...
                            }
                        ]
                        // ...
                    }
                ]
            }
            // ...
        }
    }
}
```

O host **DEVE** responder com um erro ou com o endereço recém-selecionado.
Em respostas bem-sucedidas, o anfitrião **DEVE** responder com um objeto
`fulfillment.methods` atualizado, atualizando os campos `selected_destination_id`
e `destinations` dos métodos de cumprimento e preservando o restante do estado
existente. O Embedded Checkout **DEVE** tratar esta atualização como uma mudança
no estilo PUT, substituindo totalmente o estado existente de
`fulfillment.methods`, em vez de tentar mesclar os novos dados com o estado
existente.

- **Direção:** Host → Check-out incorporado
- **Tipo:** Resposta
- **Carga útil:**
    - `ucp`: metadados do protocolo BCP com `status: "success"`
    - `checkout`: A atualização a ser aplicada ao objeto checkout

**Exemplo de resposta de sucesso:**

<!-- ucp:example schema=shopping/checkout op=update direction=request extract=$.result.checkout.fulfillment target=$.fulfillment -->
```json
{
    "jsonrpc": "2.0",
    "id": "fulfillment_address_change_request_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "checkout": {
            "fulfillment": {
                "methods": [
                    {
                        "id": "method_1",
                        "type": "shipping",
                        "selected_destination_id": "address_789",
                        "destinations": [
                            {
                                "id": "address_789",
                                "first_name": "John",
                                "last_name": "Doe",
                                "street_address": "123 New Street"
                            }
                        ]
                    }
                ]
            }
        }
    }
}
```

**Exemplo de resposta de erro:**

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result -->
```json
{
    "jsonrpc": "2.0",
    "id": "fulfillment_address_change_request_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
        "messages": [
            {
                "type": "error",
                "code": "abort_error",
                "content": "User cancelled address selection.",
                "severity": "recoverable"
            }
        ]
    }
}
```

### Formato de endereço

O objeto de endereço usa o formato [Endereço Postal](site:specification/checkout/#endereçopostal)
do BCP:

### Endereço postal

{{ schema_fields('postal_address', 'embedded-checkout') }}

## Extensão da janela

A extensão da janela define como o Embedded Checkout notifica o host quando
o comprador ativa um link apresentado pela empresa. Quando um URL de checkout
inclui `ec_delegate=window.open`, o host **DEVE** lidar com cada
`ec.window.open_request` e confirmar a solicitação.

Isto é distinto de
[Restrições de navegação](#restricoes-de-navegacao), que o Embedded Checkout
impõe incondicionalmente para impedir a navegação em páginas não relacionadas.

### Visão geral da janela e escolha do host

A delegação de janela permite dois padrões diferentes:

**Opção A: o host delega ao Embedded Checkout** O host NÃO inclui
`window.open` em `ec_delegate`. O Embedded Checkout lida com a apresentação do link
usando sua própria UI embutida. Este é o fluxo padrão não delegado.

**Opção B: O anfitrião assume o controle** O anfitrião inclui
`ec_delegate=window.open` na URL do Checkout, informando o Checkout Embutido
enviar `ec.window.open_request` quando o comprador ativar um link. Quando delegado:

**Responsabilidades do Checkout incorporado**:

- **DEVE** enviar `ec.window.open_request` quando o comprador ativar um link
    apresentado pela empresa

**Responsabilidades do anfitrião**:

- **DEVE** validar se a URL solicitada usa o esquema `https`
- **DEVE** aplicar políticas de segurança de host adicionais (por exemplo, verificar
    origens)
- **DEVE** apresentar o conteúdo ao comprador para cada solicitação aprovada
    (por exemplo, em um modal, nova guia ou similar)
- **DEVE** responder com um resultado de sucesso JSON-RPC quando a solicitação foi
    processado ou um erro `window_open_rejected_error` se a política do host impediu
    a navegação
- **PODE** notificar o comprador se a solicitação for rejeitada

Ao aceitar a delegação `window.open`, o anfitrião assume a responsabilidade por
lidar com as interações do link do comprador. O check-out incorporado **NÃO DEVE**
apresentar sua própria UI para o link.

A carga útil `ec.window.open_request` contém apenas o URL. Anfitriões que precisam
contexto mais rico (por exemplo, tipo de link ou rótulo) **PODE** fazer referência cruzada ao solicitado
URL em relação ao array `checkout.links` da sessão de checkout para obter
metadados adicionais.

### Referência da API de mensagem da janela

#### `ec.window.open_request`

Solicita ao anfitrião que administre um link ativado pelo comprador na finalização da compra.

- **Direção:** Check-out incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `url` (string, uri, **OBRIGATÓRIO**): A URL do recurso a ser apresentado.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "id": "window_1",
    "method": "ec.window.open_request",
    "params": {
        "url": "https://merchant.com/privacy-policy"
    }
}
```

- **Direção:** Host → Check-out incorporado
- **Tipo:** Resposta
- **Carga útil:**
    - `ucp`: metadados do protocolo BCP com `status: "success"`

**Exemplo de resposta de sucesso:**

<!-- ucp:example schema=transports/embedded_message def=response -->
```json
{
    "jsonrpc": "2.0",
    "id": "window_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" }
    }
}
```

**Exemplo de resposta de erro:**

<!-- ucp:example schema=shopping/types/error_response op=read direction=response extract=$.result -->
```json
{
    "jsonrpc": "2.0",
    "id": "window_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
        "messages": [
            {
                "type": "error",
                "code": "window_open_rejected_error",
                "content": "Window open rejected by host.",
                "severity": "unrecoverable"
            }
        ]
    }
}
```

## Segurança e tratamento de erros

### Códigos de erro

Consulte [Protocolo incorporado - códigos de erro](embedded-protocol.md#codigos-de-erro) para
os códigos de erro compartilhados. O Checkout Incorporado define os seguintes adicionais
códigos para cenários específicos de delegação:

| Código | Gravidade | Descrição |
| :--------------------------- | :-------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `not_allowed_error` | `recoverable` | A solicitação não tinha ativação de usuário válida (consulte [Prevenção de solicitações de pagamento não solicitadas](#prevencao-de-solicitacoes-de-pagamento-nao-solicitadas)). |
| `window_open_rejected_error` | `unrecoverable` | A política do host impediu a navegação. O anfitrião **PODE** notificar o comprador de que sua solicitação foi rejeitada.                                       |

Para `not_allowed_error`, a recuperação requer uma nova [ativação do usuário](https://html.spec.whatwg.org/multipage/interaction.html#activation)
gesto antes de tentar novamente a delegação.

### Segurança para hosts baseados na Web

O ECP herda os requisitos de segurança compartilhados do EP para CSP, sandbox de iframe,
iframes sem credenciais e validação estrita de origem. Veja
[Protocolo Incorporado - Segurança](embedded-protocol.md#seguranca) para o completo
especificação.

### Prevenção de solicitações de pagamento não solicitadas

**Vulnerabilidade:** uma empresa mal-intencionada ou comprometida pode
acionar `ec.payment.credential_request` sem interação do usuário.

**Mitigação (Execução Controlada pelo Host):** Para eliminar esse risco, o host é
designado como o único iniciador confiável da execução do pagamento. O anfitrião
**DEVE** exibir uma UI de confirmação do usuário antes de liberar o token. A
tokenização silenciosa é estritamente PROIBIDA quando o gatilho se originar do
Checkout Incorporado.

## Definições de esquema

Os esquemas a seguir definem as estruturas de dados usadas no Embedded
Protocolo de checkout e suas extensões.

### Finalização da compra

O objeto principal que representa o estado atual da transação, incluindo
itens de linha, totais e informações do comprador.

{{ schema_fields('checkout_resp', 'checkout') }}

### Pedido

O objeto retornado após a conclusão bem-sucedida de um checkout, contendo
detalhes de confirmação.

{{ schema_fields('order', 'order') }}

### Pagamento

{{ schema_fields('payment_resp', 'embedded-checkout')}}

### Instrumento de Pagamento

Representa um método específico de pagamento (por exemplo, um cartão de crédito específico, banco
conta ou credencial de carteira) disponível para o comprador.

{{ schema_fields('payment_instrument', 'embedded-checkout') }}

#### Instrumento de pagamento selecionado

{{ extension_schema_fields('types/payment_instrument.json#/$defs/selected_payment_instrument', 'embedded-checkout') }}

### Instrumento de pagamento com cartão

{{ schema_fields('types/card_payment_instrument', 'embedded-checkout') }}

### Credencial de pagamento

{{ schema_fields('types/payment_credential', 'embedded-checkout') }}

### Credencial de token

{{ schema_fields('types/token_credential_resp', 'embedded-checkout') }}

### Credencial do cartão

{{ schema_fields('types/card_credential', 'embedded-checkout') }}

### Gerenciador de pagamentos

Representa o processador ou provedor de carteira responsável pela autenticação
e pelo processamento de um instrumento de pagamento específico (por exemplo,
um PSP de Pix, Google Pay, Stripe ou um aplicativo bancário).

{{ extension_schema_fields('payment_handler.json#/$defs/response_schema', 'embedded-checkout') }}
