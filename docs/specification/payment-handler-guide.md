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

# Guia de especificação do manipulador de pagamento

## Introdução

Este guia define a estrutura padrão e o vocabulário para especificar os manipuladores
de pagamento do BCP. Todas as especificações de manipulador de pagamento **DEVEM** seguir esta
estrutura para garantir consistência, integridade e clareza para os implementadores.

### Objetivo

Os manipuladores de pagamento permitem a interoperabilidade "N-to-N" entre plataformas, empresas,
e provedores de pagamento. Um manipulador bem especificado deve responder a essas perguntas para
cada participante:

- **Quem participa?** Quais participantes estão envolvidos e quais são suas funções?
- **Quais são os pré-requisitos?** Qual integração ou configuração é necessária?
- **Como é configurado?** Qual configuração é anunciada ou consumida?
- **Como é executado?** Qual protocolo é seguido para adquirir ou processar instrumentos?

Este guia fornece uma estrutura que garante que cada especificação do manipulador responda
essas questões sistematicamente.

!!! note "Exemplo de referência"
    Os exemplos abaixo usam um tokenizador de cartão genérico
    (`com.example.tokenizer`) apenas para ilustrar a mecânica de autoria de
    esquemas — cardinalidade de campos, resolução de `available_instruments`,
    tratamento de erros. Para o manipulador de referência real e padrão do
    BCP, veja o [Gerenciador de pagamentos Pix](pix-payment-handler.md)
    (`br.dev.bcp.pix`), cujo fluxo é mais simples por não exigir tokenização
    do lado da plataforma.

### Escopo

Este guia se aplica a:

- **Manipuladores** (por exemplo, `com.google.pay`, `dev.shopify.shop_pay`) — implementações
  específicas de métodos de pagamento

---

## Conceitos Básicos

Cada especificação de manipulador de pagamento **DEVE** definir os elementos principais abaixo.

**Nota sobre assinaturas de protocolo:** As assinaturas de função fornecidas nesta
seção (por exemplo, `PROCESSING(...)`) representam **fluxos de dados lógicos**, não
chamadas de função literais. Os autores de especificações devem mapear esses fluxos lógicos para o
protocolo de transporte real usado por sua implementação.

```text
+------------------------------------------------------------------------------+
|                        Payment Handler Framework                             |
+------------------------------------------------------------------------------+
|                                                                              |
|   +--------------+                                                           |
|   | PARTICIPANTS |  Who participates in this handler?                        |
|   +------+-------+                                                           |
|          |                                                                   |
|          v                                                                   |
|   +--------------+                                                           |
|   |PREREQUISITES |  How does each participant obtain identity & configs?     |
|   +------+-------+                                                           |
|          |                                                                   |
|          +--------------------+----------------------+                       |
|          v                    v                      v                       |
|   +--------------+    +--------------+      +--------------+                 |
|   |   HANDLER    |    |  INSTRUMENT  |      |  PROCESSING  |                 |
|   | DECLARATION  |    |  ACQUISITION |      |              |                 |
|   +--------------+    +--------------+      +--------------+                 |
|   Business advertises  platform acquires     Participant                     |
|   handler config       checkout instrument   processes instrument            |
|                                                                              |
+------------------------------------------------------------------------------+
```

### Participantes

**Definição:** Os distintos atores que participam do processo do manipulador de pagamento
ciclo de vida. Cada manipulador tem no mínimo dois participantes (negócios e
plataforma), mas **PODE** definir participantes adicionais com funções específicas.

**Nota sobre terminologia:** Embora este guia se refira ao participante como
**"Negócios"**, os campos do esquema técnico podem manter a nomenclatura padrão do
setor **`merchant_*`** (por exemplo, `merchant_id`, `merchant_name`).
As especificações **DEVEM** documentar explicitamente esses mapeamentos de campo.

**Participantes Padrão:**

| Participante | Função |
| :----------- | :-------------------------------------------------------------------------------- |
| **Negócios** | Anuncia configuração de manipulador, processa instrumentos de pagamento |
| **Plataforma** | Descobre manipuladores, adquire instrumentos de pagamento, finaliza checkout |

**Participantes estendidos** (exemplo de participantes específicos do manipulador):

| Participante | Exemplo de função |
| :----------- | :--------------------------------------------------------------------- |
| **Tokenizador** | Armazena credenciais brutas e emite credenciais de token |
| **PSP** | Processa pagamentos em nome de empresas usando o instrumento de checkout |

### Pré-requisitos

**Definição:** a integração, instalação ou configuração que um participante deve
concluir antes de participar dos fluxos do manipulador.

**Assinatura:**

```text
PREREQUISITES(participant, onboarding_input) → prerequisites_output
```

| Campo | Descrição |
| :--------------------- | :------------------------------------------------------------------- |
| `participant` | O participante que está sendo integrado (negócio, plataforma, etc.) |
| `onboarding_input` | O que o participante fornece durante a configuração |
| `prerequisites_output` | A identidade e qualquer configuração adicional recebida |

**Saída de pré-requisitos:**

O `prerequisites_output` contém o que o participante recebe no onboarding.
No mínimo, isso inclui uma **identidade** (consulte [Identidade de pagamento](site:schemas/shopping/types/payment_identity.json)).
**PODE** também incluir configurações, credenciais ou configurações adicionais
específico para o manipulador.

As especificações do manipulador de pagamento **não precisam** definir um esquema formal
para `prerequisites_output`. Em vez disso, a especificação **DEVE** documentar
claramente:

- Qual identidade é atribuída (e como ela é mapeada para `PaymentIdentity`)
- Que configuração adicional é fornecida
- Como a saída de pré-requisitos é usada na Declaração do Manipulador, Aquisição de Instrumento ou Processamento

**Notas:**

- Os pré-requisitos normalmente ocorrem fora da banda (portais, contratos, chamadas de API)
- Vários participantes **PODEM** ter pré-requisitos independentes
- A identidade dos pré-requisitos normalmente aparece no manipulador
  Objeto `config` (por exemplo, como `merchant_id` ou campo específico do manipulador semelhante)
- Os participantes que recebem credenciais brutas (por exemplo, empresas, PSPs) normalmente devem preencher confirmações de segurança durante a integração, aceitando a responsabilidade pelo manuseio e conformidade das credenciais

### Declaração do manipulador

**Definição:** a configuração que uma empresa anuncia para indicar suporte para
esse manipulador e permitir que as plataformas o invoquem.

**Assinatura:**

```text
HANDLER_DECLARATION(prerequisites_output) → handler_declaration
```

| Campo | Descrição |
| :--------------------- | :----------------------------------------------------------------------- |
| `prerequisites_output` | A identidade e configuração dos pré-requisitos de negócios |
| `handler_declaration` | O objeto manipulador anunciado em `ucp.payment_handlers` |

**Estrutura de saída:**

A declaração do manipulador está em conformidade com [`PaymentHandler`](site:schemas/payment_handler.json)
esquema. A especificação **DEVE** definir a configuração e o instrumento disponíveis
esquemas e como construir cada um com base na saída de pré-requisitos do negócio
e configuração desejada.

<!-- ucp:example schema=profile def=business_schema target=$.ucp.payment_handlers -->
```json
{
  "com.example.handler": [
    {
      "id": "processor_tokenizer_1234",
      "version": "{{ bcp_schema_version }}",
      "spec": "https://example.com/bcp/handler",
      "schema": "https://example.com/bcp/handler/schema.json",
      "available_instruments": [ ... ],
      "config": {
        // Handler-specific configuration (see Config Shapes)
      }
    }
  ]
}
```

**`available_instruments`** é opcional. Quando ausente, o manipulador não impõe
nenhuma restrição de tipo de instrumento — suporta o conjunto completo de
tipos de instrumentos definidos por seu esquema. Quando presente, restringe os
tipos anunciados e/ou aplica restrições adicionais (por exemplo, limitando as
marcas de cartão para `["visa", "mastercard"]`).

---

#### Variantes de declaração do manipulador

O esquema `PaymentHandler` define três variantes para diferentes contextos. Embora apenas
`id` e `version` sejam tecnicamente exigidos, cada variante tem uma finalidade distinta
e normalmente inclui configurações diferentes:

| Variante | Contexto | Finalidade |
| :------ | :------ | :------ |
| **`business_schema`** | Descoberta de negócios (`/.well-known/bcp`) | Declara a identidade comercial e como elas estão configuradas para esse manipulador. Contém configurações específicas do comerciante. |
| **`platform_schema`** | Perfil da plataforma (URI anunciado) | Declara a identidade da plataforma e como ela suporta este manipulador. Inclui URLs `spec` e `schema` para implementadores. |
| **`response_schema`** | Respostas da API de checkout/pedido | **Configuração de tempo de execução** com contexto resolvido: identidade do comerciante, `available_instruments` resolvido para este checkout, especificações de tokenização e outros estados necessários para processar a transação. As plataformas **DEVEM** tratar isso como oficial. |

**Exemplo de esquema de negócios** (a empresa declara a configuração do manipulador):

<!-- ucp:example schema=payment_handler def=business_schema -->
```json
{
  "id": "processor_tokenizer_1234",
  "version": "{{ bcp_schema_version }}",
  "spec": "https://example.com/bcp/handler",
  "schema": "https://example.com/bcp/handler/schema.json",
  "available_instruments": [
    {
      "type": "card",
      "constraints": {
        "brands": ["visa", "mastercard"]
      }
    }
  ],
  "config": {
    "environment": "production",
    "business_id": "business_xyz_789"
  }
}
```

**Exemplo de esquema de plataforma** (a plataforma declara suporte ao manipulador):

<!-- ucp:example schema=payment_handler def=platform_schema -->
```json
{
  "id": "platform_tokenizer_2345", // note: ids are for disambiguation, they may differ between business and platform
  "version": "{{ bcp_schema_version }}",
  "spec": "https://example.com/bcp/handler",
  "schema": "https://example.com/bcp/handler/schema.json",
  "available_instruments": [
    {
      "type": "card",
      "constraints": {
        "brands": ["visa", "mastercard", "amex", "discover"]
      }
    }
  ],
  "config": {
    "environment": "production",
    "platform_id": "platform_abc_123"
  }
}
```

**Exemplo de esquema de resposta** (contexto de tempo de execução para checkout):

<!-- ucp:example schema=payment_handler def=response_schema -->
```json
{
  "id": "processor_tokenizer_1234",
  "version": "{{ bcp_schema_version }}",
  "available_instruments": [
    {
      "type": "card",
      "constraints": {
        "brands": ["visa", "mastercard"]
      }
    }
  ],
  "config": {
    "api_version": 2,
    "environment": "production",
    "business_id": "business_xyz_789"
  }
}
```

#### Resolvendo `available_instruments`

Tanto a plataforma quanto o negócio anunciam de forma independente `available_instruments`
em seus perfis. A empresa é responsável por resolvê-los no
valor autoritativo retornado em `response_schema`.

**Fluxo de resolução:**

1. **Plataforma declara capacidades** — o perfil da plataforma inclui
   `available_instruments` em cada declaração do manipulador. Isso diz à empresa
   o que a plataforma pode suportar (por exemplo, ela suporta apenas
   `["visa", "mastercard", "amex", "discover"]`).

2. **A empresa resolve** — ao receber uma solicitação, a empresa calcula o
   resolveu `available_instruments` para o checkout cruzando:
   - O `available_instruments` anunciado da plataforma (suas capacidades)
   - Sua própria declaração `business_schema` (o que o comerciante está realmente preparado para aceitar)
   - Contexto de carrinho/checkout (por exemplo, certos tipos de itens podem restringir métodos elegíveis)

3. **A resposta é oficial** — o `available_instruments` no
   `response_schema` reflete a seleção decidida do negócio para este específico
   checkout. As plataformas **DEVEM** tratá-lo como oficial e **NÃO DEVEM** tentar
   usar tipos de instrumentos ou aplicar restrições que os contradigam.

**Exemplo:**

| Fonte | `available_instruments` |
| :----- | :---------------------- |
| Perfil da plataforma | `[{type: "card", constraints: {brands: ["visa", "mastercard", "amex", "discover"]}}]` |
| Perfil empresarial | `[{type: "card", constraints: {brands: ["visa", "mastercard", "amex"]}}]` |
| **Resposta (resolvida)** | `[{type: "card", constraints: {brands: ["visa", "mastercard", "amex"]}}]` |

Neste exemplo, o PSP da empresa não está configurado para o Discover, então o Discover
é excluído da resposta mesmo que a plataforma o suporte.

---

#### Definindo o Esquema

O campo `schema` aponta para um esquema JSON que define formas específicas do manipulador.
Os autores normalmente definem cada forma em seu próprio arquivo e fazem referência a elas:

- **Config** — Configuração para declarações de plataforma/negócio e respostas de tempo de execução
- **Instrumento** — A estrutura do instrumento de pagamento retornada às plataformas
- **Credencial** — A estrutura de credenciais nos instrumentos

**Exemplo de esquema de manipulador:**

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/schema.json",
  "title": "Tokenizer Handler Schema",
  "description": "Schema for the com.example.tokenizer payment handler.",
  "name": "com.example.tokenizer",
  "version": "{{ bcp_schema_version }}",

  "$defs": {
    "tokenizer_token": { "$ref": "types/tokenizer_token.json" },
    "tokenizer_alt_token": { "$ref": "types/tokenizer_alt_token.json" },

    "tokenizer_instrument": { "$ref": "types/tokenizer_instrument.json" },
    "tokenizer_alt_instrument": { "$ref": "types/tokenizer_alt_instrument.json" },

    "com.example.tokenizer": {
      "payment_instrument": {
        "title": "Tokenizer Payment Instrument",
        "description": "Any instrument type supported by this handler.",
        "oneOf": [
          { "$ref": "#/$defs/tokenizer_instrument" },
          { "$ref": "#/$defs/tokenizer_alt_instrument" }
        ]
      },
      "platform_schema": {
        "title": "Tokenizer (Platform)",
        "description": "Platform-level handler configuration for discovery.",
        "allOf": [
          { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/payment_handler.json#/$defs/platform_schema" },
          {
            "properties": {
              "config": {
                "$ref": "types/platform_config.json",
                "description": "Platform configuration for this handler."
              }
            }
          }
        ]
      },
      "business_schema": {
        "title": "Tokenizer (Business)",
        "description": "Business-level handler configuration for discovery.",
        "allOf": [
          { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/payment_handler.json#/$defs/business_schema" },
          {
            "properties": {
              "config": {
                "$ref": "types/business_config.json",
                "description": "Business configuration for this handler."
              }
            }
          }
        ]
      },
      "response_schema": {
        "title": "Tokenizer (Response)",
        "description": "Runtime handler configuration in checkout responses.",
        "allOf": [
          { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/payment_handler.json#/$defs/response_schema" },
          {
            "properties": {
              "config": {
                "$ref": "types/response_config.json",
                "description": "Runtime configuration for this handler."
              }
            }
          }
        ]
      }
    }
  }
}
```

---

#### Formas de configuração

Cada variante tem seu próprio esquema de configuração adaptado ao seu contexto:

| Variante | Arquivo de configuração | Finalidade |
| :------ | :---------- | :------ |
| **`business_schema`** | `types/business_config.json` | Identidade comercial e configurações específicas do comerciante |
| **`platform_schema`** | `types/platform_config.json` | Identidade da plataforma e configurações no nível da plataforma |
| **`response_schema`** | `types/response_config.json` | Estado de tempo de execução completo: identidades, especificações de tokenização |

**Exemplo `types/business_config.json`:**

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/business_config.json",
  "title": "Tokenizer Business Config",
  "type": "object",
  "properties": {
    "environment": {
      "type": "string",
      "enum": ["sandbox", "production"],
      "default": "production"
    },
    "business_id": {
      "type": "string",
      "description": "Business identifier for this handler."
    }
  }
}
```

**Exemplo `types/platform_config.json`:**

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/platform_config.json",
  "title": "Tokenizer Platform Config",
  "type": "object",
  "properties": {
    "environment": {
      "type": "string",
      "enum": ["sandbox", "production"],
      "default": "production"
    },
    "platform_id": {
      "type": "string",
      "description": "Platform identifier for this handler."
    }
  }
}
```

**Exemplo `types/response_config.json`:**

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/response_config.json",
  "title": "Tokenizer Response Config",
  "type": "object",
  "properties": {
    "api_version": { "type": "integer" },
    "environment": {
      "type": "string",
      "enum": ["sandbox", "production"]
    },
    "business_id": {
      "type": "string",
      "description": "Business identifier for this handler."
    },
    "tokenization_specification": {
      "type": "object",
      "description": "Handler-specific tokenization settings.",
      "properties": {
        "type": { "type": "string" },
        "parameters": { "type": "object" }
      }
    }
  }
}
```

---

#### Formas de instrumentos

**Esquemas de instrumentos básicos:**

| Esquema | Descrição |
| :--------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------- |
| [`payment_instrument.json`](site:schemas/shopping/types/payment_instrument.json) | Base: id, handler_id, tipo, billing_address, credencial, display |
| [`card_payment_instrument.json`](site:schemas/shopping/types/card_payment_instrument.json) | Amplia a base com display: marca, last_digits, vencimento, arte do cartão |

O BCP fornece esquemas básicos para instrumentos de pagamento universais como `card`. Os autores
de especificações **PODEM** estender qualquer um dos instrumentos básicos para adicionar dados de
exibição específicos do manipulador ou personalizar a referência de credencial. Manipuladores
**PODEM** definir vários tipos de instrumentos para diferentes fluxos de pagamento.

**Esquemas de instrumentos disponíveis:**

Cada esquema de instrumento define sua própria variante `available_*` em `$defs` que
especifica quais restrições são válidas para esse tipo de instrumento. Por exemplo,
[`card_payment_instrument.json`](site:schemas/shopping/types/card_payment_instrument.json)
define `available_card_payment_instrument` com uma restrição `brands`.

| Esquema | Restrições |
| :----------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------- |
| [`available_payment_instrument.json`](site:schemas/shopping/types/available_payment_instrument.json) | Base: tipo, restrições (objeto aberto) |
| `card_payment_instrument.json#/$defs/available_card_payment_instrument` | Amplia base com `constraints.brands` para redes de placas |

Os manipuladores fazem referência a esses esquemas definidos pelo instrumento ao declarar
`available_instruments`. Os **autores do esquema do instrumento** definem o que
as restrições são significativas (por exemplo, `brands` para cartões) e **plataformas/empresas** usam isso para anunciar o que suportam (por exemplo, `["visa", "mastercard"]`).

**Exemplo `types/tokenizer_instrument.json`**:

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/tokenizer_instrument.json",
  "title": "Tokenizer Card Instrument",
  "description": "Card-based payment instrument for com.example.tokenizer.",

  "$defs": {
    "available_tokenizer_card": {
      "title": "Available Tokenizer Card",
      "description": "Card instrument availability with tokenizer-specific constraints.",
      "allOf": [
        { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/types/card_payment_instrument.json#/$defs/available_card_payment_instrument" },
        {
          "type": "object",
          "properties": {
            "type": { "const": "tokenizer_card" },
            "constraints": {
              "type": "object",
              "properties": {
                "tokenization_types": {
                  "type": "array",
                  "items": { "type": "string" },
                  "description": "Supported tokenization types (e.g., ['network_token', 'merchant_token'])."
                }
              }
            }
          }
        }
      ]
    }
  },

  "allOf": [
    { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/types/card_payment_instrument.json" }
  ],
  "type": "object",
  "required": ["type"],
  "properties": {
    "type": { "const": "tokenizer_card" },
    "credential": {
      "oneOf": [
        { "$ref": "tokenizer_token.json" },
        { "$ref": "tokenizer_alt_token.json" }
      ]
    },
    "special_tokenizer_context": {
      "type": "object",
      "description": "Handler-specific context for tokenizer instruments."
    }
  }
}
```

**Exemplo `types/tokenizer_alt_instrument.json`:**

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/tokenizer_alt_instrument.json",
  "title": "Tokenizer Alt Instrument",
  "description": "Alternative payment instrument for com.example.tokenizer.",
  "allOf": [
    { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/types/payment_instrument.json" }
  ],
  "type": "object",
  "required": ["type"],
  "properties": {
    "type": { "const": "tokenizer_alt" },
    "credential": {
      "oneOf": [
        { "$ref": "tokenizer_token.json" },
        { "$ref": "tokenizer_alt_token.json" }
      ]
    },
    "special_tokenizer_context": {
      "type": "object",
      "description": "Handler-specific context for tokenizer instruments."
    }
  }
}
```

---

#### Formas de credenciais

**Esquemas de credenciais básicas:**

| Esquema | Descrição |
| :------------------------------------------------------------------------------------------ | :--------------------------- |
| [`payment_credential.json`](site:schemas/shopping/types/payment_credential.json) | Base: somente discriminador de tipo |
| [`token_credential.json`](site:schemas/shopping/types/token_credential.json) | Token: tipo + string de token |

O BCP fornece esquemas básicos para credenciais de pagamento universais. Os autores **PODEM**
estender esses esquemas para incluir o contexto de credenciais específico do manipulador. Manipuladores
**PODEM** definir vários tipos de credenciais para diferentes fluxos de instrumentos.

A especificação **DEVE** definir quais tipos de credenciais são aceitos pelo
manipulador.

**Importante:** Se estiver usando credenciais de token, o esquema **DEVE** incluir um
campo de expiração (`expiry`, `ttl` ou similar) para garantir que as plataformas saibam quando
atualizar credenciais.

**Exemplo `types/tokenizer_token.json`** (token expirado):

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/tokenizer_token.json",
  "title": "Tokenizer Card Token",
  "description": "Card token credential for com.example.tokenizer.",
  "allOf": [
    { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/types/token_credential.json" }
  ],
  "type": "object",
  "required": ["type", "token", "expiry"],
  "properties": {
    "type": {
      "const": "tokenizer_card_token",
      "description": "Credential type discriminator."
    },
    "expiry": {
      "type": "string",
      "format": "date-time",
      "description": "Token expiration. Platforms must refresh before this time."
    }
  }
}
```

**Exemplo `types/tokenizer_alt_token.json`** (token alternativo):

<!-- ucp:example skip reason="handler schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/bcp/handlers/tokenizer/types/tokenizer_alt_token.json",
  "title": "Tokenizer Alt Token",
  "description": "Alt token credential for com.example.tokenizer, adding routing hints",
  "allOf": [
    { "$ref": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/types/token_credential.json" }
  ],
  "type": "object",
  "required": ["type", "token", "expiry"],
  "properties": {
    "type": {
      "const": "tokenizer_alt_token",
      "description": "Credential type discriminator."
    },
    "expiry": {
      "type": "string",
      "format": "date-time",
      "description": "Token expiration. Platforms must refresh before this time."
    },
    "routing_hint": {
      "type": "string",
      "description": "Optional routing number hint."
    }
  }
}
```

### Aquisição de instrumentos

**Definição:** O protocolo que uma plataforma segue para adquirir um instrumento de pagamento
que pode ser enviado para o checkout da empresa.

**Assinatura:**

```text
INSTRUMENT_ACQUISITION(
  platform_prerequisites_output,
  handler_declaration,
  binding,
  buyer_input
) → checkout_instrument
```

| Campo | Descrição |
| :------------------------------ | :--------------------------------------------------------------------------------- |
| `platform_prerequisites_output` | saída de pré-requisitos da plataforma (config), se pré-requisitos forem necessários |
| `handler_declaration.config` | Configuração específica do manipulador do negócio |
| `binding` | **(Ver 2.6)** Contexto para vincular a credencial a um checkout específico |
| `buyer_input` | Seleção ou credenciais de pagamento do comprador |
| `checkout_instrument` | O instrumento de pagamento a ser enviado na finalização da compra |

As especificações do manipulador de pagamento NÃO precisam definir um processo formal para
aquisição de instrumentos. Em vez disso, a especificação **DEVE** documentar claramente:

- Como aplicar o `config` do manipulador para construir um `checkout_instrument` válido.
- Como criar uma vinculação de credencial eficaz para o checkout e o negócio
  específicos, o que é crítico para a segurança, com base no `config` e no
  `checkout` disponíveis.

### Processamento

**Definição:** As etapas que um participante (normalmente empresarial ou PSP) executa para
processar um instrumento de pagamento recebido e concluir a transação.

**Assinatura:**

```text
PROCESSING(
  identity,
  checkout_instrument,
  binding,
  transaction_context
) → processing_result
```

| Campo | Descrição |
| :-------------------- | :------------------------------------------------------- |
| `identity` | O `PaymentIdentity` do participante do processamento |
| `checkout_instrument` | O instrumento recebido da plataforma |
| `binding` | O contexto vinculativo para verificação |
| `transaction_context` | Totais de checkout, itens de linha, etc. |
| `processing_result` | Sucesso/falha com detalhes de pagamento |

#### Tratamento de erros

A especificação **DEVE** definir um mapeamento para falhas comuns (por exemplo,
'Recusado', 'Fundos insuficientes', 'Erro de rede') para definições de erro
padrão do BCP. Isso garante que a plataforma possa renderizar mensagens de erro
localizadas e consistentes ao comprador, independentemente do processador subjacente.

### Principais Definições

| Termo | Definição |
| :---------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Vinculação** | Uma associação criptográfica ou lógica de um instrumento de pagamento a uma transação de checkout e identidade comercial específicas. Isso evita ataques de repetição em que uma credencial válida destinada à Empresa A é interceptada e usada na Empresa B. |

---

## Modelo de Especificação

As especificações do manipulador **DEVEM** usar a estrutura de modelo padrão. Seções
marcado como **[OBRIGATÓRIO]** **DEVE** estar presente; seções marcadas como **[CONDICIONAL]**
são necessários apenas quando aplicável.

**→ [Modelo de manipulador de pagamento](payment-handler-template.md)**

## Lista de verificação de conformidade para autores de especificações

Antes de publicar uma especificação de gerenciador de pagamento, verifique:

### Estrutura

- [ ] Usa a estrutura de modelo padrão
- [ ] Todas as seções [REQUIRED] estão presentes
- [ ] seções [CONDICIONAIS] estão presentes quando aplicável

### Participantes

- [ ] Todos os participantes estão listados
- [ ] A função de cada participante está claramente descrita
- [ ] Nota sobre a terminologia "Empresa" vs "Comerciante" adicionada, se aplicável

### Pré-requisitos

- [ ] O processo de pré-requisitos é documentado para cada participante que o requer
- [ ] As entradas de integração são especificadas
- [ ] A saída dos pré-requisitos é descrita (identidade + qualquer configuração adicional)
- [ ] Mapas de identidade para a estrutura `PaymentIdentity` (`access_token`)

### Declaração do manipulador

- [ ] O esquema de identidade está documentado (base ou estendido)
- [ ] O esquema de configuração está documentado (se aplicável) e inclui o ambiente
- [ ] O esquema do instrumento está documentado (base ou estendido)

### Aquisição de instrumentos

- [ ] As etapas do protocolo são enumeradas e claras
- [ ] O fluxo lógico é mapeado para o protocolo real
- [ ] chamadas de API ou uso de SDK são mostrados com exemplos
- [ ] Os requisitos de vinculação são especificados
- [ ] A criação e o formato do instrumento de pagamento do Checkout estão bem definidos

### Processamento

- [ ] As etapas de processamento são enumeradas e claras
- [ ] Os requisitos de verificação são especificados
- [ ] O tratamento e mapeamento de erros são abordados

### Segurança

- [ ] Os requisitos de segurança estão listados
- [ ] A verificação de vinculação é necessária
- [ ] Orientações sobre manuseio de credenciais são fornecidas
- [ ] A expiração do token é definida (se aplicável)

### Geral

- [ ] O nome do manipulador segue a convenção de DNS reverso
- [ ] A versão segue o formato AAAA-MM-DD
- [ ] Todos os URLs do esquema correspondem à autoridade do namespace
- [ ] A seção de referências inclui todos os esquemas

---

## Melhores práticas

Siga estas diretrizes para criar manipuladores de alta qualidade e de fácil manutenção
especificações:

### Projeto de esquema

| Prática | Descrição |
| :------------------------------------------ | :------------------------------------------------------------------------------------------------ |
| **Estenda, não reinvente** | Utilize `allOf` para compor esquemas base. Não redefina `brand`, `last_digits`, etc. |
| **Use const para discriminadores** | Defina `credential.type` como `const` para identificar os tipos de credenciais de forma inequívoca.       |
| **Validar antecipadamente** | Publique esquemas em URLs estáveis antes de finalizar a especificação para que os implementadores possam validar. |
| **Incluir vencimento** | Ao projetar credenciais de token, inclua sempre `expiry` ou `ttl`.                     |

### Documentação

| Prática | Descrição |
| :----------------------- | :--------------------------------------------------------------------- |
| **Mostre, não apenas conte** | Inclua exemplos completos de JSON para cada etapa de esquema e protocolo.     |
| **Casos de erros em documentos** | Especifique quais erros podem ocorrer e como os participantes devem lidar com eles. |
| **Versão independente** | A versão do manipulador evolui independentemente das versões principais do BCP.        |

### Segurança

| Prática | Descrição |
| :------------------------------------------ | :--------------------------------------------------------------------------------------- |
| **Requer vinculação** | Sempre vincule credenciais a um checkout específico via `binding`.                   |
| **Minimize a exposição de credenciais** | Projete fluxos para que credenciais brutas (PANs, etc.) afetem o menor número possível de sistemas. |
| **Especifique a vida útil do token** | Documente se os tokens são de uso único, limitados no tempo ou com escopo de sessão.       |

### Manutenção

| Prática | Descrição |
| :------------------------------ | :----------------------------------------------------------------------------------------------------- |
| **Esquemas de host em URLs estáveis** | Os URLs do esquema não devem mudar; use caminhos versionados, se necessário.                                          |
| **Falha normalmente** | Defina respostas de erro claras para cenários de falha comuns.                                             |
| **Link para exemplos** | Consulte as especificações do manipulador existente e o [Guia de Tokenização](tokenization-guide.md) para fluxos comuns. |

---

## Veja também

- **[Guia de tokenização](tokenization-guide.md)** — Guia para construção
  manipuladores de pagamento de tokenização
- **[Manipulador do Google Pay](https://developers.google.com/merchant/ucp/guides/google-pay-payment-handler){ target="_blank" }**
  — Manipulador para integração com Google Pay
- **[Manipulador do Shop Pay](https://shopify.dev/docs/agents/checkout/shop-pay-handler){ target="_blank" }**
  — Manipulador para integração do Shop Pay
