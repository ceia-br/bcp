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

# Assinaturas de mensagens

Esta especificação define como as mensagens BCP são assinadas criptograficamente para
garantir autenticidade e integridade.

## Visão geral

Esta especificação define como assinar e verificar mensagens BCP usando
[RFC 9421](https://www.rfc-editor.org/rfc/rfc9421) Assinaturas de mensagens HTTP.
Para o modelo de identidade do BCP, mecanismos de autenticação suportados e chaves
protocolo de descoberta, consulte
[Identidade e autenticação](overview.md#identidade-e-autenticacao).

As assinaturas de mensagens HTTP protegem contra:

* **Personificação** — Atacantes enviando mensagens alegando ser legítimas
    participantes
* **Adulteração** — Modificação do conteúdo da mensagem em trânsito
* **Ataques de repetição** — Mensagens capturadas são reenviadas para diferentes endpoints ou em
    tempos diferentes
* **Confusão de método/endpoint** — Cargas assinadas reproduzidas com diferentes
    Métodos HTTP ou para caminhos diferentes

### Arquitetura

BCP usa assinaturas de mensagens HTTP ([RFC 9421](https://www.rfc-editor.org/rfc/rfc9421))
para todos os transportes baseados em HTTP:

```text
+-----------------------------------------------------------------+
|                     SHARED FOUNDATION                           |
+-----------------------------------------------------------------+
|  Signature Format: RFC 9421 (HTTP Message Signatures)           |
|  Body Digest: RFC 9530 (Content-Digest, raw bytes)              |
|  Algorithms: must verify ES256 (baseline); other algorithms     |
|              optional — open vocabulary, counterparty-driven    |
|              (see Signature Algorithms)                         |
|  Key Format: JWK (RFC 7517 + RFC 8037 for Ed25519)              |
|  Key Discovery: keys[] (RFC 7517 JWK Set) in /.well-known/bcp   |
|  Replay Protection: idempotency-key (business layer)            |
+-----------------------------------------------------------------+
                              |
                              v
+-----------------------------------------------------------------+
|                     HTTP TRANSPORTS                             |
+-----------------------------------------------------------------+
|  REST API: Standard HTTP requests                               |
|  MCP: Streamable HTTP transport (JSON-RPC over HTTP)            |
+-----------------------------------------------------------------+
|  Headers:                                                       |
|    Signature-Input    (describes signed components)             |
|    Signature          (contains signature value)                |
|    Content-Digest     (body hash, raw bytes)                    |
+-----------------------------------------------------------------+
```

**Observação:** BCP especifica HTTP streamable para transporte MCP, substituindo o baseado em SSE
transportes. Isso permite que o mesmo mecanismo de assinatura RFC 9421 seja aplicado uniformemente
em todos os transportes BCP.

## Fundação Compartilhada

As seguintes primitivas criptográficas são compartilhadas em todos os transportes HTTP BCP.

### Algoritmos de Assinatura

O BCP reconhece duas famílias de algoritmos: ECDSA (sobre curvas P do NIST) e
EdDSA (Ed25519). ECDSA P-256 é a linha de base universal; EdDSA é um
opção aditiva que desbloqueia a interoperabilidade do Web Bot Auth (WBA).

| Família | JWK `kty` / `crv` | JWA `alg` | Hash |
| :----- | :---------------- | :-------- | :--- |
| ECDSA P-256 | `EC` / `P-256` | `ES256` | SHA-256 |
| ECDSA P-384 | `EC` / `P-384` | `ES384` | SHA-384 |
| EdDSA Ed25519 | `OKP` / `Ed25519` | `EdDSA` | (embutido) |

**Requisitos de implementação:**

* Todas as implementações **DEVEM** suportar a verificação de `ES256` (ECDSA P-256)
  assinaturas. Esta é a linha de base universal do BCP.
* O suporte para `ES384` (ECDSA P-384) é **OPCIONAL**.
* O suporte para `EdDSA` (Ed25519) é **OPCIONAL**. Um verificador com reconhecimento de WBA
  **DEVE** oferecer suporte aos algoritmos que seus signatários realmente usam (Ed25519 é
  o mais comum entre os signatários da WBA atualmente); BCP não impõe nenhum algoritmo
  requisito além da linha de base universal `ES256`.
* Os vocabulários `kty`/`crv`/`alg` são **abertos**. Um verificador que
  encontra uma chave cujo tipo, curva ou algoritmo não suporta
  **NÃO DEVE** rejeitar o conjunto de chaves publicado; a chave não suportada simplesmente
  permanece inutilizável para esse verificador. Uma assinatura que faça referência a tal
  chave falha com `algorithm_unsupported` (e, em uma solicitação de assinatura
  múltipla, é ignorada pelo [Algoritmo de Resolução de
  Identidade](overview.md#algoritmo-de-resolucao-de-identidade)).

**Orientação de uso:**

* **A escolha do algoritmo é orientada pela contraparte.** Um signatário **DEVE** usar um
  algoritmo aceito por cada verificador que a mesma assinatura deve satisfazer -
  o verificador BCP receptor, além de qualquer verificador WBA ou camada AP2 em que
  essa assinatura opte por entrar. Uma chave é suficiente quando um único algoritmo
  satisfaz todos eles; publicar múltiplas chaves de diferentes algoritmos
  (selecionadas por assinatura via `kid`) somente quando nenhum algoritmo o faz.
* **O padrão é `ES256`** sem uma restrição específica da contraparte — é
  a linha de base universal do BCP e também um algoritmo Web Bot Auth válido.
  (As regras de algoritmo do WBA e o cenário de implantação atual estão em
  [Interoperabilidade WBA](#interoperabilidade-wba).)
* **A assinatura do mandato AP2 segue a regra do próprio algoritmo do AP2** — consulte
  [Mandatos AP2](ap2-mandates.md).
* O algoritmo é derivado do campo `kty`/`crv` da chave no JWK;
  `alg` **NÃO** está incluído nos parâmetros `Signature-Input`.

**Número de chaves de assinatura.** Quantas chaves uma parte publica depende da
compatibilidade de algoritmo, não de uma regra do BCP. Uma chave é suficiente quando um único
algoritmo é aceito por todos os públicos para os quais ela assina; chaves separadas
(selecionadas por `kid`) são necessárias apenas quando o público impõe
restrições de algoritmo - por exemplo, um verificador WBA que aceita apenas
Ed25519, juntamente com um requisito de algoritmo do mandato AP2 que o exclui
(consulte [Mandatos AP2](ap2-mandates.md)). Quando um único algoritmo satisfaz
cada público, uma única chave atende a todos eles. Veja
[Perfil da empresa](overview.md#perfil-da-empresa) para ver um exemplo de duas chaves.

Para obter detalhes de codificação de assinatura on-the-wire, consulte
[Assinatura de solicitação REST - codificação de assinatura](#assinatura-de-solicitacao-rest).

### Formato de chave (JWK)

As chaves públicas **DEVEM** ser representadas usando o formato **JSON Web Key (JWK)** como
definido em [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517).
O BCP define dois formatos JWK bem conhecidos: **EC** (de acordo com RFC 7518 §6.2) para ECDSA
chaves e **OKP** (conforme [RFC 8037](https://datatracker.ietf.org/doc/html/rfc8037))
para chaves EdDSA. O vocabulário JWK é aberto (ver [Assinatura
Algoritmos](#algoritmos-de-assinatura)): perfis PODEM publicar chaves de outros
tipos e os verificadores ignoram aqueles que não podem usar.

**Estrutura Chave CE (ECDSA P-256, P-384):**

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :----- | :------- | :--------------------------------------- |
| `kid` | string | Sim | ID da chave (referenciada nas assinaturas) |
| `kty` | string | Sim | Tipo de chave (`EC`) |
| `crv` | string | Sim | Nome da curva (`P-256` ou `P-384`) |
| `x` | string | Sim | Coordenada X (codificada em base64url) |
| `y` | string | Sim | Coordenada Y (codificada em base64url) |
| `use` | string | Não | Utilização de chave (`sig` para assinatura) |
| `alg` | string | Não | Algoritmo (`ES256`, `ES384`) |

**Estrutura chave OKP (EdDSA Ed25519):**

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :----- | :------- | :---------------------------------------------------------------- |
| `kid` | string | Sim | ID da chave (referenciada nas assinaturas) |
| `kty` | string | Sim | Tipo de chave (`OKP`) |
| `crv` | string | Sim | Nome da curva (`Ed25519`) |
| `x` | string | Sim | Valor da chave pública (base64url codificado de acordo com RFC 8037 §2) |
| `use` | string | Não | Utilização de chave (`sig` para assinatura) |
| `alg` | string | Não | Algoritmo (`EdDSA`) |

**Exemplo CE (ES256):**

<!-- ucp:example schema=profile extract=$ target=$.keys[0] -->
```json
{
  "kid": "key-2024-01-15",
  "kty": "EC",
  "crv": "P-256",
  "x": "WKn-ZIGevcwGIyyrzFoZNBdaq9_TsqzGl96oc0CWuis",
  "y": "y77t-RvAHRKTsSGdIYUfweuOvwrvDD-Q3Hv5J0fSKbE",
  "use": "sig",
  "alg": "ES256"
}
```

**Exemplo OKP (Ed25519/EdDSA):**

<!-- ucp:example schema=profile extract=$ target=$.keys[0] -->
```json
{
  "kid": "poqkLGiymh_W0uP6PZFw-dvez3QJT5SolqXBCW38r0U",
  "kty": "OKP",
  "crv": "Ed25519",
  "x": "JrQLj5P_89iXES9-vFgrIy29clF9CC_oPPsw3c5D0bs",
  "use": "sig",
  "alg": "EdDSA"
}
```

Uma chave usada para assinaturas de **audiência dupla** (aquelas que carregam
`tag="web-bot-auth"`) **DEVE** publicar seu `kid` como o JWK SHA-256 da chave
Impressão digital ([RFC 7638](https://www.rfc-editor.org/rfc/rfc7638)) em cada
array que o lista. O `keyid` da assinatura em formato WBA é aquela impressão digital,
e um verificador BCP resolve a chave combinando `keyid` com um publicado
`kid`; definir ambos para a impressão digital permite que `BCP-Agent` e
As pesquisas `Signature-Agent` encontram a mesma chave. Para outras chaves `kid` é um
identificador opaco (RFC 7517) e PODE ser qualquer valor estável.

### Descoberta de chave

As chaves públicas são publicadas no perfil BCP do signatário. Veja
[Estrutura do perfil](overview.md#estrutura-do-perfil) para o contrato de
publicação, e [Descoberta de chave](overview.md#descoberta-de-chave) para a regra
de pesquisa do verificador (qual lista de chaves ler para cada mecanismo de
resolução).

### Rotação de chaves

Para girar chaves sem interrupção do serviço:

1. **Adicionar nova chave** — Publique a nova chave no `keys[]` do perfil
   junto com as chaves existentes
2. **Comece a assinar** — Comece a assinar com a nova chave
3. **Período de carência** — Continue aceitando assinaturas de chaves antigas (mínimo 7 dias)
4. **Remover chave antiga** — Remova a chave antiga de `keys[]`. Uma chave ainda
   listado em `keys[]` continua a verificar.

**Recomendações:**

* Os operadores DEVEM alternar as chaves a cada 90 dias.
* Os perfis DEVEM suportar múltiplas chaves ativas durante as transições.

**Resposta de comprometimento principal:**

1. Remova imediatamente a chave comprometida de `keys[]`; continua
   para verificar até estar ausente da matriz
2. Adicione nova chave com `kid` diferente
3. Rejeite todas as assinaturas feitas com chave comprometida

### Interoperabilidade WBA

Um integrador BCP PODE optar por sua assinatura primária em um Web Bot Auth-
formato compatível: uma única assinatura de **audiência dupla** – uma chave, uma
operação de assinatura, uma assinatura na transmissão - que tanto um verificador BCP
(resolvendo via `BCP-Agent`) e um verificador WBA (resolvendo via
`Signature-Agent`) aceitar. Este é o caminho RECOMENDADO para integradores
querendo interoperabilidade com verificadores em conformidade com WBA; os requisitos abaixo
aplicam-se a qualquer assinatura que contenha `tag="web-bot-auth"`. A interoperabilidade WBA é
escopo da solicitação: as respostas são assinadas com assinaturas BCP padrão
(cobrindo `@status`) e não carregue `tag="web-bot-auth"`.

**Na transmissão.** Uma assinatura de público duplo é uma assinatura BCP normal com
algumas adições: ele carrega um cabeçalho `Signature-Agent` **ao lado**
`BCP-Agent` (aditivo — `Signature-Agent` não substitui `BCP-Agent`),
assina o componente `signature-agent`, usa a chave de assinatura RFC 7638
impressão digital como `keyid` e adiciona `created`, `expires` e
`tag="web-bot-auth"`:

<!-- ucp:example schema=shopping/checkout op=create direction=request -->
```json
POST /checkout-sessions HTTP/1.1
Host: merchant.example.com
Content-Type: application/json
BCP-Agent: profile="https://platform.example/.well-known/bcp"
Signature-Agent: sig1="https://platform.example/.well-known/bcp";type=jwks_uri
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Digest: sha-256=:X48E9q...:
Signature-Input: sig1=("@method" "@authority" "@path" "signature-agent";key="sig1" "ucp-agent" "idempotency-key" "content-digest" "content-type");keyid="poqkLGiymh_W0uP6PZFw-dvez3QJT5SolqXBCW38r0U";created=1738617600;expires=1738621200;tag="web-bot-auth"
Signature: sig1=:base64_ed25519_signature_value:

{
  "line_items": [
    {
      "item": {"id": "item_123"},
      "quantity": 2
    }
  ]
}
```

Uma assinatura na transmissão, duas audiências. Os verificadores de formato BCP resolvem via
`BCP-Agent`, encontram seus componentes esperados (`ucp-agent`,
`idempotency-key`) e ignoram o resto; os verificadores de formato WBA resolvem via
`Signature-Agent` e encontram os deles (`@authority`, `signature-agent`,
`tag`, `created`/`expires`). Ambos verificam os mesmos bytes em relação à mesma
chave. Aqui, ambos os cabeçalhos apontam para a mesma URL `/.well-known/bcp`
(`type=jwks_uri`, então os verificadores WBA leem o `keys[]` do perfil como o
conjunto de JWK (JWK Set) — veja
[Padrões de implantação](overview.md#padroes-de-implantacao-para-interoperabilidade-wba)),
mas `Signature-Agent` PODE apontar para outro lugar.

Os três rótulos `sig1` estão unidos — a chave de membro do dicionário
`Signature-Agent`, o parâmetro `;key="sig1"` no componente assinado
`signature-agent` e o rótulo de assinatura `Signature-Input` —
conforme o item 3 da lista de opt-in abaixo.

Para aceitar, o signatário faz as seguintes alterações em seu BCP principal
assinatura. Os itens marcados como **OBRIGATÓRIOS** são exigidos por
[rascunho-meunier-webbotauth-httpsig-protocol-00](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-httpsig-protocol/00/)
§4.2; consulte esse rascunho para obter detalhes completos.

1. **Use um algoritmo que o verificador WBA aceite.** O WBA permite qualquer
   algoritmo no registro do algoritmo de assinaturas de mensagens HTTP RFC 9421
   (por exemplo, `ed25519`, `ecdsa-p256-sha256` = `ES256`, `ecdsa-p384-sha384`,
   `rsa-pss-sha512`). Confirme
   a aceitação com os verificadores-alvo. (Não normativo: Ed25519 é o
   mais amplamente implantado hoje.)
2. **DEVE enviar um cabeçalho `Signature-Agent`** junto com `BCP-Agent`. Um
   campo estruturado de dicionário RFC 8941 cujo valor de membro sf-string
   é uma URL HTTPS e cujo parâmetro `type` seleciona o mecanismo de
   descoberta; a chave do membro corresponde ao rótulo de assinatura
   `Signature-Input`. Veja
   [Padrões de implantação](overview.md#padroes-de-implantacao-para-interoperabilidade-wba)
   para as variantes `jwks_uri`/`cimd`/`directory` e como cada uma pode reutilizar
   o perfil BCP. (O formato embutido do URI `data:` está fora do escopo.)
3. **DEVE assinar o componente `signature-agent` com `;key="<label>"`**
   correspondendo à chave de membro do dicionário `Signature-Agent` (que é igual
   à etiqueta de assinatura `Signature-Input`). De acordo com WBA §4.2.1.
4. **DEVE definir `keyid` como a impressão digital JWK SHA-256** da chave de
   assinatura, por [RFC 7638](https://www.rfc-editor.org/rfc/rfc7638), e
   publique essa chave com `kid` definido para a mesma impressão digital (consulte
   [Formato da chave](#formato-de-chave-jwk)); assim, as pesquisas de `BCP-Agent` e
   `Signature-Agent` resolvem isso de forma idêntica. Para chaves Ed25519 (OKP), os
   membros da impressão digital são `crv`, `kty`, `x`, conforme
   [RFC 8037](https://www.rfc-editor.org/rfc/rfc8037) §2; o Apêndice A.3 tem
   um exemplo trabalhado.
5. **DEVE incluir os parâmetros `created` e `expires`.** O intervalo `expires`
   DEVE ser de no máximo 24 horas.
6. **DEVE incluir um `nonce`** para anti-replay - um valor aleatório codificado
   em base64url (RECOMENDADO 64 bytes), único dentro da janela
   `created`/`expires` (WBA §4.2.3). O `Idempotency-Key` do BCP é uma
   deduplicação de carga útil da camada de negócios, não um nonce vinculado ao
   transporte, e não o substitui. Uma origem de verificação **PODE** exigir um
   `nonce` e desafiar novamente (HTTP 429) uma assinatura que não o possui ou
   que o reutiliza (WBA §4.3–4.4).
7. **DEVE incluir `tag="web-bot-auth"`.** Os verificadores WBA selecionam
   assinaturas por esta tag.

**Requisitos de componentes preservados — e aplicados.** Uma assinatura em formato WBA
**DEVE** ainda cobrir os mesmos componentes que uma assinatura BCP padrão
cobre (o conjunto obrigatório na tabela
[Componentes assinados](#assinatura-de-solicitacao-rest)); a WBA os aceita como
"componentes adicionais" por
[rascunho-meunier-webbotauth-httpsig-protocol-00](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-httpsig-protocol/00/)
§4.2.4. O verificador impõe isso independentemente de `tag` de acordo com o
[Algoritmo de resolução de identidade](overview.md#algoritmo-de-resolucao-de-identidade),
portanto, optar pelo Web Bot Auth nunca amplia o que o BCP autentica.

**A interoperabilidade é unidirecional.** Um signatário do BCP satisfaz um verificador de
autenticação Web Bot - os verificadores WBA aceitam o conjunto coberto mais rico do BCP como
"componentes adicionais" permitidos (protocolo-00 §4.2.4). O reverso não é válido: uma
assinatura WBA mínima (cobrindo apenas `@authority`) falha na porta de cobertura do BCP e é
rejeitada. O objetivo do BCP é ser verificável *por* verificadores WBA, não aceitar
signatários WBA arbitrários - um verificador BCP aceita um subconjunto estrito do que um
verificador WBA aceita.

Os verificadores BCP veem a mesma assinatura com três novidades:

* O parâmetro `tag` é um parâmetro de assinatura RFC 9421 §2.3 desconhecido
  para verificadores somente BCP e ignorados pela permissão permissiva da RFC 9421
  manipulação de parâmetros.
* O componente `signature-agent` é processado normalmente como um componente coberto
  Campo HTTP; o parâmetro `;key="<label>"` seleciona um Dicionário
  membro de acordo com RFC 9421 §2.1.2. A verificação de assinaturas em formato WBA requer
  Suporte §2.1.2 — Assinaturas padrão do BCP não usam membro do dicionário
  seleção de componentes, portanto, verificadores construídos apenas para padrão BCP podem
  precisa adicioná-lo.
* `created` e `expires` são obrigatórios em assinaturas em formato WBA
  (item 5, conforme WBA §4.2). Aplicá-los é **definido pelo aplicativo**
  (RFC 9421 §3.2.1) — não é uma consequência automática da RFC 9421
  conformidade, e não exigida separadamente pelo BCP, cuja própria reprodução
  a proteção é a camada de negócios `Idempotency-Key`. Consciente da WBA
  o verificador que impõe a atualização rejeita assinaturas fora da janela.

**Resolução de identidade.** A aceitação do WBA não altera o BCP padrão
verificação; veja
[Algoritmo de resolução de identidade](overview.md#algoritmo-de-resolucao-de-identidade).

**Tags.** O BCP não define seu próprio `tag` (RFC 9421 §2.3). PCN
verificadores identificam suas assinaturas através do cabeçalho `BCP-Agent`,
conjunto de componentes assinados e roteamento de URL.

**Múltiplas assinaturas.** Solicitações BCP **PODEM** conter múltiplas assinaturas
usando o [RFC 9421 §4.3](https://www.rfc-editor.org/rfc/rfc9421#section-4.3)
mecanismo de rótulo. Use este padrão somente quando a separação genuína for
necessário (chaves diferentes por público, assinatura multipartidária,
conjuntos de componentes específicos do público que entram em conflito). Para interoperabilidade BCP + WBA
com uma chave, prefira o formato de assinatura única descrito acima.

## Ligação REST

Para transporte HTTP REST, o BCP usa
[RFC 9421 (Assinaturas de Mensagens HTTP)](https://www.rfc-editor.org/rfc/rfc9421).

### Cabeçalhos

| Cabeçalho | Direção | Obrigatório | Descrição |
| :---------------- | :--------------- | :--------- | :---------------------------------------------------------- |
| `Signature-Input` | Solicitação/Resposta | Sim | Descreve componentes assinados |
| `Signature` | Solicitação/Resposta | Sim | Contém valor de assinatura |
| `Content-Digest` | Solicitação/Resposta | Cond. `*` | Hash SHA-256 do corpo de solicitação/resposta |
| `Signature-Agent` | Solicitação | Cond. `**` | Fonte de chave WBA ([WBA Interop](#interoperabilidade-wba)) |

* `*` Obrigatório quando a solicitação/resposta possui corpo

* `**` Obrigatório ao optar pelo formato de assinatura compatível com Web Bot Auth;
ausente para assinaturas BCP padrão (os verificadores voltam para a identidade
derivada de `BCP-Agent`).

`Content-Digest` segue [RFC 9530](https://www.rfc-editor.org/rfc/rfc9530) e
faz hash dos bytes do corpo bruto. Isso vincula o corpo da mensagem à assinatura sem
exigindo canonização JSON. As implementações **DEVEM** usar `sha-256`. Para
artefatos duráveis que requerem canonização, consulte
[Mandatos AP2 - Canonicalização](ap2-mandates.md#canonizacao).

**Aviso de intermediário:** proxies, gateways de API e outros intermediários
**NÃO DEVE** serializar novamente os corpos JSON, pois isso invalidaria a assinatura.
O `Content-Digest` é calculado em bytes brutos; qualquer modificação quebra
verificação.

### Assinatura de solicitação REST

**Componentes assinados:**

| Componente | Obrigatório | Descrição |
| :---------------- | :----------- | :---------------------------------------------------------- |
| `@method` | Sim | Método HTTP (GET, POST, etc.) |
| `@authority` | Sim | Host de destino (evita retransmissão entre hosts) |
| `@path` | Sim | Caminho da solicitação |
| `@query` | Cond. `*` | String de consulta (se presente) |
| `ucp-agent` | Cond. `**` | URL do perfil (vincula identidade) |
| `signature-agent` | Cond. `***` | Fonte de chave WBA (quando [WBA Interop](#interoperabilidade-wba) optou por) |
| `idempotency-key` | Cond. `****` | Cabeçalho de idempotência (mudança de estado) |
| `content-digest` | Cond. `†` | Digest do corpo (se houver corpo) |
| `content-type` | Cond. `†` | Tipo de conteúdo (se corpo estiver presente) |

* `*` Obrigatório se a requisição possuir parâmetros de consulta

* `**` Obrigatório se o cabeçalho `BCP-Agent` estiver presente

* `***` Obrigatório se o cabeçalho `Signature-Agent` estiver presente (ou seja, assinatura em formato WBA)

* `****` Necessário para POST, PUT, DELETE, PATCH

* `†` Obrigatório se a solicitação tiver corpo

**Geração de assinatura:**

```text
sign_rest_request(method, path, query, body_bytes, idempotency_key, private_key, kid):
    // 1. Compute body digest (if body present)
    if body_bytes:
        digest = sha256(body_bytes)  // Hash raw bytes, no canonicalization
        digest_header = "sha-256=:" + base64(digest) + ":"

    // 2. Build component list
    components = ["@method", "@authority", "@path"]
    if query: components.append("@query")
    if ucp_agent: components.append("ucp-agent")
    if idempotency_key: components.append("idempotency-key")
    if body: components.extend(["content-digest", "content-type"])

    // 3. Build signature base (RFC 9421)
    signature_base = build_signature_base(
        components=components,
        method=method,
        path=path,
        query=query,
        headers={
            "idempotency-key": idempotency_key,
            "content-digest": digest_header,
            "content-type": "application/json"
        },
        keyid=kid
    )

    // 4. Sign
    signature = sign(signature_base, private_key)  // ecdsa for EC, eddsa for OKP

    // 5. Return headers
    return {
        "Idempotency-Key": idempotency_key,
        "Content-Digest": digest_header,
        "Signature-Input": format_signature_input(components, kid),
        "Signature": "sig1=:" + base64(signature) + ":"
    }
```

**Codificação de assinatura:**

* **Assinaturas ECDSA** **DEVEM** usar codificação `r||s` bruta de largura fixa por
  RFC 9421 §3.3.1, **não** ASN.1/DER. O valor da assinatura é a
  concatenação de `r` e `s` como inteiros não assinados big-endian de
  comprimento fixo: 64 bytes para P-256 (32 + 32), 96 bytes para P-384 (48 + 48).
  Muitas bibliotecas criptográficas (OpenSSL, Java, .NET) usam como padrão a codificação DER e
  requerem conversão explícita.
* **EdDSA (Ed25519)** assinaturas **DEVEM** usar a codificação definida por
  RFC 8032 §5.1.6 — a concatenação de 64 bytes do ponto `R` codificado
  e o inteiro `S`. Esta é a saída padrão da assinatura Ed25519
  bibliotecas; nenhuma conversão DER está envolvida.

**Exemplo de solicitação completa:**

<!-- ucp:example schema=shopping/checkout op=create direction=request -->
```json
POST /checkout-sessions HTTP/1.1
Host: merchant.example.com
Content-Type: application/json
BCP-Agent: profile="https://platform.example/.well-known/bcp"
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Digest: sha-256=:X48E9q...:
Signature-Input: sig1=("@method" "@authority" "@path" "ucp-agent" "idempotency-key" "content-digest" "content-type");keyid="platform-2026"
Signature: sig1=:MEUCIQDTxNq8h7LGHpvVZQp1iHkFp9+3N8Mxk2zH1wK4YuVN8w...:

{
  "line_items": [
    {
      "item": {"id": "item_123"},
      "quantity": 2
    }
  ]
}
```

**Exemplo de solicitação GET (sem corpo, sem idempotência):**

```http
GET /checkout-sessions/chk_123 HTTP/1.1
Host: merchant.example.com
Signature-Input: sig1=("@method" "@authority" "@path");keyid="platform-2026"
Signature: sig1=:MEQCIBx7kL9nM2oP5qR8sT1uV4wX6yZaB3cD...:
```

### Assinatura de resposta REST

As assinaturas de resposta usam `@status` em vez de `@method`:

**Componentes assinados:**

| Componente | Obrigatório | Descrição |
| :--------------- | :--------- | :-------------------------------- |
| `@status` | Sim | Código de status HTTP (200, 201, etc.) |
| `content-digest` | Cond. `*` | Digest do corpo (se houver corpo) |
| `content-type` | Cond. `*` | Tipo de conteúdo (se corpo estiver presente) |

* `*` Obrigatório se a resposta tiver corpo

**Exemplo de resposta completa:**

O corpo da resposta abaixo é abreviado para maior clareza – apenas os campos principais
usados na assinatura são mostrados. Uma resposta completa de checkout inclui campos
obrigatórios adicionais (`ucp`, `currency`, `line_items`, `totals`, `links`); veja
*Criar uma resposta de Checkout* (não incluída nesta versão do BCP) para a
forma completa.

```http
HTTP/1.1 201 Created
Content-Type: application/json
Content-Digest: sha-256=:Y5fK8nLmPqRsT3vWxYzAbCdEfGhIjKlMnO...:
Signature-Input: sig1=("@status" "content-digest" "content-type");created=1738617601;keyid="merchant-2026"
Signature: sig1=:MFQCIH7kL9nM2oP5qR8sT1uV4wX6yZaB3cD...:

{
  "id": "chk_123",
  "status": "ready_for_complete",
  "...": "abbreviated; see linked spec for full shape"
}
```

**Geração de assinatura de resposta:**

A assinatura de resposta espelha a assinatura de solicitação com `@status` substituindo `@method`:

```text
sign_rest_response(status, body_bytes, private_key, kid):
    // 1. Compute body digest (if body present)
    if body_bytes:
        digest = sha256(body_bytes)  // Hash raw bytes, no canonicalization
        digest_header = "sha-256=:" + base64(digest) + ":"

    // 2. Build signature base (RFC 9421)
    signature_base = build_signature_base(
        components=["@status", "content-digest", "content-type"],
        status=status,
        headers={"content-digest": digest_header, "content-type": "application/json"},
        created=current_timestamp(),
        keyid=kid
    )

    // 3. Sign
    signature = sign(signature_base, private_key)  // ecdsa for EC, eddsa for OKP

    // 4. Return headers
    return {
        "Content-Digest": digest_header,
        "Signature-Input": 'sig1=("@status" "content-digest" "content-type");created=...;keyid="..."',
        "Signature": "sig1=:" + base64(signature) + ":"
    }
```

### Verificação de solicitação REST

**Resolvendo as chaves do signatário:**

Veja
[Algoritmo de resolução de identidade](overview.md#algoritmo-de-resolucao-de-identidade)
para a regra de resolução-chave (escolhida pela capacidade do verificador e pelos
cabeçalhos presentes, não pelo `tag` da assinatura). Esta seção especifica
apenas análise de cabeçalho - `BCP-Agent` para o regime BCP padrão,
`Signature-Agent` para o regime de formato WBA.

**Regras de análise `BCP-Agent`** (regime BCP padrão):

1. Analise como Dicionário RFC 8941
2. Extraia a chave `profile` (OBRIGATÓRIO)
3. O valor DEVE ser uma string entre aspas contendo um URL HTTPS
4. Para perfis empresariais, a URL DEVE apontar para `/.well-known/bcp`; URLs de
   perfil de plataforma não são restritos por caminho
5. Rejeite URLs não HTTPS

**Regras de análise `Signature-Agent`** (regime de formato WBA):

1. Analise como Dicionário RFC 8941.
2. **DEVE** localizar o membro do dicionário cuja chave é igual à
   etiqueta de assinatura sendo verificada (para `Signature-Input: sig1=...`,
   localize o membro `sig1`). Se não existir nenhum membro correspondente, a verificação
   desta assinatura **DEVE** falhar.
3. O valor do membro **DEVE** ser uma string sf contendo uma URL HTTPS.
   Seu parâmetro `type` seleciona a resolução — `jwks_uri` (uma URL de
   conjunto de JWK, por ex. o perfil BCP), `cimd` (um Client ID Metadata
   Document), ou `directory` (uma origem que hospeda um diretório
   conhecido); veja
   [Padrões de implantação](overview.md#padroes-de-implantacao-para-interoperabilidade-wba).
   O formato embutido do URI `data:` está fora do escopo da interoperabilidade BCP-WBA.
4. A verificação desta assinatura **DEVE** falhar se o URL for
   não HTTPS.

**Exemplo (BCP padrão):**

```text
// Header
BCP-Agent: profile="https://platform.example/.well-known/bcp"

// Parsed
profile_url = "https://platform.example/.well-known/bcp"
```

**Exemplo (Agente de assinatura, formato WBA):**

```text
// Headers
Signature-Agent: sig1="https://platform.example/.well-known/bcp";type=jwks_uri
Signature-Input: sig1=("@method" "@authority" ...);...

// Parsed (member key matches sig1)
type = jwks_uri
jwks_uri = "https://platform.example/.well-known/bcp"
```

**Aplicabilidade:**

* **Plataforma → Solicitações comerciais:** URL do perfil do cabeçalho `BCP-Agent`
* **Negócios → webhooks da plataforma:** URL do perfil do cabeçalho `BCP-Agent`

Ambas as rotinas abaixo verificam uma assinatura de **único candidato**.
`skip_signature(reason)` significa que o candidato não autentica a
mensagem: sob tratamento de múltiplas assinaturas
([RFC 9421 §4.3](https://www.rfc-editor.org/rfc/rfc9421#section-4.3); consulte
o [Algoritmo de Resolução de Identidade](overview.md#algoritmo-de-resolucao-de-identidade)),
o verificador tenta o próximo candidato e rejeita a mensagem somente quando
**todo** candidato pula. `success()` autentica a mensagem.

```text
verify_rest_request(request):
    // 1. Parse Signature-Input
    sig_input = parse_signature_input(request.headers["Signature-Input"])
    keyid = sig_input.keyid
    components = sig_input.components

    // 2. Resolve signer's public key (capability-based; see
    // overview.md#algoritmo-de-resolucao-de-identidade).
    key_set = resolve_signer_key_set(request.headers)
    // sig_capable skips keys not usable for verification: use:"enc", or
    // key_ops present without "verify" (RFC 7517 §4.2, §4.3)
    public_key = find_key_by_kid(sig_capable(key_set), keyid)
    if not public_key:
        return skip_signature("key_not_found")

   // pre-2a. WBA-shape signatures bind key identity to key bytes:
   // keyid MUST equal the matched JWK's RFC 7638 thumbprint
   // (see IRA step 4 / WBA architecture draft §4.2).
   if sig_input.tag == "web-bot-auth":
       if keyid != rfc7638_thumbprint(public_key):
           return skip_signature("signature_invalid")
    // 2a. Skip keys whose algorithm this verifier does not support.
    // The kty/crv/alg vocabularies are open (see Signature Algorithms);
    // an unsupported key never invalidates the whole key set.
    if not algorithm_supported(public_key):
        return skip_signature("algorithm_unsupported")

    // 2b. Enforce covered-component requirements (all regimes/transports).
    // Bind the target, the body when present, and every integrity-relevant
    // header the request carries. A signature covering only WBA's minimum
    // (@authority, signature-agent) does not authenticate a request whose
    // body/method/path is unbound.
    // (Which requests must CARRY Idempotency-Key is a binding rule,
    // separate from this coverage check.)
    required = ["@method", "@authority", "@path"]
    if request.query:                        required += ["@query"]
    if request.has_body:                     required += ["content-digest", "content-type"]
    if "Idempotency-Key" in request.headers: required += ["idempotency-key"]
    if "BCP-Agent" in request.headers:       required += ["ucp-agent"]
    if "Signature-Agent" in request.headers: required += ["signature-agent"]
    for component in required:
        if component not in components:
            // coverage failure, a target/body/header the signature does not
            // cover is treated as unsigned (see IRA step 5)
            return skip_signature("coverage_insufficient")

    // 3. Verify body digest (if body present)
    if "content-digest" in components:
        expected = "sha-256=:" + base64(sha256(request.body_bytes)) + ":"
        if request.headers["Content-Digest"] != expected:
            return skip_signature("digest_mismatch")

    // 4. Reconstruct signature base
    signature_base = build_signature_base(
        components, request.method, request.path, request.query,
        request.headers, keyid
    )

    // 5. Verify signature
    signature = parse_signature(request.headers["Signature"])
    if not verify(signature_base, signature, public_key):
        return skip_signature("signature_invalid")

    return success()

    // Note: Replay protection handled by the signed idempotency-key header
```

### Verificação de resposta REST

A verificação de resposta espelha a verificação de solicitação com `@status`
substituindo `@method`:

```text
verify_rest_response(response, signer_profile_url):
    // 1. Parse Signature-Input
    sig_input = parse_signature_input(response.headers["Signature-Input"])
    keyid = sig_input.keyid
    components = sig_input.components

    // 2. Resolve signer's public key from the signer's profile.
    profile = fetch_profile(signer_profile_url)
    // signature-capable keys only (see request path; RFC 7517 §4.2, §4.3)
    public_key = find_key_by_kid(sig_capable(profile.keys), keyid)
    if not public_key:
        return skip_signature("key_not_found")

    // 2a. Skip keys whose algorithm this verifier does not support.
    // The kty/crv/alg vocabularies are open (see Signature Algorithms);
    // an unsupported key never invalidates the whole key set.
    if not algorithm_supported(public_key):
        return skip_signature("algorithm_unsupported")

    // 2b. Enforce covered-component requirements for responses (all regimes).
    // No method/idempotency to bind, but the body still MUST be covered.
    required = ["@status"]
    if response.has_body: required += ["content-digest", "content-type"]
    for component in required:
        if component not in components:
            return skip_signature("signature_invalid")

    // 3. Verify body digest (if body present)
    if "content-digest" in components:
        expected = "sha-256=:" + base64(sha256(response.body_bytes)) + ":"
        if response.headers["Content-Digest"] != expected:
            return skip_signature("digest_mismatch")

    // 4. Reconstruct signature base
    signature_base = build_signature_base(
        components, response.status,
        response.headers, keyid
    )

    // 5. Verify signature
    signature = parse_signature(response.headers["Signature"])
    if not verify(signature_base, signature, public_key):
        return skip_signature("signature_invalid")

    return success()
```

### Proteção de repetição

O BCP lida com a proteção de reprodução na **camada de negócios** por meio de chaves de idempotência,
não na camada de assinatura. Isso fornece separação de preocupações:

| Camada | Responsabilidade |
| :---- | :------------ |
| **Assinatura** | Autenticação (quem), Integridade (o quê) |
| **Idempotência** | Novas tentativas seguras, proteção de repetição |

**Como funciona:**

1. As operações de mudança de estado incluem um `idempotency-key` na solicitação
2. A chave de idempotência faz parte da carga assinada
3. Os invasores não podem modificar a chave sem invalidar a assinatura
4. Solicitações duplicadas retornam respostas em cache (sem novos efeitos colaterais)

**Colocação da chave de idempotência:**

O cabeçalho `Idempotency-Key` está incluído nos componentes assinados:

```http
POST /checkout-sessions HTTP/1.1
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Signature-Input: sig1=("@method" "@authority" "@path" "idempotency-key" ...);keyid="platform-2026"
Signature: sig1=:MEUCIQD...:
```

**Requisitos-chave de idempotência:**

| Requisito | Valor |
| :---------- | :---- |
| **Entropia** | Mínimo de 128 bits (por exemplo, UUID v4, 22+ caracteres alfanuméricos) |
| **Singularidade** | Por cliente, por tipo de operação |
| **Armazenamento do servidor** | Mínimo 24 horas, recomendado 48 horas |
| **Em duplicado (carga útil correspondente)** | Retornar resposta em cache, não executar novamente |
| **Em duplicado (carga útil incompatível)** | Rejeitar com `409 Conflict` (REST) / `-32000` (MCP); não executar |
| **Em caso de falha de armazenamento** | Falha fechada (rejeitar solicitação com 503) |

**Correspondência de carga útil:** As empresas **DEVEM** detectar se a carga útil de
uma solicitação de chave duplicada corresponde à carga útil da original,
comparando o hash SHA-256 dos bytes do corpo bruto - o mesmo resumo RFC 9530
exigido em `Content-Digest`. Quando a assinatura está em uso, esse valor é
fornecido no cabeçalho `Content-Digest`, e o Aviso de Intermediário acima
garante fidelidade de bytes de ponta a ponta; as empresas devem persistir esse
valor junto com a chave de idempotência. Para solicitações não assinadas, as
empresas calculam o mesmo resumo a partir dos bytes do corpo recebido.
Plataformas, portanto, **DEVEM** gerar uma nova chave de idempotência sempre
que modificarem a carga útil da solicitação – incluindo novas tentativas com
instrumentos de pagamento modificados, endereços de envio atualizados, itens
de linha trocados ou qualquer outra alteração no corpo da solicitação.

**Observação:** Para assinaturas **BCP padrão**, o parâmetro `created` do
RFC 9421 é **OPCIONAL** e a proteção de reprodução é tratada na camada de
negócios por meio de chaves de idempotência, não de carimbos de data e hora de
assinatura. **Assinaturas em formato WBA** também carregam `created`/`expires`
(e **DEVEM** carregar um `nonce`) para verificadores WBA; reforçar essa janela
de frescor (freshness) é definido pelo aplicativo (RFC 9421 §3.2.1). Veja
[Interoperabilidade WBA](#interoperabilidade-wba).
A rotação de chaves (removendo chaves comprometidas do conjunto de chaves
publicado do perfil) fornece o mecanismo para invalidar assinaturas antigas.

### Quando as assinaturas são aplicadas

**Solicitações:** As plataformas **DEVEM** assinar todas as solicitações ao usar
Assinaturas de Mensagens HTTP. Mecanismos de autenticação alternativos (chaves de
API, OAuth, mTLS) podem ser usados em seu lugar.

**Webhooks:** notificações de webhook **DEVEM** ser assinadas. Os destinatários não
podem, de outra forma, verificar a autenticidade das mensagens push iniciadas pelo
servidor.

**Outras respostas:** Assinaturas são **RECOMENDADAS** para:

* Respostas de autorização de pagamento
* Respostas de conclusão de checkout

As assinaturas são **OPCIONAIS** para:

* Operações de carrinho (de baixo valor, síncronas)
* Consultas de catálogo (somente leitura)
* Respostas de erro (4xx, 5xx)

## Transporte MCP

O BCP especifica **HTTP streamable** para transporte MCP, substituindo transportes baseados em SSE.
Como as solicitações MCP são solicitações HTTP padrão com corpos JSON-RPC, o mesmo
mecanismo de assinatura RFC 9421 se aplica:

* O cabeçalho `Content-Digest` cobre o corpo da mensagem JSON-RPC
* Os cabeçalhos `Signature-Input` e `Signature` fornecem autenticação
* O cabeçalho `BCP-Agent` funciona de forma idêntica ao REST; `Idempotency-Key` é
  assinado quando presente, mas, como toda solicitação MCP é um POST, se ela é
  necessária depende da operação JSON-RPC (mudança de estado), não do método
  HTTP

**Exemplo de solicitação de MCP com assinatura:**

```http
POST /mcp HTTP/1.1
Host: business.example.com
Content-Type: application/json
BCP-Agent: profile="https://platform.example/.well-known/bcp"
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Digest: sha-256=:RK/0qy18MlBSVnWgjwz6lZEWjP/lF5HF9bvEF8FabDg=:
Signature-Input: sig1=("@method" "@authority" "@path" "content-digest" "content-type" "ucp-agent" "idempotency-key");keyid="platform-2026"
Signature: sig1=:MEUCIQDXyK9N3p5Rt...:

{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"complete_checkout","arguments":{"id":"chk_123","checkout":{...}}}}
```

A mensagem JSON-RPC é o corpo HTTP. `Content-Digest` vincula-o à assinatura.
Nenhuma canonização JSON é necessária.

## Tratamento de erros

Os erros de verificação de assinatura usam códigos de erro BCP padrão. Veja
[Tratamento de Erros](overview.md#tratamento-de-erros) na visão geral da especificação para
o registro completo do código de erro e as ligações de transporte.

**Erros específicos de assinatura:**

| Código | HTTP | Descrição |
| :---------------------- | :--- | :---------------------------------------------------------------- |
| `signature_missing` | 401 | Cabeçalho/campo de assinatura obrigatório não presente |
| `signature_invalid` | 401 | Falha na verificação da assinatura |
| `key_not_found` | 401 | ID da chave não encontrado no conjunto de chaves publicadas do signatário |
| `digest_mismatch` | 400 | O resumo do corpo não corresponde ao cabeçalho `Content-Digest` |
| `algorithm_unsupported` | 400 | Algoritmo de assinatura não suportado |

**Erros relacionados ao perfil** (também usados para negociação de recursos):

| Código | HTTP | Descrição |
| :---------------------- | :--- | :--------------------------------------------------------------------- |
| `invalid_profile_url` | 400 | URL do perfil malformado ou esquema inválido |
| `profile_unreachable` | 424 | Não foi possível obter o perfil do signatário |
| `profile_not_trusted` | 403 | URL do perfil não consta em cadastro de plataformas pré-aprovadas |

**Observação:** A proteção de repetição é tratada na camada de negócios por meio de idempotência
chaves, não na camada de assinatura. Solicitações duplicadas retornam respostas armazenadas em cache
em vez de erros de assinatura.

### Resposta de erro REST

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "code": "signature_invalid",
  "content": "Request signature verification failed for key kid=platform-2026"
}
```

### Resposta de erro do MCP

<!-- ucp:example schema=transports/jsonrpc def=error_response -->
```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "error": {
    "code": -32000,
    "message": "Signature verification failed",
    "data": {
      "code": "signature_invalid",
      "content": "Signature verification failed for key kid=platform-2026"
    }
  }
}
```

## Referências

* [RFC 7517](https://datatracker.ietf.org/doc/html/rfc7517) — Chave Web JSON (JWK)
* [RFC 7518](https://datatracker.ietf.org/doc/html/rfc7518) — Algoritmos JSON Web (JWA), §6.2 (chaves públicas EC)
* [RFC 8032](https://datatracker.ietf.org/doc/html/rfc8032) — Algoritmo de assinatura digital da curva de Edwards (EdDSA)
* [RFC 8037](https://datatracker.ietf.org/doc/html/rfc8037) — CFRG Curva Elíptica Diffie-Hellman (ECDH) e Assinaturas em JOSE
* [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421) — Assinaturas de mensagens HTTP
* [RFC 9530](https://www.rfc-editor.org/rfc/rfc9530) — Campos Digest (Content-Digest)
