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

# Gerenciador de pagamentos {Nome do manipulador}

* **Nome do manipulador:** `{reverse-dns.name}`
* **Versão:** `{YYYY-MM-DD}`

## Introdução

{Breve descrição do que esse gerenciador permite e do fluxo de pagamento que ele
suporta.}

### Principais benefícios

* {Benefício 1}
* {Benefício 2}
* {Benefício 3}

### Guia de Integração

| Participante | Seção de Integração |
| :----------- | :---------------------------------------------------------- |
| **Negócios** | [Integração de Negócios](#integracao-de-negocios) |
| **Plataforma** | [Integração de plataforma](#integracao-de-plataforma) |

---

## Participantes

{Descreva todos os participantes deste gerenciador e suas funções.}

> **Nota sobre terminologia:**
> Embora esta especificação se refira ao participante como **"negócio",**
> os campos do esquema técnico podem manter a nomenclatura padrão da indústria
> **`merchant_*`** (por exemplo, `merchant_id`). Os mapeamentos estão documentados abaixo.

| Participante | Função | Pré-requisitos |
| :---------------------- | :----------------- | :--------------------------- |
| **Negócios** | {descrição da função} | {Sim/Não — breve descrição} |
| **Plataforma** | {descrição da função} | {Sim/Não — breve descrição} |
| **{Outro participante}** | {descrição da função} | {Sim/Não — breve descrição} |

{Opcional: diagrama ASCII mostrando os relacionamentos dos participantes}

```text
+---------+     +---------------+     +------------+
|Platform |     |   {Provider}  |     |  Business  |
+----+----+     +-------+-------+     +------+-----+
     |                  |                    |
     |  {step 1}        |                    |
     |----------------->|                    |
     |                  |                    |
     |  {step 2}        |                    |
     |<-----------------|                    |
     |                  |                    |
     |  {step 3}                             |
     |-------------------------------------->|
```

---

<!--
  PARTICIPANT INTEGRATION SECTIONS

  Include one section per participant. Each section follows the same structure:
  - Prerequisites (onboarding, setup)
  - Configuration or Protocol (what they need to do)
  - Examples

  Number sections starting from 3. Add more sections as needed for additional participants.
-->

## Integração de Negócios

### Pré-requisitos

Antes de anunciar este gerenciador, as empresas **DEVEM** preencher:

1. {Pré-requisito 1, por exemplo, "Registre-se em {provedor} para obter um identificador comercial"}
2. {Pré-requisito 2}

**Saída de pré-requisitos:**

| Campo | Descrição |
| :---------------------- | :---------------------------------------------------------- |
| `identity.access_token` | {qual identificador é atribuído, por exemplo, business_id} |
| {configuração adicional} | {qualquer configuração adicional de integração} |

### Configuração do manipulador

As empresas anunciam suporte para este gerenciador no registro `payment_handlers`
de seus perfis BCP.

#### Esquema do manipulador

**URL do esquema:** `{schema_url}`

O esquema do manipulador define três variantes de configuração para contextos diferentes. Veja
[Guia do manipulador de pagamentos: definindo o esquema](payment-handler-guide.md#definindo-o-esquema)
para o padrão completo.

| Variante de configuração | Contexto | Finalidade |
| :------------ | :------ | :------ |
| `business_config` | Descoberta de negócios | {descrever campos específicos do negócio} |
| `platform_config` | Descoberta de plataforma | {descrever campos específicos da plataforma} |
| `response_config` | Respostas de checkout | {descrever campos de tempo de execução} |

#### Campos de configuração comercial

| Campo | Tipo | Obrigatório | Descrição |
| :------ | :----- | :------- | :----------- |
| {campo} | {tipo} | {Sim/Não} | {descrição} |

#### Campos de configuração de resposta

| Campo | Tipo | Obrigatório | Descrição |
| :------ | :----- | :------- | :----------- |
| {campo} | {tipo} | {Sim/Não} | {descrição} |

#### Exemplo de declaração do manipulador

<!-- ucp:example skip reason="handler config template" -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "payment_handlers": {
      "{handler_name}": [
        {
          "id": "{handler_id}",
          "version": "{version}",
          "spec": "{spec_url}",
          "schema": "{schema_url}",
          "available_instruments": [
            {
              "type": "{instrument_type}",
              "constraints": {
                // Type-specific constraints
              }
            }
          ],
          "config": {
            // Handler-specific configuration
          }
        }
      ]
    }
  }
}
```

### Processando pagamentos

Ao receber um pagamento com este instrumento de manipulador, as empresas **DEVEM**:

1. **Validar manipulador:** Confirme se `instrument.handler_id` corresponde a um manipulador anunciado.
2. **Garantir a idempotência:** Se a solicitação for uma nova tentativa (corresponde a uma
  `checkout_id` ou chave de idempotência), retorne imediatamente o resultado anterior
  sem reprocessar fundos.
3. **{Etapa 3}:** {descrição}
4. **{Etapa 4}:** {descrição}
5. **Resposta de retorno:** Responda com o estado de checkout finalizado.

{Incluir exemplo de solicitação/resposta se a empresa ligar para um serviço externo}

---

## Integração de plataforma

### Pré-requisitos

Antes de usar este manipulador, as plataformas **DEVEM** concluir:

1. {Pré-requisito 1, por exemplo, "Registre-se em {provedor} para obter um identificador de plataforma"}
2. {Pré-requisito 2}

**Saída de pré-requisitos:**

| Campo | Descrição |
| :---------------------- | :------------------------------------------------------- |
| `identity.access_token` | {que identificador é atribuído} |
| {configuração adicional} | {qualquer configuração adicional de integração} |

### Configuração do manipulador

As plataformas anunciam suporte para este manipulador no registro `payment_handlers`
de seus perfis BCP, usando `platform_config`.

#### Campos de configuração da plataforma

| Campo | Tipo | Obrigatório | Descrição |
| :------ | :----- | :------- | :----------- |
| {campo} | {tipo} | {Sim/Não} | {descrição} |

#### Exemplo de declaração do manipulador de plataforma

<!-- ucp:example skip reason="handler config template" -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "payment_handlers": {
      "{handler_name}": [
        {
          "id": "{handler_id}",
          "version": "{version}",
          "spec": "{spec_url}",
          "schema": "{schema_url}",
          "available_instruments": [
            {
              "type": "{instrument_type}",
              "constraints": {
                // Type-specific constraints the platform supports
              }
            }
          ],
          "config": {
            // Platform-specific configuration
          }
        }
      ]
    }
  }
}
```

### Protocolo de pagamento

As plataformas **DEVEM** seguir este fluxo para adquirir um instrumento de pagamento:

#### Etapa 1: descobrir o manipulador

A Plataforma identifica `{handler_name}` no registro `payment_handlers` do perfil
BCP do negócio (`/.well-known/bcp`).

<!-- ucp:example skip reason="handler config template" -->
```json
{
  "ucp": {
    "payment_handlers": {
      "{handler_name}": [
        {
          "id": "{handler_id}",
          "version": "{version}",
          "available_instruments": [
            {"type": "{instrument_type}"}
          ],
          "config": {
            // Business's configuration
          }
        }
      ]
    }
  }
}
```

#### Etapa 2: {Nome da ação}

{Descrição do que a Plataforma faz nesta etapa.}

{Exemplo de código, se aplicável:}

```javascript
// Example SDK usage or API call
```

#### Etapa 3: {Nome da ação}

{Continue para todas as etapas...}

#### Etapa N: Concluir a finalização da compra

A Plataforma submete o checkout com o instrumento de pagamento construído.

<!-- ucp:example skip reason="handler config template" -->
```json
POST /checkout-sessions/{checkout_id}/complete
Content-Type: application/json

{
  "payment": {
    "instruments": [
      {
        "id": "{instrument_id}",
        "handler_id": "{handler_id}",
        "type": "{instrument_type}",
        "credential": {
          "type": "{credential_type}",
          // Credential fields
        }
        // Additional instrument fields
      }
    ]
  },
  "signals": {
    // Platform-observed signals (buyer connection and device)
  }
}
```

---

<!--
  ADDITIONAL PARTICIPANT SECTIONS

  Add one section per additional participant (PSP, Tokenizer, Wallet Provider, etc.)
  following the same pattern as Business and Platform integration.
-->

## {Participante} Integração

### Pré-requisitos

Antes de participar do fluxo deste gerenciador, {participants} **DEVEM** concluir:

1. {Pré-requisito 1}
2. {Pré-requisito 2}

**Saída de pré-requisitos:**

| Campo | Descrição |
| :---------------------- | :------------------------------------------------------- |
| `identity.access_token` | {que identificador é atribuído} |
| {configuração adicional} | {qualquer configuração adicional de integração} |

### {Ação ou configuração}

{Descreva o que este participante precisa fazer.}

{Inclua exemplos conforme apropriado.}

---

## Considerações de segurança

| Requisito | Descrição |
| :--------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Vinculação necessária** | As credenciais **DEVEM** estar vinculadas a `checkout_id` e `identity` para evitar reutilização.                                                                                       |
| **Colocação da vinculação** | Dados de vinculação (por exemplo, `checkout_id`) **DEVEM** ser incluídos na carga útil `credential` para garantir que sejam cobertos pela assinatura, e não nos cabeçalhos de transporte. |
| **Vinculação verificada** | O participante do processamento **DEVE** verificar as correspondências vinculativas antes do processamento.                                                                                         |
| **Expiração do token** | {Se estiver usando tokens: os tokens **DEVEM** expirar após {duration} ou de uso único.} |
| **Residência de Dados** | {Especifique se os dados pessoais **DEVEM** ser processados/armazenados em regiões geográficas específicas (por exemplo, no Brasil, para cumprir a LGPD) para atender às leis locais.} |
| **{Requisito adicional}** | {descrição} |

---

## Referências

* **Especificações do manipulador:** `{spec_url}`
* **Esquema do manipulador:** `{schema_url}` (define configuração, instrumento e formas de credencial)
