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

# Extensão de consentimento do comprador

## Visão geral

A extensão Buyer Consent permite que as empresas comuniquem as opções de consentimento que desejam
oferecer, e permite que as plataformas transmitam as decisões de consentimento dos compradores para uso de dados e
preferências de comunicação - fins como marketing, análises, preferências e
venda ou compartilhamento de dados.

O consentimento é modelado como uma estrutura de dois níveis:

- **Objetivo** — para que serve o consentimento. Chaveado no nível superior por um
    identificador de DNS reverso (por exemplo, `br.dev.bcp.consent.marketing`). Cada propósito
    carrega um estado `granted`, um `source` identificando quem afirmou esse estado,
    um `description` legível por humanos e um `links` opcional.
- **Segment** — um refinamento opcional que define o escopo do propósito pai para um
    canal específico (por exemplo, e-mail, SMS), fornecedor (por exemplo, um provedor de medição),
    ou programa. Cada segmento tem o mesmo formato (`granted`, `source`,
    `description`, opcional `links`) e substitui a finalidade pai para seu
    escopo específico.

A estrutura está limitada a um nível de aninhamento: os propósitos possuem segmentos;
os segmentos não se aninham mais.

## Escopo

Esta extensão define o mecanismo pelo qual as empresas e plataformas estabelecem
e comunicam o estado de consentimento do comprador. Não dita o comportamento de nenhuma das partes
em resposta a esse estado - como uma empresa age em relação a isso (por exemplo, enviando e-mails,
compartilhamento de dados) e como uma plataforma apresenta decisões existentes ao comprador (por exemplo,
exibindo o estado atual da assinatura com uma capacidade de cancelamento de assinatura) são
regidos pela política comercial e pela regulamentação aplicável, não por esta
especificação.

As empresas são responsáveis por selecionar o valor inicial de `granted` de acordo
com a sua política aplicável antes de anunciar opções de consentimento. O valor
anunciado com `source: "business"` é o padrão oficial do negócio;
os compradores podem substituí-lo por meio da plataforma. O raciocínio político continua a ser
responsabilidade do negócio.

## Descoberta

As empresas anunciam suporte de consentimento em seus perfis. A capacidade pode se estender
a carrinho, checkout ou ambos:

<!-- ucp:example schema=profile def=business_schema extract=$.capabilities target=$.ucp.capabilities -->

```json
{
  "capabilities": {
    "br.dev.bcp.shopping.buyer_consent": [
      {
        "version": "{{ bcp_schema_version }}",
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/buyer-consent",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/buyer_consent.json",
        "extends": [
          "br.dev.bcp.shopping.cart",
          "br.dev.bcp.shopping.checkout"
        ]
      }
    ]
  }
}
```

## Composição do esquema

Quando esse recurso está ativo, o **objeto comprador** no carrinho e/ou checkout
carrega um campo `consent`:

- **Caminho do carrinho**: `cart.buyer.consent`
- **Caminho de checkout**: `checkout.buyer.consent`

O objeto `buyer` (e portanto `consent`) é opcional em todos os carrinhos e
operações de checkout — carrinho `create` / `update` e checkout `create` / `update`
/`complete`. As plataformas PODEM enviar consentimento capturado em `complete_checkout`
junto com o pagamento.

## Definição de esquema

### Objeto de consentimento

O BCP atualmente usa um objeto de consentimento compacto em `buyer.consent`.

{{ extension_schema_fields('buyer_consent.json#/$defs/consent', 'buyer-consent') }}

## Finalidades bem conhecidas

Esta extensão define quatro identificadores de finalidade bem conhecidos sob o
namespace `br.dev.bcp.consent.*`. As empresas podem definir finalidades adicionais sob
namespaces de DNS reverso que eles controlam. Esses identificadores são definições
operacionais, não taxonomias legais.

| Identificador | Finalidade |
| --------------------------------- | --------------------------------------------------------- |
| `br.dev.bcp.consent.analytics` | Análise e medição de desempenho |
| `br.dev.bcp.consent.marketing` | Comunicações de marketing |
| `br.dev.bcp.consent.preferences` | Lembrando as preferências do comprador |
| `br.dev.bcp.consent.sale_or_sharing` | Venda ou partilha de dados pessoais com terceiros |

## Segmentos bem conhecidos

Para a finalidade `br.dev.bcp.consent.marketing`, esta extensão define
identificadores de segmento de canal:

| Identificador | Canal |
| --------------------------------- | ------- |
| `br.dev.bcp.consent.marketing.email` | E-mail |
| `br.dev.bcp.consent.marketing.sms` | SMS |

## Anuncie e confirme

O mesmo formato de mapa carrega duas direções complementares de informação:

| Direção | Quem povoa | Campos preenchidos |
| ------------------------ | ------------- | ----------------------------------------------------------------------------------- |
| **Anuncie** (resposta) | Negócios | `granted`, `source`, `description`; `links` e `segments` quando presentes |
| **Confirmar** (solicitação) | Plataforma | `granted`, `source`; `segments` quando presente |

`description` e `links` são somente resposta; a plataforma não os ecoa ao
confirmar. `granted` e `source` são obrigatórios em ambas as direções: empresas
enviam o estado atual e sua origem ao anunciar; plataformas enviam o
estado atual e sua fonte ao confirmar.

O campo `source` carrega a autoria do valor atual de `granted`:

- `source: "business"` significa que o valor reflete a inadimplência do negócio; não
  a preferência do comprador se aplica.
- `source: "platform"` significa que o valor reflete a declaração do comprador
  preferência, capturada pela plataforma.

A fonte sinaliza como a plataforma deve tratar o valor atual:
`source: "business"` convida a plataforma a apresentar a escolha ao comprador
engajamento; `source: "platform"` indica uma preferência registrada do comprador.

### Exemplo: propósitos e segmentos

O caso mais simples é a captura de consentimento em nível de finalidade – `analytics` aqui mostra
o consentimento do comprador registrado no nível pai. As finalidades também podem transportar segmentos
para controle mais refinado: `marketing` está desativado, mas o comprador
consentiu com o marketing por SMS. O `granted: true` do segmento
substitui o `granted: false` do pai para esse escopo (valores mais específicos
ganham).

<!-- ucp:example schema=shopping/buyer_consent def=consent op=read extract=$.buyer.consent -->

```json
{
  "ucp": { ... },
  "id": "checkout_456",
  "status": "ready_for_complete",
  "currency": "BRL",
  "buyer": {
    "consent": {
      "br.dev.bcp.consent.analytics": {
        "granted": true,
        "source": "platform",
        "description": "Site analytics and performance measurement"
      },
      "br.dev.bcp.consent.marketing": {
        "granted": false,
        "source": "business",
        "description": "Promotional communications",
        "segments": {
          "br.dev.bcp.consent.marketing.email": {
            "granted": false,
            "source": "business",
            "description": "Promotional emails"
          },
          "br.dev.bcp.consent.marketing.sms": {
            "granted": true,
            "source": "platform",
            "description": "Marketing text messages"
          }
        }
      }
    }
  }
}
```

O comprador se envolveu com duas opções específicas (análise em geral, SMS
marketing especificamente); ambos carregam `source: "platform"`. Os demais
valores (segmento pai `marketing`, `email`) carregam `source: "business"`.

### Exemplo de anúncio

As empresas anunciam os propósitos e segmentos disponíveis com o estado de
consentimento atual (decisão prévia do comprador ou padrão do negócio):

<!-- ucp:example schema=shopping/buyer_consent def=consent op=read extract=$.buyer.consent -->

```json
{
  "ucp": { ... },
  "id": "checkout_456",
  "status": "ready_for_complete",
  "currency": "BRL",
  "buyer": {
    "consent": {
      "br.dev.bcp.consent.marketing": {
        "granted": false,
        "source": "business",
        "description": "Promotional communications across all channels",
        "links": [{ "type": "privacy_policy", "url": "https://example.com/privacy" }],
        "segments": {
          "br.dev.bcp.consent.marketing.email": {
            "granted": true,
            "source": "platform",
            "description": "Promotional emails and exclusive offers"
          },
          "br.dev.bcp.consent.marketing.sms": {
            "granted": false,
            "source": "business",
            "description": "Marketing text messages",
            "links": [{ "type": "terms_of_service", "url": "https://example.com/sms-terms" }]
          },
          "com.example.channel.marketing": {
            "granted": false,
            "source": "business",
            "description": "Marketing messages via a third-party channel"
          }
        }
      },
      "br.dev.bcp.consent.analytics": {
        "granted": true,
        "source": "business",
        "description": "Site analytics and performance measurement",
        "segments": {
          "com.example.analytics": {
            "granted": false,
            "source": "business",
            "description": "Third-party analytics measurement",
            "links": [{ "type": "privacy_policy", "url": "https://example.com/analytics-privacy" }]
          }
        }
      },
      "br.dev.bcp.consent.preferences": {
        "granted": true,
        "source": "business",
        "description": "Remember preferences and personalize the shopping experience"
      },
      "br.dev.bcp.consent.sale_or_sharing": {
        "granted": false,
        "source": "platform",
        "description": "Sale or sharing of personal data with third parties",
        "links": [{ "type": "privacy_policy", "url": "https://example.com/privacy" }]
      }
    }
  }
}
```

Neste exemplo, o comprador optou anteriormente por receber e-mail promocional
(`marketing.email` mostra `source: "platform"`) e anteriormente optou por não participar da
venda de dados (`sale_or_sharing` mostra `source: "platform"`). Qualquer outra escolha
permanece no padrão declarado pelo negócio e é candidata a ser exposta pela
plataforma para captura explícita.

### Exemplo de confirmação

As plataformas enviam o estado atual de cada finalidade e segmento anunciado em uma
solicitação `update_checkout` ou `complete_checkout` subsequente. Para cada escolha,
a plataforma ecoa os valores anunciados de `granted` e `source` quando nenhuma
preferência do comprador se aplica, ou define `source: "platform"` com o valor
`granted` declarado pelo comprador, quando o faz.

<!-- ucp:example schema=shopping/buyer_consent def=consent op=complete direction=request extract=$.buyer.consent -->

```json
{
  "buyer": {
    "consent": {
      "br.dev.bcp.consent.marketing": {
        "granted": true,
        "source": "platform",
        "segments": {
          "br.dev.bcp.consent.marketing.email": { "granted": true,  "source": "platform" },
          "br.dev.bcp.consent.marketing.sms":   { "granted": true,  "source": "platform" },
          "com.example.channel.marketing":   { "granted": false, "source": "business" }
        }
      },
      "br.dev.bcp.consent.analytics": {
        "granted": true,
        "source": "business",
        "segments": {
          "com.example.analytics": { "granted": false, "source": "business" }
        }
      },
      "br.dev.bcp.consent.preferences":     { "granted": true,  "source": "business" },
      "br.dev.bcp.consent.sale_or_sharing": { "granted": false, "source": "platform" }
    }
  }
}
```

Aqui, o comprador optou pelo marketing por e-mail e SMS; outras opções são
ecoadas em seus valores anunciados, incluindo `sale_or_sharing`, que mantém
uma escolha anterior capturada pela plataforma.

## Dependências de dados

Alguns estados de consentimento dependem de dados adicionais do comprador ou do checkout. Por exemplo,
o consentimento de marketing por SMS requer um número de telefone do comprador. Quando a
plataforma confirma um valor de consentimento cuja dependência necessária está faltando,
as empresas superam a lacuna por meio dos mecanismos padrão de [Ciclo de Vida do
Status do Checkout](checkout.md#ciclo-de-vida-do-status-do-checkout) e [Tratamento de
Erros](checkout.md#tratamento-de-erros).

Em `create_cart`, `update_cart`, `create_checkout` e `update_checkout`,
as empresas DEVEM revelar dependências ausentes como mensagens `warning` para que a
plataforma possa coletar os dados em uma operação subsequente. As decisões de
consentimento anunciadas permanecem válidas; o aviso é informativo.

<!-- ucp:example schema=shopping/checkout target=$.messages op=read -->

```json
[
  {
    "type": "warning",
    "code": "missing_consent_data",
    "content": "Phone number is required for SMS marketing.",
    "path": "$.buyer.phone_number"
  }
]
```

Em `complete_checkout`, as empresas NÃO DEVEM fazer a transição do checkout para
`completed` enquanto uma decisão de consentimento confirmada tiver dependências de dados não atendidas.
Dependências ausentes DEVEM ser descobertas por meio do fluxo padrão de
[Tratamento de Erros](checkout.md#tratamento-de-erros).

## Requisitos normativos

1. **Use as configurações anunciadas.** As empresas DEVEM anunciar o conteúdo completo
   conjunto de opções de consentimento que eles suportam. As plataformas decidem quais escolhas
   apresentar ao comprador e quando; ao apresentar uma escolha, as plataformas DEVEM
   usar o valor anunciado `description`, `links`, `granted` e
   agrupamento de finalidade/segmento. O campo `source` informa as decisões da plataforma
   (veja [Anuncie e confirme](#anuncie-e-confirme)) e não é
   conteúdo voltado para o usuário. Identificadores fora do namespace `br.dev.bcp.consent.*`
   são alças opacas; plataformas NÃO DEVEM inferir semântica de tais caminhos
   sozinho. Os identificadores definidos pelo BCP carregam a semântica estabelecida neste
   especificação.

2. **Confirme a semântica.** O campo `consent` é opcional nas solicitações;
   omiti-lo não fornece nenhuma atualização de consentimento e a empresa mantém seus dados anteriores
   posição. Ao enviar `consent`, as plataformas DEVEM incluir todos os anúncios
   chave de finalidade e de segmento, contendo `granted` e `source` para cada uma.
   A omissão de uma chave anunciada em um mapa `consent` NÃO DEVE ser
   usado para sinalizar qualquer valor.

3. **O conjunto anunciado é oficial.** As empresas DEVEM ignorar os propósitos e
   segmentos em uma solicitação que não foram anunciados em uma resposta anterior. Plataformas
   NÃO DEVE solicitar ou transmitir propósitos ou segmentos que a empresa não
   anunciar.

4. **Valores mais específicos ganham.** Para um segmento anunciado, o valor do segmento
   O valor `granted` substitui o `granted` da finalidade pai para esse segmento.

5. **A atribuição da fonte requer uma preferência declarada pelo comprador.** As plataformas DEVEM
   definir `source: "platform"` somente quando o valor de `granted` refletir o valor do comprador
   preferência declarada. Para escolhas às quais não se aplica nenhuma preferência do comprador,
   as plataformas DEVEM ecoar o `source` anunciado inalterado. O protocolo faz
   não prescrever o que conta como preferência declarada pelo comprador; essa determinação
   é feito pela plataforma de acordo com a política aplicável.

6. **Atribuição por empresa.** Uma decisão de consentimento capturada com um
   o negócio é atribuível apenas a esse negócio; plataformas NÃO DEVEM
   propagá-lo como base para `source: "platform"` em um negócio diferente
   pedido. Preferências mais amplas do comprador que não estão vinculadas a um negócio específico
   são independentes de decisões por negócio e podem ser aplicadas a cada
   escolhas anunciadas da empresa em sua própria base.

7. **Persistência e reversibilidade.** As plataformas PODEM persistir antes do comprador
   preferências (`source: "platform"`) em interações com o mesmo
   negócios e PODE suprimir a representação de valores inalterados. Onde
   as preferências persistem, as plataformas DEVEM dar ao comprador a capacidade
   para mudá-los.
