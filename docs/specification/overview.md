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

# Especificação Oficial do Protocolo de Comércio Brasileiro (BCP)

## Diretrizes abrangentes

As palavras-chave **DEVE**, **NÃO DEVE**, **OBRIGATÓRIO**, **DEVE**, **NÃO DEVE**,
**DEVERIA**, **NÃO DEVERIA**, **RECOMENDADO**, **PODE** e **OPCIONAL** neste
documento devem ser interpretados conforme descrito em
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html){ target="_blank" } e
[RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html){ target="_blank" }.

Notas do esquema:

- Formato de data: sempre especificado como
    [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339.html){ target="_blank" }
    salvo especificação em contrário
- Formato dos valores: Unidades menores (centavos)

## Descoberta, governança e negociação

O BCP separa a compatibilidade da versão do protocolo da negociação de capacidade.
O perfil do negócio em `/.well-known/bcp` descreve capacidades para
a versão do protocolo que ele declara. Empresas que suportam protocolos mais antigos
versões **DEVERIAM** publicar perfis específicos da versão e anunciá-los
através do campo `supported_versions` — um mapa da versão do protocolo até
URI de perfil, permitindo que as plataformas descubram os recursos exatos para um
versão específica do protocolo. Ciclo de vida da versão, incluindo quando descontinuar
ou remover versões mais antigas de `supported_versions`, é uma política comercial
decisão. O protocolo não prescreve um cronograma de descontinuação.
A negociação de capacidade segue uma arquitetura de seleção de servidor onde o
negócio (servidor) determina os recursos ativos do
intersecção das capacidades declaradas de ambas as partes. Tanto os negócios quanto
perfis de plataforma podem ser armazenados em cache por ambas as partes, permitindo eficiência
negociação de capacidade dentro do fluxo normal de solicitação/resposta entre
plataforma e negócios.

### Governança de Namespace

O BCP usa nomenclatura de domínio reverso para codificar a autoridade de governança diretamente em
identificadores de capacidade. Isto elimina a necessidade de um registro central.

#### Convenção de Nomenclatura

Todos os nomes de recursos e serviços **DEVEM** usar o formato:

```text
{reverse-domain}.{service}.{capability}
```

**Componentes:**

- `{reverse-domain}` - Identificador de autoridade derivado da propriedade do domínio
- `{service}` - Categoria de serviço/vertical (por exemplo, `shopping`, `common`)
- `{capability}` - O nome do recurso específico

**Exemplos:**

| Nome | Autoridade | Serviço | Capacidade |
| ----------------------------------- | ----------- | -------- | ---------------- |
| `br.dev.bcp.shopping.checkout` | bcp.dev.br | compras | finalização da compra |
| `br.dev.bcp.shopping.fulfillment` | bcp.dev.br | compras | cumprimento |
| `br.dev.bcp.common.identity_linking` | bcp.dev.br | comum | identidade_linking |
| `com.example.payments.installments` | example.com | pagamentos | parcelamento |

#### Vinculação de Autoridade

Os nomes de domínio reverso têm dois propósitos: **identificadores** seguros contra colisões (chaves
e referências) e **entidades** — capacidades, serviços e manipuladores
de pagamento — que declaram uma URL `schema` buscável que os descreve. A
vinculação de autoridade se aplica a todas as entidades com um `schema` remoto: a origem
do URL `schema` declarado **DEVE** corresponder à autoridade do namespace em seu nome.

Uma capacidade **DEVE** declarar um `schema`; serviços e manipuladores de pagamento declaram
aquele onde seu transporte ou manipulador o define. Cada entidade **PODE** também
declarar uma URL `spec` (documentação legível por humanos).

Esta vinculação garante **proveniência, não confiança**: uma vinculação válida prova apenas
que o nome de domínio reverso é controlado pela parte proprietária do
domínio correspondente — uma entidade não pode ser publicada em um namespace que
seu autor não controla. **Não** afirma que a entidade é confiável,
correta ou digna de apoio. Negociar, confiar ou implementar é
sempre uma decisão do cliente; esta vinculação apenas informa ao cliente *quem* está fazendo
a reivindicação. A proveniência é estabelecida a partir da propriedade do domínio e avaliada em
tempo de negociação.

A URL `spec` é documentação, não faz parte do caminho confiável pela máquina, portanto
sua origem **não** é vinculada à autoridade: **DEVE** ser `https`, mas **PODE** ser veiculada
de qualquer host (por exemplo, um subdomínio de documentos ou host de documentos de terceiros). Apenas
a URL `schema` carrega a vinculação de autoridade definida abaixo.

##### Algoritmo de derivação

A autoridade é derivada **do host da URL `schema`** — que nomeia diretamente o
proprietário do domínio, sem ambiguidade sobre onde o domínio termina — e é
validada como um prefixo de rótulo do nome da entidade. Para a URL `schema` de uma
entidade cujo nome é `name`, uma plataforma **DEVE** aplicar o seguinte:

1. Analisar a URL com um analisador de URL compatível (WHATWG). Ela **DEVE** ser
   analisada com sucesso, **DEVE** usar o esquema `https` e **NÃO DEVE** conter
   informações de usuário (um componente `user:pass@`). A correspondência de
   substring na URL bruta **NÃO É** permitida — por exemplo,
   `https://bcp.dev.br@evil.example/x.json` tem host `evil.example`, não
   `bcp.dev.br`.
2. O host **DEVE** ser um nome de domínio registrado com pelo menos dois rótulos.
   Hosts IP-literais (`https://203.0.113.10/...`) e hosts de rótulo único
   (`https://localhost/...`) são autoridades inválidas.
3. Pegue o nome do host da URL (o host sem porta), normalize-o (minúsculas;
   retirar um `.` à direita; domínios internacionalizados no formato A-label/punycode),
   e **inverta seus rótulos** para formar o `authority_prefix` (host `bcp.dev.br` →
   `br.dev.bcp`).
4. A vinculação é válida se e somente se `name` começar com `authority_prefix`
   seguido por um `.` (um ponto final literal). O limite do ponto final é
   necessário para que `com.example` (do host `example.com`) não possa satisfazer um
   namespace vizinho como `com.examplecorp.*`, que é um prefixo textual, mas não
   alinhado a rótulos; também garante um resto não vazio após o
   prefixo. Os rótulos restantes após o prefixo de autoridade são tratados como opacos por esta
   verificação; eles não são inspecionados ou divididos.

| Nome da capacidade | `schema` hospedeiro | `authority_prefix` | Resultado |
| ----------------------------------- | ------------------ | ------------------ | ---------- |
| `br.dev.bcp.shopping.checkout` | `bcp.dev.br` | `br.dev.bcp` | **aceitar** |
| `br.dev.bcp.shopping.checkout` | `shopping.bcp.dev.br` | `br.dev.bcp.shopping` | **aceitar** |
| `com.example.payments.installments` | `example.com` | `com.example` | **aceitar** |
| `com.example.pay` | `evil.example` | `example.evil` | **rejeitar** |
| `br.dev.bcp.shopping.checkout` | `evil.example` | `example.evil` | **rejeitar** |
| `com.examplecorp.pay` | `example.com` | `com.example` | **rejeitar** |
| `com.example.pay` | `cdn.example.com` | `com.example.cdn` | **rejeitar** |

O `schema` de uma entidade é servido a partir de um host cujos rótulos invertidos são um prefixo de
seu nome. Um host canônico de ápice (`example.com` para `com.example.*`) sempre
satisfaz isso; um subdomínio o satisfaz apenas quando seus rótulos estão alinhados com o
caminho do namespace (`shopping.bcp.dev.br` para `br.dev.bcp.shopping.*`). Subdomínios
não relacionados, como um CDN compartilhado, **não** o satisfazem – eles hospedam o esquema
canônico em uma origem alinhada ao nome.

A verificação utiliza diretamente o host da URL `schema` e não consulta a
[Lista de Sufixos Públicos](https://publicsuffix.org/), portanto trata um **sufixo
público** — um domínio sob o qual partes independentes podem registrar nomes, de
`co.uk` aos sufixos da seção privada da lista operados por serviços que permitem
que terceiros registrem subdomínios ou buckets (`github.io`, armazenamento de objetos,
plataformas de aplicativo) — como autoridade ordinária. Os co-inquilinos sob esse sufixo
satisfazem o mesmo prefixo, então declare entidades apenas sob um **domínio registrável**
(um sufixo público mais um rótulo) que você controla exclusivamente.

##### Aplicação

Uma plataforma **DEVE** validar cada URL `schema` declarado pela empresa antes de buscar
isso. Se a origem do URL não corresponder à autoridade de namespace da entidade (por
[Algoritmo de derivação](#algoritmo-de-derivacao)), a plataforma **NÃO DEVE** buscar
e **DEVE** rejeitar a entidade - tratada como não presente e nunca
ativado. Um URL `spec` **DEVE** ser um URL `https` válido. Uma plataforma **NÃO DEVE** seguir redirecionamentos (`3xx`) ao buscar um URL `schema`, consistente com buscas de perfil.

A plataforma busca e compõe esquemas declarados pelo negócio para validar cada
solicitação e resposta, portanto, a validação da ligação garante que cada esquema composto seja
proveniente da parte que possui o namespace da entidade. Uma empresa **DEVE**
aplicar a mesma verificação ao perfil da plataforma e excluir qualquer entidade cuja
a ligação falha.

A vinculação valida o nome do host declarado quanto à proveniência; **não** é um
controle de segurança de busca e não autoriza a desreferenciação. Buscando o `schema`
O URL — como qualquer URL obtido durante a descoberta — também está sujeito ao
requisitos de segurança de busca de URL do protocolo, que protegem o endereço *resolvido*
(não apenas o nome do host) contra falsificação de solicitação do lado do servidor para uso especial
ou endereços de metadados de nuvem e religação de DNS. A verificação do nome do host e o
a verificação de endereço resolvido é independente e ambas se aplicam.

#### Modelo de Governança

| Padrão de namespace | Autoridade | Governança |
| ----------------- | ------------ | ------------------- |
| `br.dev.bcp.*` | bcp.dev.br | Órgão de governo do BCP |
| `com.{vendor}.*` | {vendor}.com | Organização do fornecedor |
| `org.{org}.*` | {org}.org | Organização |

O namespace `br.dev.bcp.*` é reservado para capacidades sancionadas pelo
corpo governante do BCP. Os fornecedores **DEVEM** usar seu próprio namespace de domínio
reverso para capacidades personalizadas.

### Serviços

Um **serviço** define a superfície da API para uma indústria (compras, comum etc.).
Os serviços incluem operações, eventos e ligações de transporte definidas via
formatos padrão:

- **REST**: OpenAPI 3.x (formato JSON)
- **MCP**: OpenRPC (formato JSON)
- **A2A**: Especificação do cartão do agente
- **EP (incorporado)**: OpenRPC (formato JSON)

#### Definição de serviço

{{ extension_schema_fields('service.json#/$defs/platform_schema', 'overview') }}

As definições de transporte **DEVEM** ser finas: elas declaram nomes de métodos e referências
apenas esquemas básicos. Consulte [Requisitos](#requisitos) para obter detalhes.

#### Resolução de endpoint

O campo `endpoint` fornece a URL base para chamadas de API. Os caminhos OpenAPI são
anexado a este endpoint para formar o URL completo.

**Exemplo:**

<!-- ucp:example schema=service def=business_schema -->
```json
{
  "version": "{{ bcp_schema_version }}",
  "transport": "rest",
  "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/rest.openapi.json",
  "endpoint": "https://business.example.com/api/v2"
}
```

Com o caminho OpenAPI `/checkout-sessions`, a URL resolvida é:

```text
POST https://business.example.com/api/v2/checkout-sessions
```

**Regras:**

- `endpoint` **DEVE** ser uma URL válida com esquema (https)
- `endpoint` **NÃO DEVE** ter uma barra final
- Os caminhos OpenAPI são relativos e anexados diretamente ao endpoint
- A mesma resolução se aplica a endpoints MCP para chamadas JSON-RPC
- `endpoint` para transporte A2A refere-se ao URL do Cartão do Agente para o agente

### Capacidades

Uma **capacidade** é um recurso de um serviço. Ele declara o que
funcionalidade é suportada e onde encontrar documentação e esquemas.

#### Definição de Capacidade

{{ extension_schema_fields('capability.json#/$defs/platform_schema', 'capability-schema') }}

#### Extensões

Uma **extensão** é um módulo opcional que aumenta outro recurso.
As extensões usam o campo `extends` para declarar seu(s) pai(s):

<!-- ucp:example schema=profile def=business_schema target=$.ucp.capabilities -->
```json
{
  "br.dev.bcp.shopping.fulfillment": [
    {
      "version": "{{ bcp_schema_version }}",
      "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
      "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
      "extends": "br.dev.bcp.shopping.checkout"
    }
  ]
}
```

##### Extensões multipais

Extensões **PODEM** estender vários recursos pai usando uma matriz:

<!-- ucp:example schema=profile def=business_schema target=$.ucp.capabilities -->
```json
{
  "br.dev.bcp.shopping.discount": [
    {
      "version": "{{ bcp_schema_version }}",
      "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/discount",
      "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/discount.json",
      "extends": ["br.dev.bcp.shopping.checkout", "br.dev.bcp.shopping.cart"]
    }
  ]
}
```

Quando uma extensão declara vários pais:

- A extensão **PODE** definir campos diferentes para cada capacidade que estende
    (por exemplo, `loyalty_earned` para finalização da compra, `loyalty_preview` para carrinho)
- Consulte [Algoritmo de interseção](#algoritmo-de-intersecao) para regras de negociação

As extensões podem ser:

- **Oficial**: `br.dev.bcp.shopping.fulfillment` estende `br.dev.bcp.shopping.checkout`
- **Fornecedor**: `com.example.installments` estende `br.dev.bcp.shopping.checkout`

### Composição do esquema

As extensões podem adicionar novos campos e modificar estruturas compartilhadas (por exemplo, descontos
modificar `totals`, o cumprimento adiciona cumprimento a `totals.type`).

#### Requisitos

- Definições de transporte (OpenAPI/OpenRPC) **DEVEM** fazer referência a esquemas base
    apenas. Eles **NÃO DEVEM** enumerar campos ou definir formas de carga útil inline.
- As extensões **DEVEM** ser autodescritivas. Cada esquema de extensão **DEVE**
    declare os tipos que introduz e como modifica os tipos base usando `allOf`
    composição.
- As plataformas **DEVEM** resolver esquemas do lado do cliente, buscando e compondo
    esquemas básicos com esquemas de extensão ativos.

#### Padrão de esquema de extensão

Os esquemas de extensão definem tipos compostos usando `allOf`. A chave `$defs` **DEVE**
use o nome completo do recurso pai (formato de domínio reverso) para ativar
resolução de esquema determinística:

<!-- ucp:example skip reason="schema definition" -->
```json
{
  "$defs": {
    "discounts_object": { ... },
    "br.dev.bcp.shopping.checkout": {
      "title": "Checkout with Discount",
      "allOf": [
        {"$ref": "checkout.json"},
        {
          "type": "object",
          "properties": {
            "discounts": {
              "$ref": "#/$defs/discounts_object"
            }
          }
        }
      ]
    }
  }
}
```

**Requisitos:**

- Esquemas de extensão **DEVEM** ter uma entrada `$defs` para cada pai declarado em
    `extends`
- A chave `$defs` **DEVE** corresponder exatamente ao nome completo da capacidade do pai

Esta convenção garante:

- **Autodocumentação**: o esquema declara exatamente quais pais ele estende
- **Resolução determinística**: o valor `extends` é mapeado diretamente para a chave `$defs`
- **Verificável**: verificações em tempo de construção podem confirmar que cada entrada `extends` tem um
    chave `$defs` correspondente

##### Requisitos de versão

Esquemas de extensão **DEVEM** declarar um objeto `requires` (junto com
`name`, `title`, `description`) para indicar o protocolo e
versões de capacidade necessárias para operação correta:

<!-- ucp:example skip reason="schema definition" -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://acme.com/bcp/schemas/loyalty.json",
  "name": "com.acme.shopping.loyalty",
  "title": "Acme Loyalty Points",
  "requires": {
    "protocol": { "min": "2026-01-23" },
    "capabilities": {
      "br.dev.bcp.shopping.checkout": { "min": "2026-06-01" }
    }
  },
  "$defs": {
    "br.dev.bcp.shopping.checkout": { ... }
  }
}
```

O autor do esquema — e não o editor do perfil — declara os requisitos de
versão. O editor do perfil seleciona e anuncia versões de perfil compatíveis
em seu perfil.

Cada restrição é um objeto com um `min` obrigatório (inclusive) e
versão opcional `max` (inclusive). Quando `max` está ausente, há
sem limite superior:

<!-- ucp:example skip reason="schema definition" -->
```json
"requires": {
  "protocol": { "min": "2026-01-23", "max": "2026-09-01" },
  "capabilities": {
    "br.dev.bcp.shopping.checkout": { "min": "2026-06-01" }
  }
}
```

As chaves em `requires.capabilities` **DEVEM** ser um subconjunto das
chaves `$defs` da extensão. Se `requires` estiver presente, as plataformas e
as empresas **DEVEM** verificar se a versão do protocolo negociado e as
versões de capacidade satisfazem as restrições declaradas durante a resolução
do esquema. Extensões incompatíveis são excluídas do conjunto de recursos
ativo (consulte [Fluxo de resolução](#fluxo-de-resolucao)). Se
`requires` estiver ausente, a extensão é considerada compatível
com as versões declaradas pelo perfil.

#### Convenção de resolução de esquema

Para validar cargas, as implementações resolvem esquemas de extensão da seguinte forma:

1. Determine a capacidade raiz da operação (por exemplo, operações de checkout
    use `br.dev.bcp.shopping.checkout`)
2. Para cada extensão ativa, resolva e aplique seu `$defs[{root_capability}]`

**Exemplo:** uma resposta de finalização de compra inclui a extensão de desconto.

- Capacidade raiz: `br.dev.bcp.shopping.checkout`
- Esquema de extensão: `discount.json`
- Resolver: `discount.json#/$defs/br.dev.bcp.shopping.checkout`

#### Fluxo de Resolução

As plataformas **DEVEM** resolver esquemas seguindo esta sequência:

1. **Descoberta**: Obtenha o perfil comercial de `/.well-known/bcp`
2. **Negociação**: Interseção de recursos de computação (consulte
    [Algoritmo de interseção](#algoritmo-de-intersecao))
3. **Schema Fetch**: busca o esquema base e todos os esquemas de extensão ativos
4. **Compatibilidade de versões**: para cada esquema de extensão obtido,
    se `requires` estiver presente, verifique a versão do protocolo negociado
    e as versões de capacidade satisfazem as restrições declaradas. Excluir
    extensões incompatíveis e remover novamente extensões órfãs
    (etapas 3-4 do [Algoritmo de interseção](#algoritmo-de-intersecao))
5. **Compor**: Mesclar esquemas por meio de cadeias `allOf` com base em extensões ativas
6. **Validar**: Valide solicitações e respostas em relação ao esquema composto

### Estrutura do perfil

Os documentos de perfil são documentos de descoberta legíveis por máquina. As empresas publicam
seu perfil em `/.well-known/bcp`; plataformas publicam seu perfil no URI
anunciado em `BCP-Agent`.

Um documento de perfil é um objeto JSON com um membro `ucp` obrigatório. O `ucp`
membro contém metadados de protocolo: versão do protocolo, serviços, opcional
recursos e manipuladores de pagamento.

Para perfis de negócios e de plataforma, `ucp.version`, `ucp.services` e
`ucp.payment_handlers` são obrigatórios. O `services` e `payment_handlers`
registros **DEVEM** estar presentes mesmo quando vazios. `ucp.capabilities` é opcional
e **PODE** ser omitido, embora perfis comerciais úteis normalmente anunciem em
pelo menos uma capacidade.

Perfis **PODEM** incluir chaves JSON Web públicas usadas para mensagens HTTP
Assinaturas e webhooks assinados. Quando um perfil publica chaves de assinatura,
eles **DEVEM** aparecer no array `keys[]` de nível superior - o canônico
Campo de perfil BCP que todo verificador BCP lê. `keys[]` é um conjunto JWK
de acordo com [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517), então o
mesmo documento é simultaneamente um perfil BCP e um conjunto JWK válido -
que um signatário pode reutilizar como sua fonte de chave Web Bot Auth. Veja
[Padrões de implantação para interoperabilidade WBA](#padroes-de-implantacao-para-interoperabilidade-wba)
abaixo.

Adicionar, girar ou remover uma chave atualiza esse array único. Remoção
é o caso crítico de segurança: uma chave revogada ou comprometida não é
efetivamente revogada até que esteja ausente de `keys[]`.

O BCP define dois tipos de chaves bem conhecidos: **EC** (ECDSA P-256, P-384) e
**OKP** (EdDSA Ed25519); o tipo de chave, curva e algoritmo
os vocabulários são abertos e os verificadores ignoram teclas que não reconhecem.
Consulte [Assinaturas de mensagens](signatures.md) para formato de chave, algoritmos,
pesquisa e rotação.

#### Perfil da empresa

As empresas publicam seu perfil em `/.well-known/bcp`. Um exemplo:

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {
      "br.dev.bcp.shopping": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "rest",
          "endpoint": "https://business.example.com/bcp/v1",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/rest.openapi.json"
        },
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "mcp",
          "endpoint": "https://business.example.com/bcp/mcp",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/mcp.openrpc.json"
        },
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "a2a",
          "endpoint": "https://business.example.com/.well-known/agent-card.json"
        },
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "embedded",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/embedded.openrpc.json"
        }
      ]
    },
    "capabilities": {
      "br.dev.bcp.shopping.checkout": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/checkout",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/checkout.json"
        }
      ],
      "br.dev.bcp.shopping.fulfillment": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
          "extends": "br.dev.bcp.shopping.checkout"
        }
      ],
      "br.dev.bcp.shopping.discount": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/discount",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/discount.json",
          "extends": "br.dev.bcp.shopping.checkout"
        }
      ],
      "br.dev.bcp.common.identity_linking": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/identity-linking",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/common/identity_linking.json",
          "config": {
            "providers": {
              "com.example.idp": [
                { "type": "oauth2", "auth_url": "https://accounts.example.com/" }
              ]
            },
            "scopes": {
              "br.dev.bcp.shopping.order:read":   {},
              "br.dev.bcp.shopping.order:manage": {}
            }
          }
        }
      ]
    },
    "payment_handlers": {
      "com.example.processor_tokenizer": [
        {
          "id": "processor_tokenizer",
          "version": "{{ bcp_schema_version }}",
          "spec": "https://example.com/specs/payments/processor_tokenizer",
          "schema": "https://example.com/specs/payments/merchant_tokenizer.json",
          "available_instruments": [
            {
              "type": "card",
              "constraints": {
                "brands": ["visa", "mastercard", "amex"]
              }
            }
          ],
          "config": {
            "type": "CARD",
            "tokenization_specification": {
              "type": "PUSH",
              "parameters": {
                "token_retrieval_url": "https://api.psp.example.com/v1/tokens"
              }
            }
          }
        }
      ]
    }
  },
  "keys": [
    {
      "kid": "poqkLGiymh_W0uP6PZFw-dvez3QJT5SolqXBCW38r0U",
      "kty": "OKP",
      "crv": "Ed25519",
      "x": "JrQLj5P_89iXES9-vFgrIy29clF9CC_oPPsw3c5D0bs",
      "use": "sig",
      "alg": "EdDSA"
    },
    {
      "kid": "business_2025",
      "kty": "EC",
      "crv": "P-256",
      "x": "qIVYZVLCrPZHGHjP17CTW0_-D9Lfw0EkjqF7xB4FivA",
      "y": "Mc4nN9LTDOBhfoUeg8Ye9WedFRhnZXZJA12Qp0zZ6F0",
      "use": "sig",
      "alg": "ES256"
    }
  ]
}
```

O perfil da empresa anuncia os transportes disponíveis da empresa,
recursos, manipuladores de pagamento e chaves de verificação públicas. Isto
exemplo publica chaves de assinatura no `keys[]` canônico de nível superior
array (um conjunto JWK RFC 7517), então o mesmo documento também é um JWK válido
Definir — reutilizável como fonte de chave do Web Bot Auth. Cada verificador BCP lê
`keys[]`, se resolveu a chave via `BCP-Agent` ou via
`Signature-Agent`.

Um verificador de formato WBA lê `keys[]` deste perfil **somente quando o
O cabeçalho `Signature-Agent` seleciona-o** com `type=jwks_uri` (ou `type=cimd`)
apontando para o URL do perfil. O padrão `type=directory` (quando `type` é
omitido) em vez disso espera um documento de diretório *assinado* em
`/.well-known/http-message-signatures-directory`, não é um perfil estático, então
ele não lerá `keys[]` de um `/.well-known/bcp` estático. Veja
[Padrões de implantação para interoperabilidade WBA](#padroes-de-implantacao-para-interoperabilidade-wba).

Este exemplo usa duas chaves. Se uma implantação precisa de um ou dois depende
nos algoritmos que suas contrapartes aceitam – muitas precisam apenas de um; veja
[Algoritmos de assinatura](signatures.md#algoritmos-de-assinatura). As duas chaves
aqui:

- Uma chave **Ed25519** (OKP) para identidade de transporte HTTP, compatível com WBA.
  O `kid` é a impressão digital JWK SHA-256 de acordo com RFC 7638.
- Uma chave **ECDSA P-256** (EC) para assinatura de mandato AP2
  (`ap2.merchant_authorization`).

Uma empresa que não interage com AP2 ou WBA pode publicar um único
Chave ES256 em `keys[]` (a linha de base universal). Veja
[Descoberta de chave](#descoberta-de-chave) para pesquisa e resolução de chaves,
[Padrões de implantação para interoperabilidade WBA](#padroes-de-implantacao-para-interoperabilidade-wba)
para opções de hospedagem e [Assinaturas de mensagens](signatures.md) para
mecânica de assinatura.

As empresas que suportam versões de protocolo mais antigas **DEVEM** incluir um
Objeto `supported_versions` mapeando cada versão mais antiga para um
URI de perfil específico da versão. Consulte [Versão do protocolo](#versao-do-protocolo)
para obter detalhes.

#### Perfil da plataforma

Os perfis de plataforma são semelhantes e incluem chaves de assinatura para recursos
exigindo verificação criptográfica. Capacidades **PODEM** incluir um `config`
objeto para configurações específicas de recursos (por exemplo, URLs de retorno de chamada, sinalizadores de recursos). Um
exemplo:

<!-- ucp:example schema=profile def=platform_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {
      "br.dev.bcp.shopping": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/overview",
          "transport": "rest",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/services/shopping/rest.openapi.json",
          "endpoint": "https://platform.example.com/bcp/v1"
        }
      ]
    },
    "capabilities": {
      "br.dev.bcp.shopping.checkout": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/checkout",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/checkout.json"
        }
      ],
      "br.dev.bcp.shopping.fulfillment": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/fulfillment",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/fulfillment.json",
          "extends": "br.dev.bcp.shopping.checkout"
        }
      ],
      "br.dev.bcp.shopping.order": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/order",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/order.json",
          "config": {
            "webhook_url": "https://platform.example.com/webhooks/bcp/orders"
          }
        }
      ],
      "br.dev.bcp.common.identity_linking": [
        {
          "version": "{{ bcp_schema_version }}",
          "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/identity-linking",
          "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/common/identity_linking.json"
        }
      ]
    },
    "payment_handlers": {
      "com.google.pay": [
        {
          "id": "gpay_1234",
          "version": "2024-12-03",
          "spec": "https://developers.google.com/merchant/ucp/guides/gpay-payment-handler",
          "schema": "https://pay.google.com/gp/p/ucp/2026-01-11/schemas/gpay_config.json"
        }
      ],
      "dev.shopify.shop_pay": [
        {
          "id": "shop_pay_1234",
          "version": "{{ bcp_schema_version }}",
          "spec": "https://shopify.dev/ucp/shop-pay-handler",
          "schema": "https://shopify.dev/ucp/schemas/shop-pay-config.json",
          "available_instruments": [
            {"type": "shop_pay"}
          ]
        }
      ],
      "com.example.processor_tokenizer": [
        {
          "id": "processor_tokenizer",
          "version": "{{ bcp_schema_version }}",
          "spec": "https://example.com/specs/payments/processor_tokenizer-payment",
          "schema": "https://example.com/schemas/payments/delegate-payment.json",
          "available_instruments": [
            {"type": "card", "constraints": {"brands": ["visa", "mastercard"]}}
          ]
        }
      ]
    }
  },
  "keys": [
    {
      "kid": "platform_2025",
      "kty": "EC",
      "crv": "P-256",
      "x": "MKBCTNIcKUSDii11ySs3526iDZ8AiTo7Tu6KPAqv7D4",
      "y": "4Etl6SRW2YiLUrN5vfvVHuhp7x8PxltmWWlbbM4IFyM",
      "use": "sig",
      "alg": "ES256"
    }
  ]
}
```

### Anúncio da plataforma mediante solicitação

As plataformas **DEVEM** comunicar seu URI de perfil a cada solicitação para ativar
negociação de capacidade.

**Transporte HTTP:** Plataformas **DEVEM** usar sintaxe de campo estruturado de dicionário
([RFC 8941](https://datatracker.ietf.org/doc/html/rfc8941){ target="_blank" })
no cabeçalho do agente BCP:

```text
POST /checkout HTTP/1.1
BCP-Agent: profile="https://agent.example/profiles/shopping-agent.json"
Content-Type: application/json

{"line_items": [...]}
```

**Transporte MCP:** As plataformas **DEVEM** incluir um objeto `meta` contendo solicitação
metadados:

<!-- ucp:example schema=shopping/checkout op=create direction=request extract=$.params.arguments.checkout -->
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_checkout",
    "arguments": {
      "meta": {
        "ucp-agent": {
          "profile": "https://agent.example/profiles/shopping-agent.json"
        }
      },
      "checkout": {
        "line_items": [...]
      }
    }
  },
  "id": 1
}
```

### Protocolo de Negociação

#### Requisitos da plataforma

1. **Anúncio de perfil**: as plataformas **DEVEM** incluir seu URI de perfil em
    cada solicitação usando o mecanismo apropriado ao transporte.
2. **Descoberta**: as plataformas **PODEM** buscar o perfil comercial de
    `/.well-known/bcp` antes de iniciar solicitações. Se buscado, plataformas
    **DEVE** armazenar em cache o perfil de acordo com as diretivas de controle de cache HTTP.
3. **Validação de namespace**: antes da busca, as plataformas **DEVEM** validar
    a origem do URL `schema` de cada recurso corresponde à sua autoridade de namespace (consulte
    [Vinculação de Autoridade](#vinculacao-de-autoridade)) e **DEVE** rejeitar recursos
    que falham nesta ligação.
4. **Resolução de esquema**: as plataformas **DEVEM** buscar e compor esquemas para
    recursos negociados antes de fazer solicitações.

#### Requisitos de negócios

1. **Resolução de perfil**: Ao receber uma solicitação com perfil de plataforma
    URI, as empresas **DEVEM** buscar e validar o perfil da plataforma, a menos que
    já armazenado em cache. Porque as empresas negociam por nome de capacidade e atendem
    seus próprios esquemas, eles normalmente não desreferenciam os declarados pela plataforma
    URLs `schema`; eles **DEVEM** mesmo assim verificar a ligação do namespace (consulte
    [Vinculação de Autoridade](#vinculacao-de-autoridade)) como defesa em profundidade.
2. **Interseção de Capacidade**: As empresas **DEVEM** calcular a interseção de
    capacidades de plataforma e negócios.
3. **Validação de extensão**: extensões sem capacidade pai no
    interseção **DEVE** ser excluída.
4. **Requisitos de resposta**: As empresas **DEVEM** incluir o campo `ucp` em
    cada resposta contendo:
    - `version`: A versão do BCP utilizada para processar a solicitação
    - `capabilities`: Conjunto de capacidades ativas para esta resposta

#### Algoritmo de Interseção

O algoritmo de interseção de capacidades determina quais capacidades estão ativas
para uma sessão:

1. **Interseção de computação**: para cada capacidade de negócios, inclua-a no
    resultado se existir uma capacidade de plataforma com o mesmo `name`.

2. **Selecionar versão**: Para cada capacidade na interseção, calcule o
    conjunto de strings de versão presentes **tanto** no negócio quanto na plataforma
    matrizes. Se o conjunto não estiver vazio, selecione a versão **mais alta**
    (última data). Se o conjunto estiver vazio (sem versão mútua), **exclua** o
    capacidade da interseção.

3. **Remover extensões órfãs**: Remova qualquer recurso em que `extends` esteja
    definido, mas **nenhum** de seus recursos pai está na interseção.
    - Para extensões monoparentais (`extends: "string"`): o pai deve estar presente
    - Para extensões multipais (`extends: ["a", "b"]`): pelo menos um pai
        deve estar presente

4. **Repetir poda**: Continue a etapa 3 até que nenhum outro recurso seja removido
    (lida com cadeias de extensão transitivas).

O resultado é o conjunto de capacidades que ambas as partes apoiam mutuamente
versões compatíveis, com dependências de extensão satisfeitas.

#### Tratamento de erros

A negociação do BCP pode falhar de duas maneiras:

1. **Falha na descoberta**: a empresa não consegue buscar ou analisar os dados da plataforma
   perfil.

2. **Falha na negociação**: o perfil fornecido é válido, mas a capacidade
   a interseção está vazia ou as versões são incompatíveis.

As falhas de descoberta são erros de transporte – as entradas necessárias podem
não foram recuperados ou estavam malformados. Falhas nas negociações são negócios
resultados - o manipulador executado nas entradas fornecidas e relatado
o resultado na resposta do BCP:

- **Falha de descoberta ou versão** → erro de transporte com opcional `continue_url`
- **Falha na negociação de capacidade** → Resposta BCP com `continue_url` opcional

##### Códigos de erro

**Erros de negociação:**

| Código | Descrição | REST | MCP |
| --------------------------- | ---------------------------------------------------- | ---- | ------ |
| `invalid_profile_url` | O URL do perfil está malformado, ausente ou não pode ser resolvido | 400 | -32001 |
| `profile_unreachable` | URL resolvido, mas falha na busca (tempo limite, não 2xx) | 424 | -32001 |
| `profile_malformed` | O conteúdo buscado não é JSON válido ou viola o esquema | 422 | -32001 |
| `version_unsupported` | Versão do protocolo da plataforma não suportada | 422 | -32001 |
| `capabilities_incompatible` | Sem recursos compatíveis na interseção | 200 | resultado |

**Erros de assinatura:**

| Código | Descrição | REST | MCP |
| ---------------------- | ------------------------------------------------------ | ---- | ------ |
| `signature_missing` | Cabeçalho/campo de assinatura obrigatório não presente | 401 | -32000 |
| `signature_invalid` | Falha na verificação da assinatura | 401 | -32000 |
| `key_not_found` | ID da chave não encontrado no conjunto de chaves publicadas do signatário | 401 | -32000 |
| `digest_mismatch` | O resumo do corpo não corresponde ao cabeçalho `Content-Digest` | 400 | -32600 |
| `algorithm_unsupported`| Algoritmo de assinatura não suportado | 400 | -32600 |

Consulte [Assinaturas de mensagens](signatures.md) para obter detalhes de verificação de assinatura.

**Erros de protocolo:**

| http | Descrição | MCP |
| ---- | ---------------------------------------------------------- | ---------- |
| 401 | Autenticação necessária ou credenciais inválidas | -32000 |
| 403 | Permissões autenticadas, mas insuficientes | -32000 |
| 409 | Chave de idempotência reutilizada com carga útil diferente | -32000 |
| 429 | Muitos pedidos | -32000 |
| 500 | Erro inesperado do servidor | -32603 |
| 503 | Servidor temporariamente incapaz de lidar com solicitações | -32000 |

Para MCP sobre HTTP, o código de status HTTP é o sinal principal; o JSON-RPC
`error.code` fornece um sinal secundário. Ambos os transportes **DEVEM** incluir
Cabeçalho `Retry-After` (REST) ou `error.data.retry_after` (MCP) para 429 e 503
respostas.

O protocolo incorporado usa os mesmos códigos de erro JSON-RPC para peer-to-peer
comunicação entre o host e o contexto incorporado. Cenários específicos do servidor
(limitação de taxa, idempotência) não se aplicam ao transporte incorporado. Veja
[Protocolo incorporado - Tratamento de resposta](embedded-protocol.md#tratamento-de-respostas)
para a especificação completa de tratamento de erros.

##### O Campo `continue_url`

Quando a negociação BCP falha, `continue_url` fornece uma experiência web alternativa.
As empresas **DEVEM** fornecer o URL mais contextualmente relevante:

- Para operações de checkout: link para o carrinho ou página de checkout
- Para operações de catálogo: link para o produto ou resultados de pesquisa
- Como alternativa: link para a página inicial da vitrine

Isso permite uma degradação graciosa – os agentes podem redirecionar os compradores para concluir suas
tarefa através da interface web padrão.

##### Ligações de transporte

=== "REST"

    **Falha na descoberta (424):**

    ```http
    HTTP/1.1 424 Failed Dependency
    Content-Type: application/json

    {
      "code": "profile_unreachable",
      "content": "Unable to fetch agent profile: connection timeout",
      "continue_url": "https://merchant.com/cart"
    }
    ```

    **Versão não suportada (422):**

    ```http
    HTTP/1.1 422 Unprocessable Content
    Content-Type: application/json

    {
      "code": "version_unsupported",
      "content": "Protocol version 2026-01-12 is not supported. This business supports versions 2026-01-11 and 2026-01-23.",
      "continue_url": "https://merchant.com/cart"
    }
    ```

    **Capacidades incompatíveis (200):**

    ```http
    HTTP/1.1 200 OK
    Content-Type: application/json

    {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "status": "error",
        "capabilities": {}
      },
      "messages": [
        {
          "type": "error",
          "code": "capabilities_incompatible",
          "content": "No compatible capabilities in the intersection",
          "severity": "unrecoverable"
        }
      ],
      "continue_url": "https://merchant.com"
    }
    ```

    **Erro de protocolo – Limite de taxa (429):**

    ```http
    HTTP/1.1 429 Too Many Requests
    Retry-After: 60
    ```

    **Erro de protocolo – não autorizado (401):**

    ```http
    HTTP/1.1 401 Unauthorized
    WWW-Authenticate: Bearer realm="bcp"
    ```

    Erros de protocolo usam códigos de status e cabeçalhos HTTP padrão. Órgãos de resposta
    são opcionais.

=== "MCP"

    **Falha na descoberta (erro JSON-RPC):**

    <!-- ucp:example schema=transports/jsonrpc def=error_response -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "error": {
        "code": -32001,
        "message": "BCP discovery failed",
        "data": {
          "code": "profile_unreachable",
          "content": "Unable to fetch agent profile: connection timeout",
          "continue_url": "https://merchant.com/cart"
        }
      }
    }
    ```

    **Versão não suportada (erro JSON-RPC):**

    <!-- ucp:example schema=transports/jsonrpc def=error_response -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "error": {
        "code": -32001,
        "message": "Protocol version not supported",
        "data": {
          "code": "version_unsupported",
          "content": "Protocol version 2026-01-12 is not supported. This business supports versions 2026-01-11 and 2026-01-23.",
          "continue_url": "https://merchant.com/cart"
        }
      }
    }
    ```

    **Capacidades incompatíveis (resultado JSON-RPC):**

    <!-- ucp:example schema=common/types/error_response extract=$.result.structuredContent -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "result": {
        "structuredContent": {
          "ucp": {
            "version": "{{ bcp_schema_version }}",
            "status": "error"
          },
          "messages": [
            {
              "type": "error",
              "code": "capabilities_incompatible",
              "content": "No compatible capabilities in the intersection",
              "severity": "unrecoverable"
            }
          ],
          "continue_url": "https://merchant.com"
        },
        "content": [
          {"type": "text", "text": "{\"ucp\":{…},…}"}
        ]
      }
    }
    ```

    **Erro de protocolo — Limite de taxa (erro JSON-RPC):**

    <!-- ucp:example schema=transports/jsonrpc def=error_response -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "error": {
        "code": -32000,
        "message": "Rate limit exceeded",
        "data": {
          "retry_after": 60
        }
      }
    }
    ```

    **Erro de protocolo – não autorizado (erro JSON-RPC):**

    <!-- ucp:example schema=transports/jsonrpc def=error_response -->
    ```json
    {
      "jsonrpc": "2.0",
      "id": 1,
      "error": {
        "code": -32000,
        "message": "Unauthorized"
      }
    }
    ```

    Ao usar o transporte HTTP Streamable, os servidores **DEVEM** retornar o
    código de status HTTP correspondente (por exemplo, `429` para limite de taxa) ao lado
    o erro JSON-RPC. O código de status HTTP é o principal sinal para
    tipo de erro.

#### Declaração de capacidade nas respostas

O registro `capabilities` nas respostas indica capacidades ativas:

<!-- ucp:example schema=shopping/checkout op=read -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "capabilities": {
      "br.dev.bcp.shopping.checkout": [
        {"version": "{{ bcp_schema_version }}"}
      ],
      "br.dev.bcp.shopping.fulfillment": [
        {"version": "{{ bcp_schema_version }}"}
      ]
    },
    "payment_handlers": {
      "com.example.processor_tokenizer": [
        {"id": "processor_tokenizer", "version": "{{ bcp_schema_version }}", "available_instruments": [{"type": "card"}]}
      ]
    }
  },
  "id": "checkout_123",
  "status": "incomplete",
  "currency": "BRL",
  "line_items": [ ... ],
  "totals": [ ... ],
  "links": [ ... ]
}
```

#### Seleção de capacidade de resposta

As empresas **DEVEM** incluir em `ucp.capabilities` apenas os recursos que são:

1. Na interseção negociada para esta sessão, E
2. Relevante para o tipo de operação desta resposta

**Relevância da capacidade raiz:**

Uma capacidade raiz é relevante se corresponder ao tipo de operação:

- `create_checkout` / `update_checkout` / `complete_checkout` →
    `br.dev.bcp.shopping.checkout`
- `create_cart` / `update_cart` → `br.dev.bcp.shopping.cart`
- Encomendar webhooks → `br.dev.bcp.shopping.order`

**Relevância da extensão:**

Uma extensão é relevante se **qualquer** de seus valores `extends` corresponder a um valor relevante
capacidade raiz.

**Exemplos de seleção:**

| Tipo de resposta | Inclui | NÃO inclui |
| ------------- | ------------------------------- | ---------------------------- |
| Finalizar compra | check-out, desconto, atendimento | carrinho, pedido |
| Carrinho | carrinho, desconto | check-out, atendimento, pedido |
| Encomendar | encomendar | checkout, carrinho, desconto |

## Identidade e autenticação

Os perfis BCP têm um duplo propósito: declaram as **capacidades** de uma parte
para negociação (consulte [Estrutura do perfil](#estrutura-do-perfil)) e publique
**assinatura de chaves** para verificação de identidade — habilitando ambos os recursos
negociação e autenticação criptográfica a partir de um único documento.

As empresas publicam seu perfil em `/.well-known/bcp` como a descoberta
ponto de entrada – as plataformas o buscam para determinar o suporte do protocolo, localizar
endpoints e recursos de negociação. Plataformas anunciam seu perfil
URL por solicitação através do cabeçalho `BCP-Agent`, permitindo que as empresas
negociar capacidades e verificar a identidade. Este desenho permite
**integração sem permissão** — qualquer plataforma com um perfil detectável
pode interagir com qualquer empresa sem registro prévio.

**Interoperabilidade Web Bot Auth.** Signatários que optam por assinaturas em formato WBA
adicionalmente emitem um cabeçalho `Signature-Agent` anunciando suas chaves. Veja
[Algoritmo de resolução de identidade](#algoritmo-de-resolucao-de-identidade) para saber como
verificadores resolvem identidade e
[Assinaturas de mensagens — Interoperabilidade WBA](signatures.md#interoperabilidade-wba) para o
formato de assinatura.

### Mecanismos de autenticação

As empresas **DEVEM** autenticar plataformas para evitar falsificação de identidade e garantir
integridade da mensagem. O BCP é compatível com vários mecanismos de autenticação:

- **Chaves de API** — Segredos pré-compartilhados trocados fora da banda
- **OAuth 2.0** — Credenciais do cliente ou outros fluxos OAuth
- **mTLS** — TLS mútuo com certificados de cliente
- **Assinaturas de mensagens HTTP** — Assinaturas criptográficas por
  [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421) (ver
  [Assinaturas de mensagens](signatures.md) para especificações completas)

Assinaturas de mensagens HTTP permitem integração sem permissão – as empresas podem
verificar plataformas por meio de suas chaves públicas anunciadas sem negociar compartilhamento
segredos. Os demais mecanismos exigem troca prévia de credenciais e implicam
relacionamento pré-estabelecido.

Webhooks business-to-platform **DEVEM** ser assinados. Veja
[Assinaturas de mensagens - quando as assinaturas se aplicam](signatures.md#quando-as-assinaturas-sao-aplicadas).

#### Vinculação de identidade

Independentemente do mecanismo de autenticação, os verificadores **DEVEM** garantir a
a identidade autenticada é consistente com o cabeçalho `BCP-Agent`:

- **Assinaturas de mensagens HTTP** — O perfil do signatário (de `BCP-Agent`) é
    verificado por validação de assinatura; nenhuma verificação adicional necessária.
- **Chaves de API / OAuth / mTLS** — Os verificadores **DEVEM** confirmar o autenticado
    o principal está autorizado a agir em nome do perfil identificado em
    `BCP-Agent`. Rejeitar solicitações onde a identidade autenticada e reivindicada
    conflito de perfil.

### Descoberta de chave

Ambas as partes publicam chaves públicas no seu perfil BCP. Busca de plataformas
o perfil comercial em `/.well-known/bcp`; as empresas buscam o
perfil de plataforma do cabeçalho `BCP-Agent` (ou `Signature-Agent`
cabeçalho quando a interoperabilidade Web Bot Auth estiver em uso). O mesmo perfil que
fornece recursos também fornece chaves de verificação - este é o BCP
mecanismo de resolução chave para
[RFC 9421](https://www.rfc-editor.org/rfc/rfc9421) Mensagem HTTP
Assinaturas.

Consulte [Estrutura do perfil](#estrutura-do-perfil) para a publicação
contrato (o conjunto canônico `keys[]` JWK de nível superior). Ambas as resoluções
caminhos leem a mesma lista:

- **Resolvido via `BCP-Agent`** (pesquisa de chave BCP padrão) — leia `keys[]`.
- **Resolvido via `Signature-Agent`** (Web Bot Auth, opcional) — leia
  `keys[]`; as variantes `cimd`/`directory` chegam ao Conjunto JWK através
  seus próprios documentos.

Para o algoritmo de verificação completo – resolução de chave baseada em capacidade,
busca de perfil e aplicação de componentes cobertos - consulte
[Algoritmo de resolução de identidade](#algoritmo-de-resolucao-de-identidade) abaixo.
Para formato de chave (JWK), algoritmos suportados, procedimentos de rotação de chave,
e o formato de assinatura de interoperabilidade do Web Bot Auth, consulte
[Assinaturas de mensagens](signatures.md).

### Requisitos de perfil

#### Hospedagem

Ambos os perfis devem ser hospedados de forma confiável. Um não confiável ou mal configurado
O endpoint do perfil pode impedir que a outra parte processe solicitações.

1. Os perfis **DEVEM** ser veiculados por HTTPS.
2. Os endpoints do perfil **NÃO DEVEM** usar redirecionamentos (3xx).
3. As respostas do perfil **DEVEM** incluir um cabeçalho `Cache-Control` com
   `public` e `max-age` de pelo menos 60 segundos. Perfis **NÃO DEVEM**
   ser servidos com as diretivas `private`, `no-store` ou `no-cache`.

Os perfis representam a identidade e as capacidades estáveis de uma parte. Espera-se
que as URLs de perfil permaneçam consistentes em todas as solicitações e não contenham
configuração por transação ou por sessão — a política de cache acima
reforça isso exigindo suporte a cache compartilhado com um TTL mínimo.

#### Buscando

As empresas buscam perfis de plataforma para realizar negociação de capacidade e
verificar a identidade. O BCP define melhores práticas que permitem integração sem
permissão, mas as empresas mantêm controle total sobre suas políticas de acesso
e **PODEM** impor regras adicionais com base na confiança estabelecida, no
comportamento observado ou em requisitos operacionais.

As empresas **DEVEM** manter um registro de plataformas pré-aprovadas —
plataformas cujos perfis foram validados e cuja confiança é
estabelecido por meio de mecanismos fora de banda (chave de API, credencial OAuth,
certificado mTLS ou verificação prévia). Plataformas conhecidas podem ser atendidas
eficientemente com base na identidade e nos recursos armazenados em cache e não são
sujeito a restrições orçamentárias de descoberta.

Quando uma plataforma *não é reconhecida*, ela aciona uma descoberta de perfil
dinâmica. As empresas **DEVEM** estabelecer uma pegada de descoberta de valor
fixo para que o consumo de recursos para resolver
plataformas não reconhecidas permaneça constante, independentemente de quantas plataformas
solicitarem acesso. As estratégias incluem:

- **Cache de perfil de tamanho fixo** (por exemplo, LRU) — limita a memória independentemente de
  o número de URLs de perfil exclusivos encontrados
- **Limite de taxa global** em buscas de descoberta — limita a rede de saída
  sem exigir rastreamento de estado por origem
- **Recuo em falhas repetidas** — reduz tentativas para persistentemente
  endpoints de perfil indisponíveis ou maliciosos
- **Descoberta assíncrona** — adie a resolução do perfil respondendo
  com um código de status `503` e cabeçalho `Retry-After` e resolver o problema
  perfil em segundo plano; quando a plataforma tenta novamente, o validado
  o perfil é armazenado em cache e a negociação de capacidade prossegue de forma síncrona

Estas regras se aplicam a qualquer URL desreferenciado durante a resolução de identidade —
o perfil e qualquer documento `jwks_uri` ou CIMD, um verificador segue:

1. As implementações **DEVEM** rejeitar URLs não veiculados por HTTPS.
2. Implementações **NÃO DEVEM** seguir redirecionamentos (3xx).
3. As implementações **DEVEM** impor tempos limite de conexão e resposta.
4. Implementações **DEVEM** armazenar perfis em cache com um piso mínimo de TTL
   de 60 segundos, independente dos cabeçalhos `Cache-Control` da origem.
5. Implementações **PODEM** atualizar perfis de forma assíncrona usando
   semântica obsoleta enquanto revalidada.
6. Em caso de falha na verificação de assinatura com um `kid` desconhecido,
   implementações **DEVEM** forçar a atualização do perfil em cache uma vez -
   mas **NÃO DEVE** fazê-lo mais de uma vez por piso TTL por origem.
7. As implementações **DEVEM** rejeitar URLs que resolvem para IP de uso especial
   endereços ([RFC 6890](https://www.rfc-editor.org/rfc/rfc6890) -
   loopback, link-local incluindo o endereço de metadados da nuvem
   `169.254.169.254`, intervalos privados e outros intervalos reservados), exceto um
   alvo de loopback quando o próprio verificador é executado no mesmo loopback
   interface (desenvolvimento local). Os verificadores **DEVEM** validar o
   endereço resolvido, não apenas o nome do host (para resistir à religação do DNS),
   e **NÃO DEVE** desreferenciar um URL contido em um buscado
   documento (por exemplo, um CIMD `jwks_uri`) que resolve esse endereço.
8. As implementações **DEVEM** limitar o tamanho do corpo da resposta para evitar
   esgotamento de recursos de resposta ilimitada. Um perfil BCP é um
   manifesto de identidade/capacidade, não uma carga útil de dados (perfis documentados
   têm menos de 5 KiB); como o esquema não define limite de tamanho, esse limite é um
   guarda de implantação e verificadores **DEVEM** defini-lo no mínimo
   128 KiB para não rejeitar perfis compatíveis.

Se um perfil não puder ser obtido (tempo limite, falha de DNS, 5xx) ou falhar
validação (esquema inválido, chaves de assinatura, incompatibilidade de assinatura),
as empresas **DEVEM** rejeitar a solicitação com um erro apropriado e
código de status (consulte [Tratamento de erros](#tratamento-de-erros)).

### Padrões de implantação para interoperabilidade WBA

Um perfil BCP carregando uma matriz `keys[]` de nível superior é um RFC 7517 válido
Conjunto JWK, que um signatário pode opcionalmente reutilizar como sua chave Web Bot Auth
fonte. O parâmetro `type` do cabeçalho `type` seleciona
como um verificador resolve as chaves anunciadas. O parâmetro e
seus valores `jwks_uri`/`cimd`/`directory` são definidos no §4.1 do
[draft-meunier-webbotauth-httpsig-directory-00](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-httpsig-directory/00/).
Cada variante pode ser independente ou apontar para o perfil BCP:

- **`type=jwks_uri`** — o valor do membro é um URL de conjunto JWK, obtido
  diretamente. Aponte para o URL do perfil BCP e o `keys[]` do perfil
  serve como conjunto JWK: um documento é o perfil e a fonte da chave.
  A integridade deriva do TLS até a origem do perfil, sem chave por chave
  autoassinatura. Defina `type=jwks_uri` explicitamente: omitindo `type`
  o padrão é `directory` (abaixo), que espera um sinal assinado
  diretório, não um perfil estático.

  ```text
  Signature-Agent: sig1="https://platform.example/.well-known/bcp";type=jwks_uri
  ```

- **`type=cimd`** — o valor do membro é um documento de metadados de ID do cliente
  ([draft-ietf-oauth-client-id-metadata-document](https://datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/))
  cujo `jwks_uri` **PODE** apontar para o perfil BCP. Use quando um
  a contraparte consome a identidade do agente em formato CIMD.

  ```text
  Signature-Agent: sig1="https://platform.example/agent";type=cimd
  ```

- **`type=directory`** *(padrão)* — quando `type` é omitido ou definido como
  `directory`, o valor do membro é uma **origem** (não um URL completo): o
  verificador anexa o caminho conhecido registrado
  (`/.well-known/http-message-signatures-directory`) para essa origem e
  busca um diretório assinado lá. Seu formato, autoassinaturas por chave,
  e o tipo de mídia são definidos pelo rascunho do diretório §5.2.

  ```text
  Signature-Agent: sig1="https://platform.example"  # type omitted -> directory
  Signature-Agent: sig1="https://platform.example";type=directory  # explicit
  ```

### Algoritmo de resolução de identidade

O BCP e o Web Bot Auth definem dois mecanismos de resolução de chave. Qual deles
os usos do verificador são escolhidos pela **capacidade do verificador e pelos cabeçalhos
presente**, não pelo `tag` da assinatura — o `tag` é uma dica, não uma
portão. A pesquisa de chave BCP padrão (`BCP-Agent`) é suportada por todos os BCP
verificador e funciona para qualquer assinatura BCP; Pesquisa de chave de autenticação do Web Bot
(`Signature-Agent`) é uma camada aditiva opcional.

Uma solicitação PODE conter múltiplas assinaturas por
[RFC 9421 §4.3](https://www.rfc-editor.org/rfc/rfc9421#section-4.3).
Os verificadores tentam cada assinatura de forma independente; o pedido é
autenticado quando pelo menos uma assinatura é verificada. O algoritmo
abaixo processa uma única assinatura.

1. **Resolva a chave de assinatura.** Um verificador usa um mecanismo de resolução
   ele suporta cujo cabeçalho está presente:
    - **`BCP-Agent` — pesquisa de chave BCP padrão, suportada por cada BCP
      verificador.** Resolva a URL do perfil `BCP-Agent` e leia
      `keys[]`. Este caminho se aplica a assinaturas BCP que são
      não marcado (BCP padrão) ou carregue `tag="web-bot-auth"` (o
      formato de dupla audiência); o verificador os resolve via `BCP-Agent`,
      trata `signature-agent` como um componente coberto comum, e
      não precisa implementar a descoberta de chave do Web Bot Auth. (Verificando um
      assinatura de público duplo ainda requer suporte à chave
      algoritmo - qualquer que seja o signatário usado, por
      [Algoritmos de assinatura](signatures.md#algoritmos-de-assinatura) - e
      RFC 9421 §2.1.2 Seleção de componentes de membros do dicionário para cobrir
      `signature-agent;key="<label>"`.) Assinaturas com tags
      diferentes de `web-bot-auth` são ignorados, a menos que o BCP defina
      ou aceita explicitamente essa tag.
    - **`Signature-Agent` — Pesquisa de chave de autenticação do Web Bot, OPCIONAL
      (verificadores com reconhecimento de WBA).** Para uma assinatura com
      `tag="web-bot-auth"`, um verificador com reconhecimento de WBA **PODE** resolver
      por meio do membro `Signature-Agent`, analisado de acordo com o
      [Regras de análise do agente de assinatura](signatures.md#verificacao-de-solicitacao-rest).
      Tal assinatura **DEVE** satisfazer a assinatura do agente WBA
      requisitos em
      [rascunho-meunier-webbotauth-httpsig-protocol-00](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-httpsig-protocol/00/)
      §4.2 (consulte [Interoperabilidade WBA](signatures.md#interoperabilidade-wba) para o
      formato do lado do signatário). O valor do membro **DEVE** ser um URL HTTPS.
      Seu `type` seleciona resolução: `jwks_uri` e `cimd` atingem a
      chaves por meio do perfil do signatário e são resolvidas pelas etapas
      abaixo; o mecanismo `directory` é definido pelo rascunho do diretório
      (consulte [Padrões de implantação](#padroes-de-implantacao-para-interoperabilidade-wba)).
      O formato embutido do URI `data:` está fora do escopo da interoperabilidade BCP-WBA.
   **Ignore** esta assinatura se nenhum mecanismo compatível com o verificador puder
   resolva sua chave — o cabeçalho necessário está ausente, não há `Signature-Agent`
   membro corresponde ao rótulo de assinatura, o URL não é HTTPS ou o
   `tag` tem como escopo uma finalidade que este verificador não atende.
2. **Busque o documento** por [§Buscando](#buscando). Se a busca
   falha (erro de DNS, falha de rede, resposta não 2xx, falha de análise),
   **pular** esta assinatura.
3. **Localize a lista de chaves.** O `keys[]` de nível superior do perfil (RFC 7517
   Conjunto JWK) quando resolvido via `BCP-Agent` ou via `Signature-Agent`
   `type=jwks_uri`; para `type=cimd`, desreferenciar o documento
   `jwks_uri` para obter o Conjunto JWK. A integridade deriva do TLS para o
   origem resolvida.
4. **Corresponda o `keyid` da assinatura** a um `kid` na chave resolvida
   lista. Ao resolver, **pular chaves não utilizáveis para assinatura
   verificação**: qualquer chave marcada como `use:"enc"`, ou cujo `key_ops` seja
   presente, mas não inclui `"verify"`
   ([RFC 7517](https://www.rfc-editor.org/rfc/rfc7517) §4.2, §4.3). Chaves
   que definirem `use:"sig"` ou omitirem ambos os membros permanecem elegíveis. **Pular**
   esta assinatura se nenhuma chave elegível corresponder. Para assinaturas em formato WBA
   (`tag="web-bot-auth"`), o verificador **DEVE** também confirmar `keyid`
   é igual ao [RFC 7638](https://www.rfc-editor.org/rfc/rfc7638) SHA-256
   impressão digital do JWK correspondente - o rascunho da arquitetura WBA §4.2
   exige isso, vinculando a identidade da chave anunciada aos seus bytes. Se
   falhar, pule esta assinatura.
5. **Aplicar os requisitos dos componentes cobertos, em todos os regimes.**
   Independente de `tag` e transporte, a assinatura **DEVE** cobrir o
   alvo de solicitação (`@method`, `@authority`, `@path`; `@query` quando umstring de consulta está presente), o corpo quando presente (`content-digest`,
   `content-type`) e cada um desses cabeçalhos de solicitação quando presentes:
   `ucp-agent`, `signature-agent`, `idempotency-key` (um conjunto fechado - um
   cabeçalho adicionado ao BCP posteriormente é obrigatório apenas se sua definição
   seção diz isso). Se houver
   tal componente está ausente do conjunto coberto da assinatura, **skip**
   esta assinatura - um alvo, corpo ou cabeçalho que a assinatura não
   a capa é tratada como não assinada. Isto evita que uma assinatura satisfaça apenas
   Conjunto mínimo coberto do Web Bot Auth (`@authority`, `signature-agent`)
   de autenticar uma solicitação BCP cujo corpo, método ou caminho é
   não vinculado. (Se uma solicitação deve conter `Idempotency-Key` é uma questão
   regra de nível vinculativo, separada desta verificação de cobertura.)
6. **Verifique a assinatura** usando a chave correspondente. A assinatura
   O algoritmo é derivado do `kty`/`crv` do JWK. Se o verificador
   não suporta `kty`, `crv` ou `alg` da chave correspondente, **pular**
   esta assinatura; produz `algorithm_unsupported` se nenhum outro
   assinatura autentica a solicitação.

A solicitação **DEVE** ser rejeitada (`key_not_found`,
`algorithm_unsupported`, ou erro relacionado) somente quando cada assinatura
foi ignorado ou falhou na verificação.

**Identidade autenticada.** Quando uma assinatura é verificada, o
signatário autenticado é identificado pela URL que forneceu o
chave de verificação - o URL `Signature-Agent` para assinaturas em formato WBA,
o URL `BCP-Agent` para assinaturas BCP padrão.
Ambas as URLs podem estar presentes na mesma solicitação; a identidade anexada
à solicitação é determinado pela assinatura verificada, e não por
quais cabeçalhos foram enviados. Quando múltiplas assinaturas são verificadas, cada
identifica o signatário apenas como o URL que forneceu sua chave – uma chave
resolvido via `Signature-Agent` prova o controle dessa fonte de chave, não
do perfil `BCP-Agent` (cuja URL é apenas um valor de cabeçalho assinado).
As implementações **DEVEM** tratar a solicitação como uma única autenticação
identidade somente quando esses URLs forem iguais após a normalização;
caso contrário, são identidades distintas e a política decide se
qualquer um é suficiente.

Esta regra rege a **identidade de transporte HTTP**. Camada de carga útil
asserções (por exemplo, JWTs de mandato AP2 transportados no corpo da solicitação) têm
suas próprias regras de vinculação de identidade e resolução de chave; veja
[Mandatos AP2](ap2-mandates.md).

## Arquitetura de Pagamento

O BCP adota uma arquitetura dissociada de pagamentos para resolver o
problema de complexidade “N-to-N” entre **plataformas**, **empresas** e
**provedores de credenciais de pagamento**. Este design separa **Instrumentos
de Pagamento** (o que é aceito) de **Manipuladores de Pagamento** (as especificações
sobre como os instrumentos são processados), garantindo segurança e escalabilidade.

### Modelo de segurança e confiança

A arquitetura de pagamento é construída com base na filosofia “Trust-by-Design”. Ele assume
que, embora o provedor de credenciais comerciais e de pagamento tenha uma autoridade legal confiável
relacionamento, a plataforma (Cliente) atua como um intermediário que **NÃO DEVE**
toque em credenciais financeiras brutas.

#### O Triângulo da Confiança

1. **Empresa ↔ Provedor de credenciais de pagamento:** Um relacionamento jurídico e técnico pré-existente. A empresa possui chaves de API e um contrato com o provedor de credenciais de pagamento.
2. **Plataforma ↔ Provedor de credenciais de pagamento:** A plataforma interage com a interface do provedor de credenciais de pagamento (por exemplo, um iframe ou API) para tokenizar dados, mas não é o “proprietário” dos fundos.
3. **Plataforma ↔ Negócio:** A plataforma repassa o resultado (um token ou mandato) para a empresa finalizar o pedido.

#### Segurança aprimorada para comércio autônomo

Para cenários que exigem prova criptográfica de autorização do usuário (por exemplo,
agentes autônomos de IA), o BCP apoia a **Extensão de Mandatos AP2**
(`br.dev.bcp.shopping.ap2_mandate`). Esta extensão opcional fornece
autorização irrecusável por meio de credenciais digitais verificáveis.

Consulte [Integridade e não repúdio da transação](#integridade-e-nao-repudio-da-transacao)
e [Extensão de mandatos AP2](ap2-mandates.md) para obter detalhes sobre quando e como
use esta extensão.

#### Fluxo de credenciais e escopo PCI

Para minimizar a sobrecarga de conformidade (PCI-DSS):

1. **Fluxo Unidirecional:** Fluxo de credenciais **Plataforma → Negócios** apenas. As empresas **NÃO DEVEM** repetir credenciais nas respostas.
2. **Credenciais opacas:** As plataformas lidam com tokens (como tokens de rede), cargas criptografadas ou mandatos, e não PANs brutos.
3. **Roteamento de ID do manipulador:** O `handler_id` na carga útil garante que a empresa saiba exatamente qual chave do provedor de credenciais de pagamento usar para descriptografia/cobrança, evitando ataques de confusão de chaves.

### Funções e responsabilidades: quem implementa o quê?

Uma fonte comum de confusão é a divisão do trabalho. O modelo de pagamento BCP
divide as responsabilidades da seguinte forma:

| Função | Responsabilidade | Ação |
| :------------------------------ | :------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Provedor de credenciais de pagamento** | **Define a especificação** | Cria a **Definição do manipulador**. Eles publicam o "Blueprint" (esquemas JSON) que determina como tokenizar um cartão e quais entradas de configuração são necessárias.<br>*Exemplo: "Aqui está o esquema para o manipulador 'com.psp-x.tokenization'."* |
| **Negócios** | **Configura o manipulador** | Seleciona o manipulador que deseja usar e fornece sua **configuração** específica (chaves públicas, IDs de comerciante) na resposta de checkout do BCP. *Exemplo: "Aceito Visa usando 'com.psp-x.tokenization' com esta chave publicável."* |
| **Plataforma** | **Executa o Protocolo** | Lê a configuração do negócio e executa a lógica definida pelas especificações do provedor de credenciais de pagamento para adquirir um token. *Exemplo: "Vejo que a empresa usa um provedor de credenciais de pagamento. Chamarei o SDK do provedor com a chave da empresa para obter um token."* |

### Pagamento no ciclo de vida do checkout

Quando o pagamento é necessário, o processo de pagamento segue um ciclo de vida padrão de três etapas
dentro do BCP: **Negociação**, **Aquisição** e **Conclusão**.

![Diagrama de sequência de fluxo de pagamento de alto nível](site:specification/images/ucp-payment-flow.png)

1. **Negociação (Empresa → Plataforma):** A empresa anuncia os manipuladores de pagamento disponíveis em seu perfil BCP. Isso informa à plataforma *como* pagar (por exemplo, "Use este endpoint específico do provedor de credenciais de pagamento com esta chave pública").
2. **Aquisição (Plataforma ↔ Provedor de Credencial de Pagamento):** A plataforma executa a lógica do manipulador. Isso acontece no lado do cliente ou no lado do agente, diretamente com o provedor de credenciais de pagamento (por exemplo, troca de credenciais por um token de rede). A empresa não está envolvida, garantindo que os dados brutos nunca cheguem à API front-end da empresa.
3. **Conclusão (Plataforma → Negócio):** A plataforma envia a credencial opaca (token) para o negócio. A empresa o utiliza para capturar fundos por meio da integração de back-end com o provedor de credenciais de pagamento.

### Manipuladores de pagamento

Os manipuladores de pagamento são **especificações** (não entidades) que definem como o pagamento
instrumentos são processados. Eles são o contrato que une os três
participantes juntos.

**Distinção importante:**

- **Provedor de credenciais de pagamento** = O participante (entidade como Google Pay, Shop Pay)
- **Manipulador de pagamento** = A especificação criada pelo provedor (por exemplo, `com.google.pay`, `dev.shopify.shop_pay`)

Os manipuladores de pagamento permitem que uma variedade de instrumentos de pagamento e
tipos de token diferentes sejam suportados, incluindo tokens de rede. São definições
padronizadas normalmente de autoria de provedores de credenciais de pagamento ou do
corpo governante do BCP.

**Filtragem Dinâmica:** As empresas **DEVEM** filtrar a lista `handlers` com base em
o contexto do carrinho (por exemplo, removendo "Compre agora, pague depois" para assinatura
itens ou filtragem de métodos regionais com base no endereço de entrega).

**Resolução de instrumento disponível:** Dentro de cada manipulador ativo, tanto o
plataforma e a empresa anunciam de forma independente `available_instruments` - o
conjunto de tipos de instrumentos e restrições que cada parte suporta. O negócio é
responsável por resolvê-los em um valor oficial no checkout
resposta. A declaração da plataforma (do seu perfil) sinaliza o que ela pode
alça; o negócio cruza isso com sua própria declaração `business_schema`
e contexto do carrinho e retorna o resultado resolvido. As plataformas **DEVEM** tratar o
`available_instruments` na resposta como oficial para esse checkout. Veja
o [Guia do manipulador de pagamentos](payment-handler-guide.md#resolving-available_instruments)
para a semântica de resolução completa.

**Cardinalidade do instrumento:** Um envio de checkout **DEVE** conter exatamente um
instrumento de pagamento, a menos que a capacidade `br.dev.bcp.shopping.split_payments` seja
ativo. As empresas **DEVEM** rejeitar envios que violem esta restrição com
um erro `payment_failed` em `messages[]`. Veja
Pagamentos divididos (não incluídos nesta versão do BCP) para a extensão que flexibiliza esta
restrição.

### Cenários de implementação

Os cenários a seguir ilustram como diferentes manipuladores de pagamentos e
instrumentos são negociados e executados usando exemplos de dados concretos.
O **Pix é o método de pagamento padrão do BCP** e recebe o exemplo mais
detalhado abaixo; os demais métodos (carteiras digitais, tokenização de
cartão) seguem o mesmo modelo de manipuladores dissociados e aparecem de
forma resumida, com referência ao
[Guia do manipulador de pagamentos](payment-handler-guide.md) para o
contrato completo de cada um.

#### Cenário A: Pix (padrão)

Neste cenário — o caminho recomendado para a maioria dos checkouts BCP — a
empresa cria uma cobrança dinâmica Pix através do seu PSP beneficiário e a
devolve à plataforma para exibição. Ao contrário dos manipuladores de
cartão, a plataforma nunca troca credenciais diretamente com um provedor:
ela apenas seleciona o instrumento `pix` e exibe o QR Code ou o código
copia-e-cola que a empresa retorna. Veja
[Gerenciador de pagamentos Pix](pix-payment-handler.md) para o contrato
completo.

##### 1. Anúncio comercial (resposta de criar checkout)

<!-- ucp:example schema=shopping/checkout target=$.ucp -->
```json
{
  "version": "{{ bcp_schema_version }}",
  "payment_handlers": {
    "br.dev.bcp.pix": [
      {
        "id": "pix_recebedor_001",
        "version": "{{ bcp_schema_version }}",
        "available_instruments": [{ "type": "pix" }],
        "config": {
          "environment": "production"
        }
      }
    ]
  }
}
```

##### 2. Seleção do instrumento (solicitação de atualização de checkout)

A plataforma sinaliza que o comprador escolheu Pix. Nenhuma credencial é
enviada nesta etapa — a cobrança ainda não existe.

<!-- ucp:example schema=shopping/checkout op=update direction=request -->
```json
PUT /checkout-sessions/{id}

{
  "payment": {
    "instruments": [
      { "handler_id": "pix_recebedor_001", "type": "pix", "selected": true }
    ]
  }
}
```

##### 3. Cobrança gerada (resposta da empresa)

A empresa aciona seu PSP, recebe `provider_payment_id`, `copia_e_cola` e
`expires_at`, e devolve o instrumento Pix já preenchido para exibição.

<!-- ucp:example schema=shopping/checkout target=$.ucp -->
```json
{
  "payment": {
    "instruments": [
      {
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
          "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
          "expires_at": "2026-07-20T15:30:00-03:00"
        }
      }
    ]
  }
}
```

*A plataforma exibe o QR Code ou o código copia-e-cola até `expires_at`. A
confirmação de liquidação chega à empresa por webhook do PSP beneficiário; o
pedido avança assim que ela é validada — não é necessário reenviar
credenciais em uma chamada de conclusão de checkout separada.*

#### Outros métodos de pagamento

O mesmo modelo de manipuladores dissociados suporta outros instrumentos
quando a empresa optar por oferecê-los, sempre seguindo o fluxo de
negociação → aquisição → conclusão descrito acima para o Pix:

- **Carteiras digitais** (`com.google.pay`, `dev.shopify.shop_pay`, etc.): a
  plataforma troca a configuração anunciada pela credencial tokenizada
  diretamente com o provedor da carteira, e envia o token resultante na
  conclusão do checkout.
- **Tokenização direta de cartão**: um `payment_handler` genérico tokeniza o
  cartão do comprador; a empresa pode responder à conclusão pedindo um
  desafio adicional (SCA/3DS) via `continue_url` antes de aceitar o
  pagamento.

Para o contrato completo de declaração, `config` e resolução de
`available_instruments` de cada manipulador, veja o
[Guia do manipulador de pagamentos](payment-handler-guide.md).

#### Cenário C: Agente Autônomo (AP2)

Este cenário demonstra o **Fluxo recomendado para agentes**. Em vez de um
token de sessão, o agente gera mandatos criptográficos.

##### 1. Anúncio de negócios

<!-- ucp:example schema=shopping/checkout target=$.ucp -->
```json
{
  "version": "{{ bcp_schema_version }}",
  "payment_handlers": {
    "br.dev.bcp.ap2_mandate_compatible_handlers": [
        {
          "id": "ap2_234352",
          "version": "{{ bcp_schema_version }}",
          "spec": "https://example.com/specs/ap2-handler",
          "schema": "https://example.com/schemas/ap2-handler.json",
          "available_instruments": [
            {"type": "ap2_mandate"}
          ]
        }
      ]
  }
}
```

##### 2. Execução do Agente

O agente assina objetos criptograficamente usando a chave privada do usuário em um
superfície não-agente.

##### 3. Finalização completa da compra

<!-- ucp:example schema=shopping/checkout op=complete direction=request -->
```json
POST /checkout-sessions/{id}/complete

{
  "payment": {
    "instruments": [
      {
        "handler_id": "ap2_234352",
        // other required instruments fields
        "credential": {
          "type": "card",
          "token": "eyJhbGciOiJ..." // Token would contain payment_mandate, the signed proof of funds auth
        }
      }
    ]
  },
  "signals": {
    "br.dev.bcp.buyer_ip": "203.0.113.42",
    "com.example.risk_score": 0.95
  },
  "ap2": {
    "checkout_mandate": "eyJhbGciOiJ..." // Signed proof of checkout terms
  }
}
```

*Isso fornece à empresa uma prova irrefutável de que o usuário autorizou
esta transação específica, permitindo o processamento autônomo seguro. O
mandato AP2 é ortogonal ao instrumento escolhido — ele acrescenta prova
criptográfica de autorização por cima de qualquer manipulador, incluindo
Pix; o exemplo acima usa cartão apenas para ilustrar o formato genérico do
campo `credential`.*

### Gerenciamento de escopo PCI-DSS

#### Escopo da plataforma

A maioria das implementações de plataforma pode **evitar o escopo PCI-DSS**:

- Usando manipuladores que fornecem credenciais opacas (dados criptografados, token
    referências, etc.)
- Nunca acessar ou armazenar dados brutos de pagamento (números de cartão, CVV, etc.)
- Encaminhamento de credenciais sem a capacidade de usá-las diretamente
- Usando manipuladores de pagamento de tokenização PSP onde as credenciais brutas nunca passam
    através da plataforma

#### Escopo de Negócios

As empresas podem minimizar o escopo do PCI:

- Usando tokenização hospedada pelo provedor de credenciais de pagamento (lojas do provedor
    credenciais, a empresa recebe referência de token)
- Usando provedores de carteira que fornecem credenciais criptografadas (Google Pay, Shop
    Pay)
- Nunca registrando credenciais brutas
- Delegar processamento de credenciais a provedores de credenciais de pagamento certificados pelo PCI

#### Escopo do provedor de credenciais de pagamento

Provedores de credenciais de pagamento (PSPs, carteiras) são normalmente PCI-DSS Nível 1
certificado e manusear:

- Coleta de credenciais brutas
- Proteção de credenciais (tokenização, criptografia, armazenamento seguro)
- Validação e processamento de credenciais
- Infraestrutura compatível com PCI

### Melhores práticas de segurança

**Para empresas:**

1. Valide handler_id antes do processamento (certifique-se de que o manipulador esteja no conjunto anunciado)
2. Use credenciais PSP separadas para ambientes de TESTE versus PRODUÇÃO
3. Implementar idempotência para processamento de pagamentos (evitar cobranças duplas)
4. Registrar eventos de pagamento sem registrar credenciais
5. Defina tempos limite de credencial apropriados
6. Para cenários de comércio autônomo que exigem prova criptográfica, considere
    suportando a extensão `br.dev.bcp.shopping.ap2_mandate` (veja
    [Extensão de mandatos AP2](ap2-mandates.md))

**Para plataformas:**

1. Sempre use HTTPS para chamadas de API de checkout
2. Valide as configurações do manipulador antes de executar protocolos
3. Implementar tratamento de tempo limite para aquisição de credenciais
4. Limpe as credenciais da memória após o envio
5. Lide com a expiração de credenciais normalmente (adquira novamente, se necessário)
6. Para agentes autônomos, considere usar o `br.dev.bcp.shopping.ap2_mandate`
    extensão para prova criptográfica de autorização (ver
    [Extensão de mandatos AP2](ap2-mandates.md))

**Para provedores de credenciais de pagamento:**

1. Credenciais seguras para o negócio específico (criptografia, tokenização ou
    outros métodos específicos do manipulador)
2. Implementar limitação de taxa na aquisição de credenciais
3. Valide a autorização da plataforma antes de fornecer credenciais
4. Defina uma expiração de credencial razoável (por exemplo, 15 minutos para tokens, tempo
    cargas criptografadas limitadas)
5. Garantir que as credenciais não possam ser usadas diretamente pelas plataformas (apenas pelo
    negócio pretendido)

### Integração de prevenção de fraude

O BCP apoia a prevenção de fraudes através de [Sinais](#sinais) e da
arquitetura de pagamento:

- As plataformas fornecem ambiente de transação [sinais](#sinais) (IP, usuário
    agente) em solicitações de catálogo, carrinho e checkout
- As empresas podem exigir campos adicionais nas configurações do manipulador (por exemplo,
    Requisitos 3DS)
- Os provedores de credenciais de pagamento podem realizar avaliações de risco durante a credencial
    aquisição
- As empresas podem rejeitar transações de alto risco e solicitar
    verificação via feedback de sinal

### Extensões de arquitetura de pagamento

A arquitetura básica de pagamento descrita acima pode ser estendida para serviços especializados
casos de uso:

- **Extensão de mandatos AP2** (`br.dev.bcp.shopping.ap2_mandate`): Adiciona
    prova criptográfica de autorização do usuário para cenários de comércio autônomo
    onde são exigidas provas não repudiáveis. Veja
    [Extensão de mandatos AP2](ap2-mandates.md).

- **Tipos de manipulador personalizado**: os provedores de credenciais de pagamento podem definir
    manipuladores para apoiar novos instrumentos de pagamento. Veja
    [Guia do manipulador de pagamentos](payment-handler-guide.md) para obter detalhes.

O modelo de extensão garante que a arquitetura central permaneça simples enquanto
suportando requisitos avançados de segurança e conformidade quando necessário.

## Camada de Transporte

O BCP oferece suporte a vários protocolos de transporte. Plataformas e negócios
negociam efetivamente o transporte via `services` em seus perfis.

### Transporte REST (núcleo)

O BCP oferece suporte a **HTTP/1.1** (ou superior) usando padrões RESTful.

- **Tipo de conteúdo:** Solicitações e respostas **DEVEM** usar `application/json`.
- **Métodos:** Implementações **DEVEM** usar verbos HTTP padrão (por exemplo, `POST`
    para criação, `GET` para recuperação).
- **Códigos de status:** Implementações **DEVEM** usar códigos de status HTTP padrão
    (por exemplo, 200, 201, 400, 401, 500).

### Protocolo de Contexto do Modelo (MCP)

O BCP suporta **[protocolo MCP](https://modelcontextprotocol.io/specification/)**,
que opera em JSON-RPC.

#### Formato de solicitação

As solicitações MCP utilizam o método `tools/call` com o nome da operação em
`params.name` e carga útil BCP em `params.arguments`:

<!-- ucp:example schema=shopping/checkout op=create direction=request extract=$.params.arguments.checkout -->
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_checkout",
    "arguments": {
      "meta": {"ucp-agent": {"profile": "https://..."}},
      "checkout": {"line_items": [...]}
    }
  },
  "id": 1
}
```

#### Formato de resposta

As respostas da ferramenta MCP usam um padrão de saída dupla para compatibilidade com versões anteriores.
Servidores MCP do BCP:

- **DEVE** retornar a carga útil da resposta BCP em `structuredContent`
- **DEVE** declarar `outputSchema` nas definições da ferramenta, referenciando o
    Esquema JSON BCP apropriado para o recurso
- **DEVE** também retornar JSON serializado em `content[]` para retrocesso
    compatibilidade com clientes que não suportam `structuredContent`. Documentação
    exemplos abreviam essa string JSON serializada com `…` para facilitar a leitura.

<!-- ucp:example schema=shopping/checkout extract=$.result.structuredContent.ucp target=$.ucp -->
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "structuredContent": {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "payment_handlers": {},
        "capabilities": {...}
      },
      "id": "checkout_abc123",
      "status": "incomplete"
      // ... other checkout fields
    },
    "content": [
      {"type": "text", "text": "{\"ucp\":{…},…}"}
    ]
  }
}
```

### Protocolo Agente para Agente (A2A)

Uma empresa **PODE** expor um agente A2A que suporta BCP como uma extensão A2A,
permitindo integração com plataformas sobre tipos de dados BCP estruturados.

### Protocolo Incorporado (EP)

Uma empresa **PODE** incorporar uma interface em um host qualificado que
receber eventos conforme o usuário interage com a interface e delegar usuário-chave
ações.

A iniciação se dá por meio de um `continue_url` que é retornado pelo negócio.

## Capacidades padrão

O BCP define um conjunto de capacidades padrão:

| Nome da capacidade | ID (URI) | Descrição |
| :------------------- | :---------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------- |
| **Carrinho**            | [esquemas/shopping/cart.json](site:esquemas/shopping/cart.json) | Permite a construção da cesta antes que a intenção de compra seja estabelecida.                                               |
| **Finalização de compra** | [esquemas/shopping/checkout.json](site:esquemas/shopping/checkout.json) | Facilita a criação e gestão de sessões de checkout, incluindo gestão de carrinho e cálculo de impostos. |
| **Vinculação de identidade** | - | Permite que as plataformas obtenham autorização via OAuth 2.0 para executar ações em nome de um usuário.               |
| **Encomenda** | [esquemas/shopping/order.json](site:esquemas/shopping/order.json) | Permite que as empresas enviem atualizações assíncronas sobre o ciclo de vida de um pedido (envio, entrega, devoluções).     |

### Definição e extensões

Definições detalhadas para endpoints, esquemas e extensões válidas para cada
capacidade são fornecidas em seus respectivos arquivos de especificação. Extensões são
normalmente versionado e definido junto com seu recurso pai.

## Segurança

### Segurança de Transporte

Toda comunicação BCP **DEVE** ocorrer por **HTTPS**.

### Privacidade de dados

Dados confidenciais (como credenciais de pagamento ou PII) **DEVEM** ser tratados
de acordo com a LGPD e com diretrizes como PCI-DSS e GDPR, quando aplicáveis. O
BCP incentiva o uso de dados de pagamento tokenizados para minimizar a
responsabilidade comercial e da plataforma.

### Sinais

As empresas exigem dados ambientais para autorização, taxa
limitação e prevenção de abusos. Os valores do sinal **NÃO DEVEM** ser declarados pelo comprador
reivindicações - as plataformas fornecem sinais com base na observação direta (por exemplo,
IP de conexão, agente do usuário) ou retransmitindo informações verificáveis de forma independente
atestados de terceiros, como resultados assinados criptograficamente de um
verificador externo que a empresa pode validar em relação ao fornecedor
conjunto de chaves publicado.

Todas as chaves de sinal **DEVEM** usar nomenclatura de domínio reverso para garantir a procedência e
evitar colisões quando múltiplas extensões contribuem para o namespace compartilhado.
Sinais bem conhecidos usam o namespace `br.dev.bcp` (por exemplo, `br.dev.bcp.buyer_ip`);
sinais de extensão usam seu próprio namespace (por exemplo, `com.example.device_id`).

<!-- ucp:example schema=shopping/checkout op=create direction=request target=$.signals -->
```json
{
  "br.dev.bcp.buyer_ip": "203.0.113.42",
  "br.dev.bcp.user_agent": "Mozilla/5.0 ...",
  "com.example.attestation": {
    "provider_jwks": "https://example.com/.well-known/jwks.json",
    "kid": "example-key-2026-01",
    "payload": { "id": "att-7c3e9f", "pass": true, "...": "..." },
    "sig": "base64url..."
  }
}
```

Os campos de sinal podem conter informações de identificação pessoal
(PII). As plataformas **DEVEM** incluir apenas sinais relevantes para o atual
transação. As empresas **NÃO DEVEM** persistir os dados do sinal além do
necessidades operacionais da transação (por exemplo, finalização de pedido, revisão de fraude).

As empresas **PODEM** usar mensagens com o código `signal` para solicitar
dados. O campo `path` identifica o sinal solicitado; a mensagem `type`
determina a execução. Um `error` bloqueia a progressão do status até que o
o sinal é fornecido; um `info` é consultivo e não bloqueador.

<!-- ucp:example schema=shopping/checkout target=$.messages -->
```json
[
  {
    "type": "error",
    "code": "signal",
    "path": "$.signals['br.dev.bcp.buyer_ip']",
    "content": "Buyer IP is required to proceed.",
    "severity": "recoverable"
  },
  {
    "type": "info",
    "code": "signal",
    "path": "$.signals['br.dev.bcp.user_agent']",
    "content": "Providing user agent may improve checkout outcomes."
  }
]
```

### Atribuição

As plataformas encaminham os usuários para empresas por meio de vários canais — anúncios pagos,
recomendações orgânicas, links de influenciadores, agentes de IA. Em um navegador
fluxo, o contexto de referência (campanhas, identificadores de clique, origem/meio
marcadores) flui através de parâmetros de consulta de URL. O campo `attribution`
permite que as plataformas comuniquem os mesmos parâmetros às empresas.

O BCP **NÃO** prescreve modelos de atribuição, janelas ou atribuições
lógica. As plataformas usam suas convenções existentes (parâmetros de campanha GA4,
identificadores de clique como `gclid` / `fbclid` / `ttclid`, etc.); negócios
recebê-los e processá-los de acordo com suas próprias necessidades analíticas.

<!-- ucp:example schema=shopping/checkout op=create direction=request target=$.attribution -->
```json
{
  "campaign_id": "18234567890",
  "campaign_source": "google",
  "campaign_medium": "cpc",
  "campaign_name": "spring_2026",
  "gclid": "EAIaIQobChMI..."
}
```

A atribuição é informativa e opcionalmente fornecida pela plataforma.
As empresas não negociam nem anunciam apoio; a presença do campo ou
a ausência NÃO DEVE afetar a resposta ou negociação.

Os dados podem conter identificadores pseudônimos (IDs de clique, chaves de sessão)
tratados como dados pessoais sob as leis de proteção de dados aplicáveis. Plataformas
e as empresas são responsáveis pela conformidade em seus respectivos
jurisdições: as plataformas determinam o que emitir e divulgar; negócios
aplicar suas próprias políticas de tratamento, retenção e consentimento de dados. O
A extensão `buyer_consent` fornece um canal estruturado para os compradores
comunicar estado de consentimento.

A atribuição aparece no carrinho, na finalização da compra e nas solicitações de catálogo como
contexto de atribuição fornecido pela plataforma; no pedido, ele aparece como um
instantâneo emitido pela empresa da atribuição do checkout de origem.

### Integridade e não repúdio da transação

Para cenários que exigem prova criptográfica de autorização (por exemplo,
agentes, transações de alto valor), o BCP apoia a **Extensão de Mandatos AP2**
(`br.dev.bcp.shopping.ap2_mandate`). Quando esta extensão opcional for negociada:

- As empresas fornecem uma assinatura criptográfica nos termos de checkout
- As plataformas fornecem mandatos criptográficos que comprovam a autorização do usuário

Este mecanismo fornece garantias criptográficas fortes e completas sobre
detalhes da transação e consentimento do participante, reduzindo significativamente os riscos de
adulterações e disputas.

Consulte [Extensão de Mandatos AP2](ap2-mandates.md) para especificações completas,
guia de implementação e exemplos.

## Versionamento

### Formato da versão

O BCP usa versionamento baseado em data no formato `YYYY-MM-DD`. Isso fornece
ordem cronológica clara e comparação inequívoca de versões.

### Descoberta e negociação de versões

O BCP prioriza forte compatibilidade com versões anteriores. As empresas que implementam um
versão **DEVE** lidar com solicitações de plataformas que usam essa versão ou mais antiga.

Tanto empresas quanto plataformas declaram uma única versão em seus perfis:

#### Exemplo

=== "Perfil Empresarial"

    <!-- ucp:example schema=profile def=business_schema -->
    ```json
    {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "services": { ... },
        "capabilities": { ... },
        "payment_handlers": { ... }
      }
    }
    ```

=== "Perfil da plataforma"

    <!-- ucp:example schema=profile def=platform_schema -->
    ```json
    {
      "ucp": {
        "version": "{{ bcp_schema_version }}",
        "services": { ... },
        "capabilities": { ... },
        "payment_handlers": { ... }
      }
    }
    ```

### Negociação de versão

![Diagrama de sequência de fluxo de resolução de alto nível](site:specification/images/ucp-discovery-negotiation.png)

A compatibilidade de versão opera em dois níveis: a **versão do protocolo**
e **versões de capacidade**. A versão do protocolo (`ucp.version`)
rege os principais mecanismos do protocolo – descoberta, fluxo de negociação,
ligações de transporte e requisitos de assinatura. Versões de capacidade
regem a semântica de cada recurso de forma independente, conforme definido em
[Versionamento de componentes independentes](#versionamento-de-componentes-independentes).

#### Versão do Protocolo

O campo `version` declara a versão atual do protocolo do negócio.
O perfil em `/.well-known/bcp` descreve as capacidades, serviços,
e manipuladores de pagamento disponíveis nessa versão.

As empresas que suportam versões de protocolo mais antigas **DEVEM** declarar um
Objeto `supported_versions` mapeando cada versão mais antiga para um perfil
URI. Cada URI aponta para um perfil completo e independente para aquele
versão - incluindo seus próprios recursos, serviços, manipuladores de pagamento,
e assinatura de chaves. Quando `supported_versions` é omitido, somente
`version` é suportado.

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "2026-01-23",
    "supported_versions": {
      "2026-01-11": "https://business.example.com/.well-known/bcp/2026-01-11"
    },
    "services": {},
    "payment_handlers": {}
  }
}
```

##### Serviço inicial e descoberta de capacidade

As plataformas descobrem as capacidades de uma empresa através do seguinte fluxo:

1. Plataforma busca `/.well-known/bcp` — esta é a versão atual
    perfil.
2. Se a versão do protocolo da plataforma corresponder a `version`: utilize este
    perfil diretamente. Prossiga para a negociação de capacidade.
3. Se a versão do protocolo da plataforma for uma chave em
    `supported_versions`: busca o perfil na URI mapeada. Esse
    perfil descreve os recursos disponíveis nessa versão de
    protocolo. Prossiga para a negociação de capacidade.
4. Caso contrário: a empresa não suporta o protocolo da plataforma
    versão. Plataformas **NÃO DEVEM** enviar solicitações com conteúdo incompatível
    versão; as empresas **DEVEM** responder com um `version_unsupported`
    erro.

Perfis específicos de versão são documentos folha — eles descrevem exatamente
uma versão de protocolo e **NÃO DEVEM** conter um campo
`supported_versions`.

##### Validação no momento da solicitação

As empresas **DEVEM** validar a versão do protocolo da plataforma em
cada solicitação:

1. A plataforma declara a versão do protocolo que utiliza através do
    Campo `version` no perfil referenciado na solicitação.
2. Validações de negócios:
    - Se o `version` da plataforma corresponde ao `version` do negócio
        ou é uma chave em `supported_versions`: a solicitação **PODE**
        prossiga para a negociação de capacidade usando a correspondência
        versão do perfil comercial.
    - Caso contrário: a empresa **DEVE** retornar um `version_unsupported`
        erro.
3. Se a negociação de capacidade não produzir uma versão com suporte mútuo
    para uma capacidade exigida pela operação solicitada, o
    a empresa **DEVE** retornar um erro `capabilities_incompatible`
    (veja [Tratamento de erros](#tratamento-de-erros)).
4. As empresas **DEVEM** incluir a versão do protocolo negociado em
    cada resposta.

Resposta com confirmação de versão:

<!-- ucp:example schema=shopping/checkout extract=$.ucp target=$.ucp -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "capabilities": { ... },
    "payment_handlers": { ... }
  },
  "id": "checkout_123",
  "status": "incomplete"
  // ... other checkout fields
}
```

Erro de versão não suportada — nenhum recurso é criado:

<!-- ucp:example schema=common/types/error_response op=read -->
```json
{
  "ucp": { "version": "2026-01-11", "status": "error" },
  "messages": [{
    "type": "error",
    "code": "version_unsupported",
    "content": "Version 2026-01-12 is not supported. This business implements version 2026-01-11.",
    "severity": "unrecoverable"
  }],
  "continue_url": "https://merchant.com/"
}
```

##### Versões de pré-lançamento

A versão do protocolo **DEVE** ser uma versão datada no formato `YYYY-MM-DD`.
As empresas **NÃO DEVEM** anunciar uma string de versão sem data (por exemplo,
`"draft"`) no campo `version` do seu perfil ou em `supported_versions`.
Implementações de pré-lançamento não são estáveis e NÃO DEVEM ser divulgadas
através da descoberta pública - isso exporia o ecossistema geral
a comportamento indefinido e alterações incompatíveis sem aviso prévio.

Plataformas e empresas **PODEM** coordenar implementações de pré-lançamento fora de
descoberta pública. Tal uso não traz estabilidade ou compatibilidade
garantias - o comportamento subjacente pode mudar a qualquer momento sem
aviso prévio.

#### Versões de capacidade

As versões de capacidade são negociadas independentemente do protocolo
versão. Cada recurso no perfil é uma matriz. Múltiplas entradas
para a mesma capacidade, cada um com um `version` diferente, anuncie
suporte para múltiplas versões desse recurso. A capacidade
algoritmo de interseção considera apenas versões de capacidade suportadas
por ambas as partes.

As empresas **DEVEM** incluir apenas recursos compatíveis com a
versão do protocolo negociado em sua resposta. Uma capacidade que
depende de recursos introduzidos em uma versão mais recente do protocolo
**NÃO DEVE** ser incluída ao processar em uma versão de protocolo mais antiga.

### Compatibilidade com versões anteriores

#### Alterações compatíveis com versões anteriores

As seguintes alterações **PODEM** ser introduzidas sem uma nova versão:

- Adicionando novos campos não obrigatórios às respostas
- Adicionando novos parâmetros não obrigatórios às solicitações
- Adicionar novos endpoints, métodos ou operações a um transporte
- Adicionando novos códigos de erro com estruturas de erro existentes
- Adicionar novos valores a enums (a menos que explicitamente documentado como exaustivo)
- Alterando a ordem dos campos nas respostas
- Alterar o comprimento ou formato de strings opacas (IDs, tokens)

#### Mudanças importantes

As seguintes alterações **NÃO DEVEM** ser introduzidas sem uma nova versão:

- Remover ou renomear campos existentes
- Alteração de tipos de campo ou semântica
- Tornar campos não obrigatórios obrigatórios
- Removendo operações, métodos ou endpoints
- Alteração dos requisitos de autenticação ou autorização
- Modificar fluxo de protocolo existente ou máquina de estado
- Alterar o significado dos códigos de erro existentes

### Versionamento de componentes independentes

- As versões do protocolo evoluem independentemente das capacidades.
- Cada versão de capacidade é independente de outras capacidades.
- Os recursos **DEVEM** seguir as mesmas regras de compatibilidade com versões anteriores do
    protocolo.
- As empresas **DEVEM** validar a compatibilidade da versão do recurso usando o mesmo
    lógica como a descrita acima.
- Os transportes **PODEM** definir seus próprios mecanismos de manipulação de versão.

#### Capacidades BCP (`br.dev.bcp.*`)

Capacidades de autoria do BCP versionam junto com as versões de protocolo por padrão.
Capacidades individuais **PODEM** versionar de forma independente quando alterações
significativas são necessárias fora do ciclo de lançamento do protocolo.

#### Capacidades do fornecedor (`com.{vendor}.*`)

Capacidades fora do namespace `br.dev.bcp.*` versionam de forma totalmente independente.
Os fornecedores controlam seus próprios cronogramas de lançamento e estratégia de controle de versão.

## Glossário

Para definições de siglas e termos usados em toda a especificação BCP, consulte o [Glossário](glossary.md).
