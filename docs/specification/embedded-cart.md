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

# Capacidade do carrinho - Vinculação EP

## Introdução

O Embedded Cart Protocol (ECaP) é uma implementação específica de carrinho da
Ligação de transporte do Protocolo Incorporado (EP) do BCP que permite que um
**host** incorpore uma interface de carrinho de **empresa** e receba eventos
conforme o comprador interage com o carrinho.
O ECaP é uma ligação de transporte (como REST) — ela define **como** se
comunicar, não **quais** dados existem.

## Terminologia e atores

### Funções comerciais

- **Negócios:** O vendedor que fornece bens/serviços e a experiência de
    construção do carrinho.
- **Comprador:** o usuário final que deseja fazer uma compra por meio do fluxo de construção de carrinho.

### Componentes Técnicos

- **Host:** O aplicativo que incorpora o carrinho (por exemplo, aplicativo AI Agent,
    Super App, navegador). Responsável pela autenticação do usuário
    (incluindo quaisquer pré-requisitos, como vinculação de identidade).
- **Carrinho incorporado:** a interface do carrinho da empresa renderizada em um
    iframe ou webview. Responsável pelo fluxo de construção do carrinho e pela
    eventual transição para etapas mais avançadas do funil, como a criação do checkout.

### Descoberta

A disponibilidade do ECaP é sinalizada através da descoberta de serviços. Quando uma empresa anuncia
o transporte `embedded` em seu perfil `/.well-known/bcp`, todos os valores
`continue_url` de carrinho suportam o protocolo de carrinho incorporado.

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
suporta continuação de carrinho baseada em redirecionamento via `continue_url`.

#### Configuração por carrinho

A descoberta em nível de serviço declara que uma empresa oferece suporte ao ECaP, mas não
garante que as empresas o habilitarão para todas as sessões do carrinho. As empresas **DEVEM** incluir
uma ligação de serviço incorporada com `config.delegate` nas respostas do carrinho para
indicar a disponibilidade do ECaP e permitir delegações para uma sessão específica.

**Exemplo de resposta do carrinho:**

<!-- ucp:example schema=shopping/cart op=read direction=response extract=$.ucp.services target=$.ucp.services -->
```json
{
    "id": "cart_123",
    "continue_url": "https://merchant.example.com/cart/cart123",
    "ucp": {
        "version": "{{ bcp_schema_version }}",
        "services": {
            "br.dev.bcp.shopping": [
                {
                    "version": "{{ bcp_schema_version }}",
                    "transport": "embedded",
                    "config": {
                        "delegate": []
                    }
                }
            ]
        },
        "capabilities": {...},
        "payment_handlers": {...}
    }
    // ...other cart fields...
}
```

### Carregando um URL de carrinho incorporado

Quando um host recebe uma resposta de carrinho com `continue_url` de uma empresa
que anuncia suporte ao ECaP, ele **PODE** iniciar uma sessão do ECaP carregando o
URL em um contexto incorporado.

**Exemplo:**

```text
https://example.com/cart/cart123?ep_version=2026-01-23...
```

Observação: todos os valores dos parâmetros de consulta devem ser codificados em URL corretamente de acordo com RFC 3986.

Antes de carregar o contexto incorporado, o host **DEVE**:

1. Verificar `config.delegate` na resposta para saber quais delegações estão disponíveis
2. Completar, opcionalmente, os mecanismos de autenticação (ou seja, vinculação
   de identidade), se exigidos pela empresa

Para iniciar a sessão, o host **DEVE** aumentar o `continue_url` com os
parâmetros de consulta do ECaP.

Todos os parâmetros ECaP são passados por meio de string de consulta de URL, e não por cabeçalhos HTTP, para garantir
compatibilidade máxima em diferentes ambientes de incorporação. Os parâmetros
**DEVERIAM** usar os prefixos `ep` ou `ep_cart` para evitar a poluição do
namespace e distinguir claramente os parâmetros do ECaP dos parâmetros de
consulta específicos do negócio:

- `ep_version` (string, **OBRIGATÓRIO**): A versão BCP para esta sessão
    (formato: `YYYY-MM-DD`). Deve corresponder à versão da descoberta de serviço.
- `ep_auth` (string, **OPCIONAL**): Token de autenticação em ambiente definido pelo negócio
    formato.
- `ep_color_scheme` (string, **OPCIONAL**): A preferência do esquema de cores para
    a interface do carrinho. Valores válidos: `light`, `dark`. Quando não fornecido, o
    O carrinho incorporado segue a preferência do sistema.
- `ep_cart_delegate` (string, **OPCIONAL**): lista de delegações delimitada por vírgulas
    o host deseja lidar. **PODE** estar vazio se nenhuma delegação for necessária.
    **DEVE** ser um subconjunto de `config.delegate` da ligação de serviço incorporada.

## Transporte e mensagens

ECaP usa a camada de transporte EP compartilhada. Veja
[Protocolo incorporado – Transporte e mensagens](embedded-protocol.md#transporte-e-mensagens)
para formato de mensagem, tipos de mensagem e convenções de tratamento de resposta.

O `ucp.version` em todas as respostas **DEVE** ecoar o `ep_version` negociado
durante a inicialização da sessão e confirmado pelo host na resposta
`ep.cart.ready`. A versão está vinculada à sessão — **NÃO DEVE** ser alterada
durante a sessão do ECaP.

### Canais de Comunicação

O ECaP segue o modelo de canal de comunicação EP partilhado. Veja
[Protocolo Incorporado – Canais de Comunicação](embedded-protocol.md#canais-de-comunicacao)
para o padrão geral.

Para hosts nativos, os globais específicos do carrinho são:

- `window.EmbeddedCartProtocolConsumer` (preferencial)
- `window.webkit.messageHandlers.EmbeddedCartProtocolConsumer`
- `window.EmbeddedCartProtocol` (Host → Carrinho Incorporado)

## Referência da API de mensagens

### Categorias de mensagens

#### Mensagens principais

As mensagens principais são definidas pela especificação ECaP e **DEVEM** ser suportadas por
todas as implementações.

| Categoria | Finalidade | Padrão | Mensagens principais |
| :---------------- | :----------------------------------------------------------------------------------- | :--------------------- | :-------------------------------------------------------------------------------------------------- |
| **Aperto de mão** | Estabeleça conexão entre o host e o carrinho incorporado.                      | Solicitação | `ep.cart.ready` |
| **Autenticação**| Comunique trocas de dados de autenticação entre o carrinho incorporado e o host.           | Solicitação | `ep.cart.auth` |
| **Ciclo de vida** | Informar o estado do carrinho no carrinho incorporado.                                    | Notificação | `ep.cart.start`, `ep.cart.complete` |
| **Mudança de estado** | Informar sobre alterações nos campos do carrinho.                                             | Notificação | `ep.cart.line_items.change`, `ep.cart.buyer.change`, `ep.cart.messages.change` |
| **Erro de sessão** | Sinaliza um erro no nível da sessão não relacionado ao recurso do carrinho.              | Notificação | `ep.cart.error` |

### Mensagens de aperto de mão

#### `ep.cart.ready`

Após a renderização, o carrinho incorporado **DEVE** transmitir a prontidão
para o contexto pai usando a mensagem `ep.cart.ready`. Esta mensagem
inicializa um canal de comunicação seguro entre o host e o carrinho
incorporado, comunica se é necessária ou não uma troca de autenticação
adicional, e permite que o host forneça quaisquer dados de autorização
solicitados de volta ao carrinho incorporado.

- **Direção:** Carrinho Incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `delegate` (array de strings, **OBRIGATÓRIO**): Lista de identificadores
        de delegação aceitos pelo carrinho incorporado. **DEVE** ser um subconjunto de
        ambos `ep_cart_delegate` (o que o host solicitou) e `config.delegate`
        da resposta do carrinho (o que o negócio permite). Uma matriz vazia
        significa que nenhuma delegação foi aceita.
    - `auth` (objeto, **OPCIONAL**): Quando o parâmetro URL `ep_auth` não é suficiente
        nem aplicável devido a considerações adicionais, a empresa pode solicitar
        autorização durante o handshake inicial especificando a string `type`
        dentro deste objeto. Este valor de string `type` é um espelho do conteúdo da carga útil
        incluído em [`ep.cart.auth`](#epcartauth).

**Exemplo de mensagem (nenhuma delegação aceita):**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "id": "ready_1",
    "method": "ep.cart.ready",
    "params": {
        "delegate": [],
        "auth": {
            "type": "oauth"
        }
    }
}
```

A mensagem `ep.cart.ready` é uma solicitação, o que significa que o host **DEVE** responder
para completar o aperto de mão.

- **Direção:** Host → Carrinho Incorporado
- **Tipo:** Resposta
- **Carga útil do resultado:**
    - `ucp` (objeto, **OBRIGATÓRIO**): metadados do protocolo BCP. O `version`
        confirma que os `ep_version` e `status` negociados **DEVERÃO** ser
        `"success"`.
    - `upgrade` (objeto, **OPCIONAL**): Um objeto que descreve como o carrinho
        incorporado deve atualizar o canal de comunicação que usa para se
        comunicar com o anfitrião. Quando presente, o host **NÃO DEVE** incluir
        `credential` — o canal será restabelecido e qualquer credencial
        enviada aqui será descartada.
    - `credential` (string, **OPCIONAL**): Os dados de autorização solicitados,
        pode estar na forma de um token OAuth, JWT, chaves de API, etc. **DEVE** ser
        definido se `auth` estiver presente na solicitação. **NÃO DEVE** ser definido se
        `upgrade` está presente.

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
canal entre o host e o carrinho incorporado. Atualmente, este objeto suporta apenas
um campo `port`, que **DEVE** ser um objeto `MessagePort` e **DEVE** ser
transferido para o contexto do carrinho incorporado (por exemplo, com `{transfer: [port2]}`
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

Quando o host responde com um objeto `upgrade`, o carrinho incorporado **DEVE**
descartar qualquer outra informação da mensagem, enviar uma nova mensagem `ep.cart.ready`
através do canal de comunicação atualizado e aguarde uma nova resposta. Todos
mensagens subsequentes **DEVEM** ser enviadas somente pela comunicação atualizada
canal.

Se o host não puder completar o handshake (por exemplo, falha na validação de origem ou
violação do estado do protocolo), ele **DEVE** responder com um resultado `error_response`.
Quando o host responde com um erro, a sessão não pode prosseguir. O anfitrião
**DEVE** eliminar o contexto incorporado e **PODE** redirecionar o comprador para
`continue_url` se presente. O carrinho incorporado **NÃO DEVE** ser enviado posteriormente
mensagens após receber um erro de handshake.

### Autenticação

#### `ep.cart.auth`

`ep.cart.auth` implementa o padrão de autenticação EP compartilhado — veja
[Protocolo Incorporado - Autenticação](embedded-protocol.md#autenticacao) para
o contrato de solicitação/resposta, exemplos e fluxo de escalonamento de erros.

- **Método:** `ep.cart.auth`
- **Direção:** Carrinho Embutido → Host (solicitação); Host → Carrinho Incorporado (resposta)

Quando o escalonamento de erros é necessário, o carrinho incorporado **DEVE** emitir um
Notificação `ep.cart.error` de acordo com o
[padrão de erro de sessão](embedded-protocol.md#erro-de-sessao).

### Mensagens do ciclo de vida

As notificações do ciclo de vida seguem o padrão EP compartilhado — consulte
[Protocolo incorporado - Ciclo de vida](embedded-protocol.md#ciclo-de-vida). Todo o ciclo de vida
notificações carregam o objeto `cart` completo como carga útil.

#### `ep.cart.start`

Sinaliza que o carrinho está visível e pronto para interação. Enviado após um sucesso
Aperto de mão `ep.cart.ready`.

- **Direção:** Carrinho Incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `cart` (objeto, **OBRIGATÓRIO**): O estado atual completo do carrinho.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ep.cart.start",
    "params": {
        "cart": {
            "id": "cart_123",
            "currency": "BRL",
            "totals": [ ... ],
            "line_items": [ ... ],
            "buyer": { ... }
            // ...other cart fields...
        }
    }
}
```

#### `ep.cart.complete`

Indica a conclusão do processo de construção do carrinho, e o comprador está
pronto para avançar para a próxima etapa de sua jornada de compra.

Isso marca a conclusão do carrinho incorporado. Se `br.dev.bcp.shopping.checkout`
fizer parte dos recursos negociados durante a descoberta de serviço, o host
**PODE** prosseguir para iniciar uma sessão de checkout com base no carrinho
concluído, emitindo uma operação de [Criar Checkout](checkout.md#criar-check-out).

- **Direção:** Carrinho Incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `cart` (objeto, **OBRIGATÓRIO**): Estado final do carrinho.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ep.cart.complete",
    "params": {
        "cart": {
            "id": "cart_123",
            "currency": "BRL",
            "totals": [ ... ],
            "line_items": [ ... ],
            "buyer": { ... }
            // ...other cart fields...
        }
    }
}
```

### Mensagens de mudança de estado

As notificações de mudança de estado seguem o padrão EP compartilhado – consulte
[Protocolo Incorporado - Mudança de Estado](embedded-protocol.md#mudanca-de-estado). Todos os estados
notificações de alteração são enviadas do carrinho incorporado para o host e carregam o
objeto `cart` completo como sua carga útil.

#### `ep.cart.line_items.change`

Os itens de linha foram modificados (quantidade alterada, itens adicionados/removidos).

- **Direção:** Carrinho Incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `cart` (objeto, **OBRIGATÓRIO**): O estado atual completo do carrinho.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ep.cart.line_items.change",
    "params": {
        "cart": {
            "id": "cart_123",
            // The entire cart object is provided, including the updated line items and estimated totals
            "totals": [ ... ],
            "line_items": [ ... ]
            // ...
        }
    }
}
```

#### `ep.cart.buyer.change`

As informações do comprador foram atualizadas (e-mail, telefone, nome).

- **Direção:** Carrinho Incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `cart` (objeto, **OBRIGATÓRIO**): O estado atual completo do carrinho.

**Exemplo de mensagem:**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ep.cart.buyer.change",
    "params": {
        "cart": {
            "id": "cart_123",
            // The entire cart object is provided, including the updated buyer information
            "buyer": { ... }
            // ...
        }
    }
}
```

#### `ep.cart.messages.change`

As mensagens do carrinho foram atualizadas. As mensagens incluem erros, avisos e
avisos informativos sobre o estado do carrinho.

- **Direção:** Carrinho Incorporado → Host
- **Tipo:** Notificação
- **Carga útil:**
    - `cart` (objeto, **OBRIGATÓRIO**): O estado atual completo do carrinho.

**Exemplo de mensagem:**

<!-- ucp:example schema=shopping/cart op=read direction=response extract=$.params.cart.messages target=$.messages -->
```json
{
    "jsonrpc": "2.0",
    "method": "ep.cart.messages.change",
    "params": {
        "cart": {
            "id": "cart_123",
            // The entire cart object is provided, including any updated messages
            "messages": [
                {
                    "type": "error",
                    "code": "invalid_quantity",
                    "path": "$.line_items[0].quantity",
                    "content": "Quantity must be at least 1",
                    "severity": "recoverable"
                }
            ]
            // ...
        }
    }
}
```

### Mensagens de erro de sessão

#### `ep.cart.error`

`ep.cart.error` implementa o padrão de erro de sessão EP compartilhada — veja
[Protocolo incorporado - erro de sessão](embedded-protocol.md#erro-de-sessao) para o
especificação de carga útil e requisitos de manipulação de host.

## Segurança e tratamento de erros

### Códigos de erro

ECaP usa o conjunto de códigos de erro EP compartilhado - consulte
[Protocolo incorporado - códigos de erro](embedded-protocol.md#codigos-de-erro).

### Segurança para hosts baseados na Web

O ECaP herda os requisitos de segurança compartilhados do EP para CSP, sandbox
de iframe, iframes sem credenciais e validação estrita de origem. Veja
[Protocolo Incorporado - Segurança](embedded-protocol.md#seguranca) para o completo
especificação.

## Definições de esquema

Os esquemas a seguir definem as estruturas de dados usadas no Embedded
Protocolo do carrinho.

### Carrinho

O objeto principal que representa o estado atual do carrinho, incluindo
itens de linha, totais e informações do comprador.

{{ schema_fields('cart_resp', 'cart') }}
