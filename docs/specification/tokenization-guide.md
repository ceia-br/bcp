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

# Guia de tokenização

**OpenAPI:** não publicado nesta versão do BCP.

## Visão geral

Este guia é para **implementadores que criam gerenciadores de pagamentos de tokenização**. Ele
define a API compartilhada, os requisitos de segurança e os critérios de conformidade que todos
os manipuladores de tokenização seguem.

**Observação:** Embora os exemplos neste guia usem credenciais de cartão, os padrões de
tokenização se aplicam a **qualquer tipo de credencial sensível** — contas bancárias, carteiras
digitais, contas de fidelidade, etc. Requisitos de conformidade (por exemplo, PCI DSS para
cartões) variam de acordo com o tipo de credencial.

**Pix não segue este padrão.** O manipulador padrão do BCP,
[`br.dev.bcp.pix`](pix-payment-handler.md), não envolve tokenização do lado
da plataforma — a empresa gera a cobrança diretamente com seu PSP e a
devolve para exibição. Este guia é relevante para manipuladores baseados em
cartão ou outras credenciais tokenizáveis, não para Pix.

Oferecemos uma série de exemplos para utilizar formas de tokenização no BCP:

| Exemplo | Caso de uso |
| :------ | :------- |
| Tokenizer de processador (não incluído nesta versão BCP) | Business ou PSP executa tokenização e processamento |
| Platform Tokenizer (não incluído nesta versão BCP) | Plataforma tokeniza credenciais para empresas/PSPs |
| Manipulador de credenciais criptografadas (não incluído nesta versão do BCP) | Plataforma criptografa credenciais em vez de tokenizar |

---

## Conceitos Básicos

### Fluxo de credenciais

Os manipuladores de tokenização transformam credenciais entre os formulários de origem e de checkout:

```text
+-------------------------------------------------------------------------+
|                     Tokenization Payment Flow                           |
+-------------------------------------------------------------------------+
|                                                                         |
|   Platform has:            Tokenizer            Business receives:      |
|   Source Credential    -->  /tokenize  -->         TokenCredential      |
|                                                                         |
|   +-----------------+                      +-------------------------+  |
|   | source_         |                      | checkout_               |  |
|   | credentials     |    What goes IN      | credentials             |  |
|   |                 |<---------------      |                         |  |
|   | * card/fpan     |                      | What comes OUT          |  |
|   | * card/dpan     |                ----->| * token                 |  |
|   |                 |                      |                         |  |
|   +-----------------+                      +-------------------------+  |
|                                                                         |
+-------------------------------------------------------------------------+
```

Os manipuladores de tokenização aceitam credenciais de origem (por exemplo, cartão com FPAN) e
produzir credenciais de checkout (por exemplo, tokens).

### Ciclo de vida do token

Os tokens passam por fases distintas. A especificação do seu manipulador deve documentar
qual política de ciclo de vida você usa:

```text
+--------------+    +--------------+    +--------------+    +--------------+
|  Generation  |--->|   Storage    |--->| Detokenize   |--->| Invalidation |
|              |    |              |    |              |    |              |
|Platform calls|    | Tokenizer    |    | Business/PSP |    | Token expires|
| /tokenize    |    | holds token  |    | calls        |    | or is used   |
|              |    | -> credential|    | /detokenize  |    |              |
+--------------+    +--------------+    +--------------+    +--------------+
```

| Política | Descrição | Caso de uso |
| :----------------- | :------------------------------------------ | :-------------------------------------------------------- |
| **Utilização única** | Invalidado após a primeira destokenização | Mais seguro; padrão recomendado |
| **Baseado em TTL** | Expira após duração fixa (por exemplo, 15 min) | Permite novas tentativas em falhas transitórias |
| **Escopo da sessão** | Válido para duração da sessão de checkout | Fluxos complexos com múltiplas tentativas de processamento |

### Vinculação

Todas as solicitações de tokenização requerem um objeto `binding` que vincula o token a um
contexto específico:

| Campo | Obrigatório | Descrição |
| :----------- | :---------- | :------------------------------------------------------------------------------------------------------------ |
| `checkout_id` | Sim | A sessão de checkout para a qual este token é válido |
| `identity` | Condicional | A identidade do participante à qual se vincular; obrigatório quando o chamador age em nome de outro participante |

O tokenizer **DEVE** verificar as correspondências de ligação em `/detokenize`. Consulte [Esquema de ligação](site:schemas/shopping/types/binding.json).

---

## OpenAPI

Os manipuladores de tokenização implementam dois pontos de extremidade. Seu gerenciador **PODE** implementar
um ou ambos, dependendo da sua arquitetura. Ou nenhum, como no nosso exemplo de carga
útil criptografada, que define seu próprio mecanismo de criptografia.

### POST /tokenizar

Converte uma credencial bruta em um token vinculado a um checkout e uma identidade.

**Quando implementar:** Sempre, a menos que você seja um manipulador gerando tokens
internamente.

<!-- ucp:example skip reason="tokenization API, not BCP payload" -->
```json
POST /tokenize
Content-Type: application/json

{
  "credential": {
    "type": "card",
    "card_number_type": "fpan",
    "number": "4111111111111111",
    "expiry_month": 12,
    "expiry_year": 2026,
    "cvc": "123"
  },
  "binding": {
    "checkout_id": "abc123",
    "identity": {
      "access_token": "merchant_001"
    }
  }
}
```

**Resposta:**

<!-- ucp:example skip reason="tokenization API, not BCP payload" -->
```json
{
  "token": "tok_abc123xyz789"
}
```

### POST /destokenizar

Retorna a credencial original de um token válido. A vinculação deve corresponder.

**Quando implementar:** Sempre, a menos que você combine a destokenização com
processamento (ver exemplo PSP).

<!-- ucp:example skip reason="tokenization API, not BCP payload" -->
```json
POST /detokenize
Content-Type: application/json
Authorization: Bearer {caller_access_token}

{
  "token": "tok_abc123xyz789",
  "binding": {
    "checkout_id": "abc123"
  }
}
```

**Resposta:**

<!-- ucp:example skip reason="tokenization API, not BCP payload" -->
```json
{
  "type": "card",
  "card_number_type": "fpan",
  "number": "4111111111111111",
  "expiry_month": 12,
  "expiry_year": 2026,
  "cvc": "123"
}
```

**Observação:** `binding.identity` é omitido quando o chamador autenticado é o
alvo vinculativo. Inclua-o ao agir em nome de outro participante (por exemplo,
Destokenização de PSP para empresas).

A especificação OpenAPI para manipuladores de tokenização não está publicada nesta
versão do BCP.

---

## Requisitos de segurança

| Requisito | Descrição |
| :--------------------------- | :--------------------------------------------------------------------------------------------------- |
| **Vinculação necessária** | As credenciais **DEVEM** ser vinculadas a `checkout_id` e ao participante `identity` para evitar reutilização |
| **Vinculação verificada** | O tokenizer **DEVE** verificar as correspondências de ligação antes de retornar as credenciais |
| **Criptograficamente aleatório** | Use geradores aleatórios seguros; os tokens devem ser indecifráveis |
| **Comprimento suficiente** | Mínimo de 128 bits de entropia |
| **Não reversível** | Não é possível derivar a credencial do token |
| **Escopo** | O token só deve funcionar com o seu tokenizer |
| **Tempo limitado** | Aplicar TTL apropriado ao caso de uso (normalmente de 5 a 30 minutos) |
| **Preferencialmente de uso único** | Invalidar após a primeira destokenização quando possível |

---

## Requisitos de especificação do manipulador

Ao publicar seu manipulador, seu documento de especificação **DEVE** incluir:

| Requisito | Exemplo |
| :------------------------------ | :---------------------------------------------------------------- |
| **Nome exclusivo do manipulador** | `com.example.tokenization_payment` (formato DNS reverso) |
| **URLs de endpoint** | URLs base de produção e sandbox |
| **Requisitos de autenticação** | OAuth 2.0, chaves de API, etc. |
| **Processo de integração** | Como os participantes se cadastram e recebem identidades |
| **Credenciais aceitas** | Quais tipos de credenciais são aceitos para tokenização |
| **Política de ciclo de vida de token** | Uso único, TTL ou escopo de sessão |
| **Reconhecimentos de segurança** | Os participantes que recebem credenciais brutas devem aceitar a responsabilidade |

### Exemplo de esboço de especificação

```markdown
**Handler Name:** `com.acme.tokenization_payment`
**OpenAPI:** not published in this BCP release.

| Environment | Base URL                           |
| :---------- | :--------------------------------- |
| Production  | `https://api.acme.com/ucp`         |
| Sandbox     | `https://sandbox.api.acme.com/ucp` |

**Supported Instruments:**

| Instrument | Source Credentials           | Checkout Credentials |
| :--------- | :--------------------------- | :------------------- |
| `card`     | `card` (fpan, network_token) | `token`              |

**Token Lifecycle:** Single-use (invalidated after detokenization)

**Authentication:** OAuth 2.0 client credentials

**Onboarding:** Register at portal.acme.com. Businesses receive `access_token` for handler identity.
```

---

## Lista de verificação de conformidade

Um manipulador de tokenizador estará em conformidade com esse padrão se:

- [ ] Publica uma especificação de manipulador em uma URL estável com um DNS reverso exclusivo `handler_name`
- [ ] Implementa `/tokenize` e/ou `/detokenize` pela OpenAPI
- [ ] Define requisitos de autenticação e integração
- [ ] Documenta a transformação de credenciais entre os formulários de origem e de checkout
- [ ] Produz tokens compatíveis com o esquema `TokenCredential`
- [ ] Especifica a política de ciclo de vida do token (TTL, uso único, etc.)
- [ ] Requer `binding` com `checkout_id` em solicitações de tokenização
- [ ] Utiliza `PaymentIdentity` para identificação do participante
- [ ] Verifica correspondências de `binding` em solicitações de destokenização
- [ ] Requer confirmações de segurança dos participantes que recebem credenciais brutas

---

## Referências

| Recurso | URL |
| :---------------------- | :---------------------------------------------------------------------------------------------------------------------------- |
| OpenAPI de tokenização | Não publicado nesta versão do BCP.                                                                             |
| Esquema de Identidade | [schemas/shopping/types/payment_identity.json](site:schemas/shopping/types/payment_identity.json) |
| Esquema de ligação | [schemas/shopping/types/binding.json](site:schemas/shopping/types/binding.json) |
| Esquema de credenciais de token | [schemas/shopping/types/token_credential.json](site:schemas/shopping/types/token_credential.json) |
| Esquema de instrumento de cartão | [schemas/shopping/types/card_payment_instrument.json](site:schemas/shopping/types/card_payment_instrument.json) |

---

## Veja também

- **Manipulador de credenciais criptografadas (não incluído nesta versão do BCP)** — Padrão alternativo usando criptografia em vez de tokenizar/destokenizar viagens de ida e volta
- **[AP2 Mandates Extension](ap2-mandates.md)** — Adicionar prova criptográfica do contrato de checkout para verificação PSP
