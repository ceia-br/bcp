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

# Extensão de mandatos AP2

## Visão geral

A extensão AP2 Mandates permite a troca segura de intenções do usuário e
autorizações usando **Credenciais Digitais Verificáveis**. Ela estende a
capacidade padrão do Shopping Service Checkout para oferecer suporte ao
**[Protocolo AP2](https://ap2-protocol.org/){ target="_blank" }**.

Quando esta capacidade é negociada e ativa, ela transforma uma sessão de
checkout padrão em um contrato vinculado criptograficamente:

* **As empresas** **DEVEM** incorporar uma assinatura criptográfica na finalização da compra
    respostas, provando que os termos (preço, itens de linha) são autênticos.
* **Plataformas** **DEVEM** fornecer provas assinadas criptograficamente (Mandatos)
    durante a operação `complete`, comprovando que o usuário autorizou explicitamente a
    estado de checkout específico e transferência de fundos.

**Vinculação de Segurança:** Depois que esta extensão for negociada na interseção
de recursos, a sessão ficará **travada por segurança**. Nenhuma das partes poderá voltar a
um fluxo de checkout padrão (desprotegido).

**Independência de instrumento:** o mandato AP2 protege a intenção de
checkout, não o instrumento de pagamento em si — ele se aplica igualmente a
Pix (o manipulador padrão do BCP, veja
[Gerenciador de pagamentos Pix](pix-payment-handler.md)), cartão ou qualquer
outro manipulador negociado. Os exemplos abaixo usam cartão apenas para
ilustrar o formato genérico do campo `credential`.

![Diagrama de sequência de fluxo AP2 de alto nível](site:specification/images/ucp-ap2-checkout-flow.png)

### Projeto

Todos os campos específicos do AP2 estão aninhados em um objeto `ap2` nas solicitações e
respostas. Este projeto fornece:

* **Modularidade do esquema** — O esquema de checkout básico permanece limpo; AP2 adiciona um
    campo contendo todos os seus dados.
* **Canonização consistente** — Uma regra: excluir `ap2` do cálculo de
    assinatura do negócio. Os campos AP2 futuros são tratados automaticamente.
* **Coexistência de extensões** — Várias extensões de segurança podem coexistir
    sem colisões de namespace.
* **Sinal de capacidade** — A presença do objeto `ap2` indica claramente que o
    AP2 está ativo.

## Descoberta e Negociação

Esta extensão segue o protocolo de negociação padrão do BCP. Está ativada
somente quando aparece na **Interseção de Capacidades** tanto do negócio
quanto da plataforma.

### Anúncio do perfil da empresa

As empresas declaram apoio adicionando `br.dev.bcp.shopping.ap2_mandate` à sua
lista `capabilities` em `/.well-known/bcp`.

**Exemplo de perfil comercial:**

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {},
    "capabilities": {
      "br.dev.bcp.shopping.checkout": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/checkout",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/checkout.json"
        }
      ],
      "br.dev.bcp.shopping.ap2_mandate": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/ap2-mandates",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/ap2_mandate.json",
          "extends": "br.dev.bcp.shopping.checkout",
          "config": {
            "vp_formats_supported": {
              "dc+sd-jwt": { }
            }
          }
        }
      ]
    },
    "payment_handlers": {}
  }
}
```

### Anúncio do perfil da plataforma

As plataformas declaram apoio em seu perfil. Se a plataforma estiver operando sob o
modelo de provedor de plataforma confiável, a plataforma **DEVE** fornecer pelo menos um
tipo de chave na matriz `keys` de nível superior em seu perfil.

### Ativação e bloqueio de sessão

1. A plataforma anuncia seu URI de perfil (mecanismo específico de transporte).
2. A empresa busca o perfil e calcula a interseção.
3. Se `br.dev.bcp.shopping.ap2_mandate` estiver presente na intersecção:
    * O negócio **DEVE** incluir `ap2.merchant_authorization` em todas
        as respostas de checkout.
    * A empresa **NÃO DEVE** aceitar uma solicitação `complete_checkout` que
        não possui `ap2.checkout_mandate`.
    * A plataforma **DEVE** verificar a assinatura da empresa antes de apresentar
        o checkout para o usuário.

### Requisitos-chave de assinatura

Para utilizar esta extensão, uma chave de assinatura pública **DEVE** estar disponível para a
empresa verificar a assinatura do mandato.

* **Fluxo do Provedor da Plataforma:** Chave fornecida no `keys` do perfil da plataforma.
* **Fluxo de credencial do usuário:** Chave vinculada à credencial de pagamento digital.

Se uma chave pública não puder ser resolvida ou se a assinatura for inválida, a empresa
**DEVE** retornar um erro.

## Requisitos criptográficos

Esta extensão usa as primitivas criptográficas definidas na
especificação de [Assinaturas de mensagens](signatures.md):

* **Algoritmo:** de acordo com a regra de assinatura JWT do Checkout do AP2 — o AP2 v0.2 requer
  ECDSA (`ES256`/`ES384`/`ES512`); veja a nota abaixo.
* **Canonização:** JCS ([RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785))
* **Formato de chave:** JWK ([RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517))
* **Descoberta de chave:** `keys[]` em `/.well-known/bcp` (consulte
  [Descoberta de chave](overview.md#descoberta-de-chave))

Consulte [Assinaturas de mensagens](signatures.md) para formato e rotação de chaves.

> **Nota (requisito de algoritmo).** AP2 vincula o Mandato de Pagamento ao
> checkout via `hash(checkout_jwt)`; a propriedade de segurança subjacente é a
> imprevisibilidade, por sessão, dos bytes assinados — o que o `id` de sessão
> do Checkout do BCP fornece estruturalmente. O AP2 v0.2 é internamente
> inconsistente sobre como exigir isso: `specification.md` declara uma regra
> de classe de algoritmo (apenas não determinística, por exemplo, ECDSA),
> enquanto as Considerações de Segurança e Privacidade estabelecem uma regra
> de entropia, satisfeita por qualquer algoritmo com entropia de carga útil
> suficiente. A discussão em
> [AP2 #268](https://github.com/google-agentic-commerce/AP2/issues/268)
> converge para a formulação de entropia. Siga o AP2 para a regra definitiva;
> sob a leitura de entropia, um JWT de checkout do BCP pode ser assinado com
> qualquer algoritmo (incluindo Ed25519), deixando uma única chave servir
> tanto à assinatura de mandato AP2 quanto ao Web Bot Auth.

### Autorização Comercial

As empresas **DEVEM** incorporar sua assinatura no corpo da resposta de checkout em
`ap2.merchant_authorization` usando formato **JWS Detached Content**
([RFC 7515 Apêndice F](https://datatracker.ietf.org/doc/html/rfc7515#appendix-F){target="_blank"}).

**Resposta de checkout com assinatura incorporada:**

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "chk_abc123",
  "status": "ready_for_complete",
  "currency": "BRL",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ],
  "ap2": {
    "merchant_authorization": "eyJhbGciOiJFUzI1NiIsImtpZCI6Im1lcmNoYW50XzIwMjUifQ..<signature>"
  }
}
```

O valor `merchant_authorization` é um JWS com payload desanexado no formato
`<header>..<signature>`. O ponto duplo (`..`) indica que a carga útil está
transmitida separadamente (como o próprio corpo do checkout).

**Reivindicações de cabeçalho JWS:**

| Reivindicação | Tipo | Obrigatório | Descrição |
| :---- | :----- | :------- | :------------------------------------------------- |
| `alg` | string | Sim | Algoritmo de assinatura aceito pelo AP2 (ex. `ES256`) |
| `kid` | string | Sim | ID da chave referenciando o `keys` do negócio |

**Cálculo de assinatura:**

A assinatura **DEVE** abranger tanto o cabeçalho JWS quanto a carga útil do checkout. Isto
evita ataques de substituição de algoritmo onde um invasor modifica a reivindicação
`alg` sem invalidar a assinatura.

```text
sign_checkout(checkout, private_key, kid, alg="ES256"):
    // Extract payload (checkout minus ap2)
    payload = checkout without "ap2" field

    // Canonicalize using JCS (RFC 8785)
    canonical_bytes = jcs_canonicalize(payload)

    // Create protected header
    header = {"alg": alg, "kid": kid}
    encoded_header = base64url_encode(json_encode(header))

    // Sign header + payload per JWS
    signing_input = encoded_header + "." + base64url_encode(canonical_bytes)
    signature = sign(signing_input, private_key, alg)

    // Return detached JWS (header..signature, no payload)
    checkout.ap2.merchant_authorization = encoded_header + ".." + base64url_encode(signature)
    return checkout
```

### Estrutura do Mandato

Os mandatos são credenciais **SD-JWT** com Key Binding (`+kb`). A plataforma
**DEVE** produzir dois artefatos de mandato distintos:

| Mandato | Colocação no BCP | Finalidade |
| :------------------- | :--------------------------------------------------- | :---------------------------------------------------------------- |
| **checkout_mandate** | `ap2.checkout_mandate` | Prova vinculada aos termos de checkout protege os negócios |
| **payment_mandate** | `payment.instruments[*].credential.token` | Comprovante vinculado à autorização de pagamento protege fundos |

O mandato de checkout **DEVE** conter a resposta de checkout completa, incluindo o
Campo `ap2.merchant_authorization`. Isso cria uma ligação criptográfica aninhada
onde a assinatura da plataforma cobre a assinatura da empresa.

**Limite de especificação:** Esta extensão define *onde* os mandatos são colocados
nas solicitações e respostas do BCP. A estrutura de credenciais do mandato (reivindicações,
divulgação seletiva, vinculação de chave) é definida pelo
[Especificação do Protocolo AP2](https://ap2-protocol.org/specification).

### Canonização

Todas as cargas JSON **DEVEM** ser canonizadas usando **Canonização JSON
Esquema (JCS)** de acordo com [RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785).

**Por que JCS para Mandatos?** As assinaturas de solicitação BCP usam `Content-Digest` (bruto
bytes) sem canonização — a solicitação é assinada e verificada
imediatamente pela mesma conexão HTTP. Os mandatos são diferentes:

* **Durabilidade** — Os mandatos são armazenados como prova do consentimento do usuário. Eles podem
    ser recuperados e verificados dias ou meses depois.
* **Transmissão entre sistemas** — Os mandatos passam por vários sistemas
    (plataforma → negócio → PSP → rede de cartões) que pode serializar novamente o JSON.
* **Reprodutibilidade** — Qualquer parte deve reconstruir os bytes assinados exatos
    do conteúdo JSON lógico, independentemente das diferenças de serialização.

JCS garante que JSON semanticamente idêntico produza saída idêntica em bytes,
tornando as assinaturas reproduzíveis entre implementações e tempo.

**Regra Específica do AP2:** Ao calcular a assinatura `merchant_authorization`
do negócio, exclua totalmente o campo `ap2`. Isso garante que futuros campos
AP2 sejam tratados automaticamente.

## O Fluxo do Mandato

Uma vez negociada a capacidade `br.dev.bcp.shopping.ap2_mandate`, a sessão
está bloqueada no fluxo a seguir. Ambas as partes **DEVEM** seguir estas etapas para
garantir a integridade criptográfica; qualquer tentativa de ignorar essas etapas ou enviar
uma solicitação de conclusão sem mandatos **DEVE** resultar em uma falha de sessão.

### Etapa 1: Criação e assinatura do checkout

A plataforma inicia a sessão. O negócio retorna o objeto `Checkout`
com `ap2.merchant_authorization` embutido no corpo da resposta.

{{ extension_schema_fields('ap2_mandate.json#/$defs/br.dev.bcp.shopping.checkout', 'ap2-mandates') }}

**Exemplo de resposta:**

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": { ... },
  "id": "chk_abc123",
  "status": "ready_for_complete",
  "currency": "BRL",
  "line_items": [
    {
      "id": "li_1",
      "item": {"id": "item_123", "title": "Widget", "price": 2500},
      "quantity": 2,
      "totals": [
        {"type": "subtotal", "amount": 5000},
        {"type": "total", "amount": 5000}
      ]
    }
  ],
  "totals": [
    {"type": "subtotal", "amount": 5000},
    {"type": "tax", "amount": 400},
    {"type": "total", "amount": 5400}
  ],
  "links": [ ... ],
  "ap2": {
    "merchant_authorization": "eyJhbGciOiJFUzI1NiIsImtpZCI6Im1lcmNoYW50XzIwMjUifQ..<signature>"
  }
}
```

A plataforma **DEVE** verificar a assinatura:

```text
verify_merchant_authorization(checkout, merchant_profile):
    // Parse detached JWS (header..signature)
    jws = checkout.ap2.merchant_authorization
    [encoded_header, empty, encoded_signature] = jws.split(".")

    // Decode and validate header
    header = json_decode(base64url_decode(encoded_header))
    assert header.alg in ap2_accepted_algorithms  // ES256/ES384/ES512 per AP2 v0.2

    // Reconstruct signed payload (checkout minus ap2)
    payload = checkout without "ap2" field
    canonical_bytes = jcs_canonicalize(payload)

    // Reconstruct signing input (header + payload)
    signing_input = encoded_header + "." + base64url_encode(canonical_bytes)

    // Get business's public key and verify
    public_key = get_key_by_kid(merchant_profile.keys, header.kid)
    return verify(encoded_signature, signing_input, public_key, header.alg)
```

### Etapa 2: Consentimento do usuário e geração de mandato

Quando o usuário confirma a compra, a plataforma **DEVE** facilitar a
geração de mandatos verificáveis criptograficamente.

#### Opção 1: Provedor de plataforma confiável

Um provedor de plataforma confiável atua em nome do usuário para gerar as
credenciais de mandato. O provedor da plataforma **DEVE** garantir que os mandatos
não são criados sem o consentimento explícito do usuário, obtido a partir de
canais confiáveis e determinísticos.

Mediante consentimento do usuário, a plataforma assina os mandatos usando a chave
do seu servidor. A empresa confia que a assinatura da plataforma implica o consentimento do usuário.

#### Opção 2: credencial de pagamento digital

Neste modelo, o usuário possui um VDC emitido por uma fonte confiável para a empresa
(por exemplo: uma credencial de pagamento digital emitida por um banco ou rede).

A plataforma solicita uma apresentação através de um protocolo como OpenID4VP. A
Wallet do usuário (ou equivalente) processa a solicitação e assina os mandatos usando a
chave privada associada à sua credencial de pagamento.

A empresa confia no Emissor da Credencial (Banco) e verifica a assinatura de
Key Binding do usuário (+kb).

### Etapa 3: Envio (`complete_checkout`)

Uma vez gerados os mandatos, a plataforma os envia na solicitação de
conclusão (`complete`):

{{ extension_schema_fields('ap2_mandate.json#/$defs/ap2_with_checkout_mandate', 'ap2-mandates') }}

<!-- ucp:example schema=shopping/checkout op=complete direction=request -->
```json
{
  "payment": {
    "instruments": [
      {
        "id": "instr_1",
        "handler_id": "gpay_1234",
        "type": "card",
        "selected": true,
        "display": {
          "description": "Visa •••• 1234"
        },
        "billing_address": {
          "street_address": "Rua Augusta, 123",
          "address_locality": "São Paulo",
          "address_region": "SP",
          "address_country": "BR",
          "postal_code": "01305-000"
        },
        "credential": {
          "type": "PAYMENT_GATEWAY",
          "token": "examplePaymentMethodToken"
        }
      }
    ]
  },
  "ap2": {
    "checkout_mandate": "eyJhbGciOiJFUzI1NiIsInR5cCI6InZjK3NkLWp3dCJ9..." // The User-Signed SD-JWT+kb / platform provider signed SD-JWT / delegated SD-JWT-KB
  }
}
```

* `ap2.checkout_mandate`: O mandato de checkout SD-JWT+kb contendo o
    checkout completo (com `ap2.merchant_authorization`)
* `payment.instruments[*].credential.token`: Contém o mandato de pagamento (token composto)

## Verificação e processamento

### Verificação comercial

Ao receber a solicitação `complete`, a empresa **DEVE**:

1. **Aplicar Negociação:** Se o AP2 foi negociado, rejeite a solicitação com o
    código de erro `mandate_required` se `ap2.checkout_mandate` estiver faltando.

**Verificação de mandato (conforme especificação AP2):**

1. **Verificar Mandato:** Decodifique e verifique a assinatura SD-JWT, ligação de chave,
    e expiração de acordo com o
    [Especificação do Protocolo AP2](https://ap2-protocol.org/specification).
2. **Extrair Checkout Incorporado:** Extraia o objeto checkout do
    reivindicações de mandato verificadas.

**Verificação BCP:**

1. **Verifique a autorização comercial:** Confirme que `ap2.merchant_authorization`,
    no checkout incorporado, é a assinatura válida da própria empresa:

    ```text
    jws = embedded_checkout.ap2.merchant_authorization
    [encoded_header, _, encoded_signature] = jws.split(".")
    header = json_decode(base64url_decode(encoded_header))

    payload = embedded_checkout without "ap2" field
    signing_input = encoded_header + "." + base64url_encode(jcs_canonicalize(payload))

    my_key = get_key_by_kid(my_keys, header.kid)
    verify(encoded_signature, signing_input, my_key, header.alg)
    ```

2. **Verificar a correspondência dos termos:** Confirme se os termos de checkout incorporados correspondem ao
    estado atual da sessão (id, totais, itens de linha).

### Verificação PSP

A empresa passa o `token` (objeto composto) para seu manipulador de
pagamento / PSP. O PSP verifica o `payment_mandate` conforme o
[Especificação do Protocolo AP2](https://ap2-protocol.org/specification),
incluindo validação de assinatura, expiração e correlação com o
checkout.

## Esquema

### Autorização comercial {: #merchant-authorization }

{{ extension_schema_fields('ap2_mandate.json#/$defs/merchant_authorization', 'ap2-mandates') }}

### Resposta de checkout do AP2

O objeto `ap2` incluído nas respostas de checkout.

{{ extension_schema_fields('ap2_mandate.json#/$defs/ap2_with_merchant_authorization', 'ap2-mandates') }}

### Mandato de checkout

{{ extension_schema_fields('ap2_mandate.json#/$defs/checkout_mandate', 'ap2-mandates') }}

### Solicitação completa de AP2

O objeto `ap2` incluído nas solicitações de checkout COMPLETE.

{{ extension_schema_fields('ap2_mandate.json#/$defs/ap2_with_checkout_mandate', 'ap2-mandates') }}

### Códigos de erro

{{ extension_schema_fields('ap2_mandate.json#/$defs/error_code', 'ap2-mandates') }}

| Código de erro | Descrição |
| :------------------------------------------ | :---------------------------------------------------------------- |
| `mandate_required` | AP2 foi negociado, mas falta `ap2.checkout_mandate` na solicitação. |
| `agent_missing_key` | O perfil da plataforma não possui uma entrada `keys` válida.                      |
| `mandate_invalid_signature` | A assinatura do mandato não pode ser verificada.                         |
| `mandate_expired` | O carimbo de data/hora do mandato `exp` passou.                           |
| `mandate_scope_mismatch` | O mandato está vinculado a uma verificação diferente.                     |
| `merchant_authorization_invalid` | A assinatura da autorização comercial não pôde ser verificada.       |
| `merchant_authorization_missing` | A resposta de checkout omite `ap2.merchant_authorization`.         |
