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

# Protocolo Incorporado (EP)

## Introdução

O Protocolo Incorporado (EP) é uma ligação de transporte BCP que permite que um
**host** incorpore uma interface de **empresa** em um iframe ou webview e troque
mensagens estruturadas por esse canal. O EP define **como** comunicar — formato
da mensagem, configuração de canal, autenticação, tratamento de erros e
restrições de segurança. Ele não define **quais** dados existem; isso é
responsabilidade de cada capacidade que se liga ao EP.

Cada capacidade implementa métodos EP sob seu próprio prefixo de método. Por
exemplo, checkout usa o prefixo `ec.*` e carrinho usa o prefixo `ep.cart.*`.
Os padrões compartilhados descritos neste documento aplicam-se uniformemente
a todas as capacidades do EP.

Detalhes específicos da capacidade — descoberta, parâmetros de URL, contratos
de delegação, cargas úteis de mensagens e definições de esquema — são
definidos na especificação de vinculação EP de cada capacidade:

- [Capacidade de checkout - Vinculação EP](embedded-checkout.md)
- [Capacidade do carrinho - Vinculação EP](embedded-cart.md)

## Terminologia e atores

### Funções comerciais

- **Negócios:** O vendedor que fornece bens ou serviços.
- **Comprador:** o usuário final que faz uma compra.

### Componentes Técnicos

- **Host:** O aplicativo que incorpora a interface da empresa (por exemplo, AI Agent
    aplicativo, Super App, Navegador). Responsável pela autenticação do usuário e, quando
    UI nativa delegada para ações como pagamento e seleção de endereço.
- **Contexto incorporado:** A interface do negócio renderizada em um iframe ou
    visualização da web. Responsável pelo fluxo específico da capacidade (por exemplo, checkout,
    construção de carrinho).

## Transporte e mensagens

### Formato da mensagem

Todas as mensagens EP **DEVEM** usar o formato JSON-RPC 2.0
([RFC 7159](https://datatracker.ietf.org/doc/html/rfc7159)). Cada mensagem
**DEVE** conter:

- `jsonrpc`: **DEVE** ser `"2.0"`
- `method`: O nome da mensagem (por exemplo, `"ec.start"`, `"ep.cart.start"`)
- `params`: carga útil específica da mensagem (pode ser um objeto vazio)
- `id`: (Opcional) Presente apenas para solicitações que esperam respostas

### Tipos de mensagens

**Solicitações** (com campo `id`):

- Exige uma resposta do receptor
- **DEVE** incluir um campo `id` exclusivo
- O receptor **DEVE** responder com `id` correspondente
- A resposta **DEVE** ser `result` ou `error_response`
- Usado para operações que requerem confirmação ou dados

**Notificações** (sem campo `id`):

- Apenas informativo, nenhuma resposta esperada
- **NÃO DEVE** incluir um campo `id`
- O destinatário **NÃO DEVE** enviar uma resposta
- Usado para atualizações de estado e eventos informativos

### Tratamento de respostas

Para solicitações (mensagens com `id`), os destinatários **DEVERÃO** responder com `result`.
Os resultados de sucesso e erro **DEVEM** ser retornados por meio do campo `result`,
consistente com o modelo de erro de duas camadas do BCP. O campo JSON-RPC `error` é
reservado para falhas no nível de transporte (erros de análise, método não encontrado,
parâmetros inválidos). Implementações **NÃO DEVEM** usar o campo JSON-RPC `error` para
códigos de erro no nível do aplicativo.

**Resposta de sucesso:**

<!-- ucp:example schema=transports/embedded_message def=response -->
```json
{
  "jsonrpc": "2.0",
  "id": "req_1",
  "result": {
    "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" }
    // ... result fields
  }
}
```

**Resposta de erro:**

<!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.result -->
```json
{
  "jsonrpc": "2.0",
  "id": "...",
  "result": {
    "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
    "messages": [...]
  }
}
```

Em ambos os casos, `result.ucp.status` serve como discriminador entre sucesso
e resultados de erro — o mesmo padrão usado em todos os transportes BCP.

### Erros de transporte

Erros de transporte são falhas em nível de protocolo que impedem o processamento de solicitações.
Eles são retornados como JSON-RPC `error` usando códigos de erro JSON-RPC padrão e
indicam que a mensagem em si é inválida ou não pôde ser processada — não que
a lógica de negócio executada produziu um resultado de erro. Veja a
[especificação principal](reference.md#error-code) para o registro completo
de códigos de erro.

Por exemplo, se uma solicitação não puder ser processada (método desconhecido,
parâmetros malformados), o host **DEVE** responder com um JSON-RPC `error`:

<!-- ucp:example schema=transports/embedded_message def=error_response -->
```json
{
    "jsonrpc": "2.0",
    "id": "req_1",
    "error": {
        "code": -32601,
        "message": "Method not found."
    }
}
```

## Canais de comunicação

### Hosts baseados na Web

Quando o host é uma aplicação web, a comunicação começa usando `postMessage`
entre o host e a janela do contexto incorporado. O anfitrião **DEVE** ouvir as
chamadas de `postMessage` vindas da janela incorporada e, quando uma mensagem
for recebida, **DEVE** validar se a origem corresponde ao `continue_url`
usado para iniciar a sessão.

Após a validação, o host **PODE** criar um `MessageChannel` e transferir uma
de suas portas na resposta `ready`. Quando um host responde com `MessagePort`,
todas as mensagens subsequentes **DEVEM** ser enviadas por esse canal. Caso
contrário, o anfitrião e as empresas **DEVEM** continuar usando `postMessage()`
entre seus objetos `window`, incluindo validação de origem.

### Hosts nativos

Quando o host é um aplicativo nativo, ele **DEVE** injetar globais no
contexto incorporado que permitam a comunicação `postMessage` entre a web e
ambientes nativos. Cada capacidade define os nomes de seus globais seguindo
o padrão:

- `window.Embedded{Capability}ProtocolConsumer` (preferencial)
- `window.webkit.messageHandlers.Embedded{Capability}ProtocolConsumer`

Este objeto **DEVE** implementar a seguinte interface:

```javascript
{
  postMessage(message: string): void
}
```

Onde `message` é uma mensagem JSON-RPC 2.0 com string JSON. O anfitrião **DEVE**
analisar a string JSON antes do processamento.

Para mensagens que viajam do host para o contexto incorporado, o host **DEVE**
injetar JavaScript no webview que chama
`window.Embedded{Capability}Protocol.postMessage()` com a mensagem JSON-RPC.
O contexto incorporado **DEVE** inicializar este objeto global — e começar a
ouvir chamadas de `postMessage()` — antes que a mensagem `ready` do recurso seja enviada.

Consulte a ligação EP de cada capacidade para obter os nomes globais específicos:

- **Check-out:** `EmbeddedCheckoutProtocolConsumer` / `EmbeddedCheckoutProtocol`
- **Carrinho:** `EmbeddedCartProtocolConsumer` / `EmbeddedCartProtocol`

## Padrões de mensagens

### Aperto de mão

Após a renderização, o contexto incorporado **DEVE** transmitir prontidão para
o host usando a mensagem `ready` do recurso. Esta mensagem inicializa um canal
de comunicação seguro entre o host e o contexto incorporado, comunica quais
delegações foram aceitas e sinaliza se é necessária uma troca de autorização
adicional.

**Fluxo geral:**

1. O contexto incorporado envia uma solicitação `ready` com uma lista
   `delegate` e uma solicitação `auth` opcional
2. O anfitrião responde com:
    - Envelope `ucp` confirmando a versão do protocolo negociado
    - `upgrade` opcional com `MessagePort` para atualização de canal
    - `credential` opcional com dados de autorização solicitados
    - Estado opcional específico da capacidade (por exemplo, estado de delegação de checkout)
3. Se o host incluir um `upgrade`, o contexto incorporado **DEVE** descartar
   todos os outros campos da resposta, mudar para o canal atualizado e enviar
   uma nova mensagem `ready` nesse canal
4. Se o host responder com um resultado `error_response`, a sessão não pode
   prosseguir — o host **DEVE** destruir o contexto incorporado e **PODE**
   redirecionar o comprador para `continue_url` se disponível. O contexto
   incorporado **NÃO DEVE** enviar mais mensagens após receber um erro de handshake.

Cada capacidade define a especificação completa do método `ready`, incluindo
parâmetros específicos da capacidade e campos de resultados.

### Autenticação

O contexto incorporado **PODE** solicitar autorização do host após o
handshake inicial — por exemplo, para atualizar um token OAuth expirado. Essa
troca usa o método de autenticação do recurso (por exemplo, `ec.auth` para checkout,
`ep.cart.auth` para carrinho).

**Solicitação:**

- **Direção:** Contexto incorporado → Host
- **Tipo:** Solicitação
- **Carga útil:**
    - `type` (string, **OBRIGATÓRIO**): O tipo de autorização solicitado (por exemplo,
        `"oauth"`, `"api_key"`, `"jwt"`).

**Resposta de sucesso:**

- **Direção:** Host → Contexto incorporado
- **Tipo:** Resposta
- **Carga útil do resultado:**
    - `ucp` (objeto, **OBRIGATÓRIO**): metadados do protocolo BCP com
        `status: "success"`.
    - `credential` (string, **OBRIGATÓRIO**): Os dados de autorização solicitados.

**Resposta de erro:**

O host **DEVE** responder com um `result` contendo os dados de autorização
ou um `error_response`.

**Exemplo de resposta de sucesso:**

<!-- ucp:example schema=transports/embedded_message def=response -->
```json
{
    "jsonrpc": "2.0",
    "id": "auth_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "success" },
        "credential": "eyJhbGciOiJSUzI1NiIs..."
    }
}
```

**Exemplo de resposta de erro:**

<!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.result -->
```json
{
    "jsonrpc": "2.0",
    "id": "auth_1",
    "result": {
        "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
        "messages": [
            {
                "type": "error",
                "code": "timeout_error",
                "content": "An internal service timed out when fetching the required authorization data.",
                "severity": "recoverable"
            }
        ]
    }
}
```

**Escalonamento de erros:**

Se o erro for transitório (indicado pela gravidade `recoverable`), o
contexto **PODE** reiniciar a solicitação de autenticação. Caso contrário, o contexto incorporado
**DEVE** emitir uma notificação de erro de sessão (consulte [Erro de sessão](#erro-de-sessao))
contendo uma resposta de erro `unrecoverable`. Esta escalada também se aplica quando
o contexto incorporado não é capaz de processar uma credencial fornecida pelo host (por exemplo,
a credencial está corrompida). O erro de sessão **DEVE** incluir um
`continue_url` para permitir a transferência do comprador.

**Exemplo — falha de autenticação escalonada para erro de sessão:**

<!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.params.error -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.error",
    "params": {
        "error": {
            "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
            "messages": [
                {
                    "type": "error",
                    "code": "not_supported_error",
                    "content": "Requested auth credential type is not supported",
                    "severity": "unrecoverable"
                }
            ],
            "continue_url": "https://merchant.example.com"
        }
    }
}
```

Quando o host recebe esta notificação, ele **DEVE** desmontar o contexto
incorporado e **DEVE** exibir um estado de erro apropriado. Se `continue_url`
estiver presente, o host **DEVE** usá-lo para entregar o comprador para
recuperação da sessão.

### Erro de sessão

Um erro de sessão sinaliza uma condição fatal que não está relacionada a um
recurso específico — por exemplo, uma falha de autenticação terminal que
impede a sessão de continuar. Cada recurso define seu próprio método de notificação de erros de sessão
(por exemplo, `ec.error` para finalização da compra, `ep.cart.error` para carrinho).

**Carga útil de notificação:**

- `error` (objeto, **OBRIGATÓRIO**): Resposta de erro em nível de sessão.
    - `ucp` (objeto, **OBRIGATÓRIO**): metadados do protocolo BCP. `status`
        **DEVE** ser `"error"`.
    - `messages` (array, **OBRIGATÓRIO**): Uma ou mais mensagens descrevendo o
        fracasso.
    - `continue_url` (string, **OPCIONAL**): URL para transferência ou sessão do comprador
        recuperação.

**Exemplo:**

<!-- ucp:example schema=common/types/error_response op=read direction=response extract=$.params.error -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.error",
    "params": {
        "error": {
            "ucp": { "version": "{{ bcp_schema_version }}", "status": "error" },
            "messages": [
                {
                    "type": "error",
                    "code": "not_supported_error",
                    "content": "Requested auth credential type is not supported.",
                    "severity": "unrecoverable"
                }
            ],
            "continue_url": "https://merchant.example.com/checkout/abc123"
        }
    }
}
```

**Manuseio do host:**

Quando o host recebe uma notificação de erro de sessão, ele **DEVE** desmontar o
contexto incorporado e **DEVE** exibir um estado de erro apropriado para o comprador.
Se `continue_url` estiver presente, o anfitrião **DEVE** usá-lo para entregar o comprador para
recuperação da sessão.

### Ciclo de vida

Cada capacidade define os métodos de notificação `start` e `complete` que seguem
um contrato compartilhado:

- **`start`**: O contexto incorporado notifica o host de que a UI está visível
    e pronta para interação. A notificação **DEVE** incluir o estado atual
    completo do recurso (por exemplo, o objeto checkout ou carrinho).
- **`complete`**: O contexto incorporado notifica o host de que o fluxo do
    recurso foi concluído com sucesso. A notificação **DEVE** incluir o
    estado final do recurso.

Ambas são notificações – o host **NÃO DEVE** responder.

**Exemplo – iniciar notificação (carrinho):**

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
        }
    }
}
```

**Exemplo – notificação completa (checkout):**

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

### Mudança de Estado

Notificações de mudança de estado informam o host sobre mudanças que já ocorreram
no contexto incorporado. Estas são apenas informativas — o contexto incorporado
já aplicou as alterações e renderizou a UI atualizada. O anfitrião **NÃO DEVE**
responder às notificações de mudança de estado.

Cada capacidade define seu próprio conjunto de métodos de mudança de estado,
cobrindo os campos de recurso relevantes (por exemplo, itens de linha,
informações do comprador, totais). As notificações de alteração de estado
**DEVEM** incluir o estado atual completo do recurso, não apenas os campos
alterados.

**Exemplo — itens de linha alterados (checkout):**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ec.line_items.change",
    "params": {
        "checkout": {
            "id": "checkout_123",
            "totals": [ ... ],
            "line_items": [ ... ]
            // ... other checkout fields
        }
    }
}
```

**Exemplo — mensagens alteradas (carrinho):**

<!-- ucp:example schema=transports/embedded_message def=request direction=request -->
```json
{
    "jsonrpc": "2.0",
    "method": "ep.cart.messages.change",
    "params": {
        "cart": {
            "id": "cart_123",
            "line_items": [ ... ],
            "messages": [
                {
                    "type": "error",
                    "code": "invalid_quantity",
                    "path": "$.line_items[0].quantity",
                    "content": "Quantity must be at least 1",
                    "severity": "recoverable"
                }
            ]
            // ... other cart fields
        }
    }
}
```

## Códigos de erro

O Protocolo Incorporado define um conjunto compartilhado de códigos de erro. As capacidades
**PODEM** definir códigos de erro adicionais para cenários específicos de capacidade.

| Código | Gravidade | Descrição |
| :-------------------- | :-------------- | :--------------------------------------------------------------------------------- |
| `abort_error` | `recoverable` | O usuário cancelou a interação (por exemplo, fechou a planilha).         |
| `security_error` | `unrecoverable` | A validação da origem do host falhou.                                   |
| `invalid_state_error` | `unrecoverable` | O aperto de mão foi tentado fora de ordem.                                |
| `not_supported_error` | `unrecoverable` | A operação solicitada ou o tipo de autorização não são suportados.      |
| `timeout_error` | `recoverable` | Um serviço interno expirou. A operação pode ser repetida.         |

Erros **DEVERÃO** usar apenas as gravidades `recoverable` e `unrecoverable`.
`recoverable` significa que a operação pode ser tentada novamente. `unrecoverable`
significa que a operação não pode ser bem-sucedida na sessão atual.

## Segurança

### Política de Segurança de Conteúdo (CSP)

Para garantir a segurança, ambas as partes **DEVEM** implementar diretivas de
**[Política de Segurança de Conteúdo (CSP)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)**:

- **Negócios:** **DEVE** definir `frame-ancestors <host_origin>;` para garantir
    que só seja incorporada por hosts confiáveis.

- **Anfitrião:**
    - **Incorporação direta:** se o host incorporar diretamente a página da empresa,
        especificar uma diretiva `frame-src` listando a origem de todos os
        negócios em potencial pode ser impraticável, especialmente se houver
        muitas empresas. Nesse cenário, embora um `frame-src` rigoroso seja
        ideal, outras medidas como as descritas em
        [Iframe Sandbox Attributes](#atributos-da-sandbox-do-iframe) e
        [Iframes sem credenciais](#iframes-sem-credenciais) são críticas.
    - **Iframe intermediário:** O host **PODE** usar um iframe intermediário
        (por exemplo, em um subdomínio controlado por host) para incorporar a página da empresa.
        Isso oferece melhor controle:
        - A página principal do host só precisa permitir a origem do
            iframe intermediário em seu `frame-src` (por exemplo,
            `frame-src <intermediate_iframe_origin>;`).
        - O iframe intermediário **DEVE** implementar uma política de
            `frame-src` estrita, definida dinamicamente para permitir
            _apenas_ o `<merchant_origin>` específico da sessão incorporada
            atual (por exemplo, `frame-src <merchant_origin>;`). Isso pode
            ser definido por meio de cabeçalhos HTTP ao servir o conteúdo do
            iframe intermediário.

### Atributos da sandbox do iframe

Todos os iframes de negócios **DEVEM** ser colocados em sandbox para restringir seus recursos. Os
seguintes atributos de sandbox **DEVERÃO** ser aplicados, mas um host e uma empresa
**PODEM** negociar recursos adicionais:

```html
<iframe sandbox="allow-scripts allow-forms allow-same-origin"></iframe>
```

### Iframes sem credenciais

Os hosts **DEVERÃO** usar o atributo `credentialless` no iframe para carregá-lo
em um contexto novo e efêmero. Isso evita que a empresa correlacione a
atividade do usuário entre contextos ou acesse sessões existentes, protegendo
a privacidade do usuário.

```html
<iframe credentialless src="https://business.example.com/..."></iframe>
```

### Validação estrita de origem

Aplicar validação rigorosa de `origin` para todas as comunicações `postMessage`
entre quadros.
