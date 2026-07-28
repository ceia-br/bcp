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

# Capacidade de vinculação de identidade

* **Nome do recurso:** `br.dev.bcp.common.identity_linking`
* **Esquema:** `https://bcp.dev.br/schemas/common/identity_linking.json`

## Visão geral

O recurso Identity Linking permite que uma **plataforma** obtenha autorização
para executar ações em nome de um **usuário** em uma **empresa** (a parte
confiável).

Essa ligação é fundamental para experiências de comércio autenticadas pelo usuário: acessar
benefícios de fidelidade, ofertas personalizadas, endereços salvos, listas de desejos e
histórico de pedidos. Capacidades sem vinculação de identidade ainda operam em nível público ou
em níveis de acesso autenticados pelo agente – a vinculação de identidade eleva a experiência,
não a bloqueia.

**Esta especificação usa
[OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749){ target="_blank" }**
para autorização. O OAuth 2.0 direcionado ao domínio comercial (via
[Discovery](#descoberta)) está sempre disponível. Quando a empresa declara
provedores de identidade externos confiáveis em seu `config.providers`, a
plataforma **PODE**, em vez disso, encadear a identidade de um provedor por meio do
[Fluxo IdP acelerado](#fluxo-de-idp-acelerado), ignorando o
fluxo baseado em navegador quando ela já possui um token upstream adequado.

### Participantes

| Função no BCP | Função de identidade | Descrição |
| :------- | :----------- | :---------- |
| **Plataforma** | Agente do usuário | Intermediário confiável que inicia a vinculação de identidade e apresenta tokens de identidade do usuário às empresas em nome do usuário. |
| **Negócios** | Servidor de autorização/Parte confiável | Hospeda seu próprio servidor de autorização OAuth 2.0. Autentica usuários e emite tokens de acesso com escopo para recursos BCP. |
| **Usuário** | Proprietário do recurso | A pessoa cuja identidade está sendo vinculada. Concede consentimento explícito à plataforma durante o fluxo de autorização OAuth. |

### Níveis de acesso

Os recursos operam em três níveis de acesso:

| Nível | Autenticação | Exemplo |
| :---- | :------------ | :------ |
| **Público** | Nenhum | Navegue em um catálogo público |
| **Autenticado pelo agente** | Credenciais da plataforma (`client_id` / `client_secret`) | Finalização da compra como convidado, criação de um carrinho |
| **Autenticado pelo usuário** | Credenciais da plataforma + token de identidade do usuário | Endereços salvos, histórico completo de pedidos, preços personalizados |

A vinculação de identidade conecta o acesso autenticado pelo agente ao acesso autenticado pelo usuário: o
plataforma obtém um token de identidade do usuário completando o fluxo OAuth descrito
abaixo e apresenta-o em solicitações subsequentes.

**A vinculação de identidade e a negociação de capacidade são camadas independentes.**
A capacidade é anunciada e negociada com base na presença de seu próprio perfil —
nunca é excluída porque a vinculação de identidade está ausente. A vinculação de
identidade, quando presente, declara os **escopos** que controlam operações
autenticadas pelo usuário *dentro* dos recursos negociados (consulte
[Escopos](#escopos)). Um comerciante cujo perfil lista `br.dev.bcp.shopping.order`
tem essa capacidade na interseção negociada de qualquer forma. Se o perfil dele
*também* listar vinculação de identidade com `br.dev.bcp.shopping.order:read` em
`config.scopes`, as operações cobertas por esse escopo exigirão um token de
identidade do usuário.

### BCP e OAuth

O BCP define a semântica comercial (o que cada escopo significa, quais operações
cada um controla); OAuth ([RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" })
define o mecanismo de identidade (endpoints, fluxos, vocabulário de escopos
aceito); mensagens de tempo de execução carregam avisos por solicitação.

* **BCP `config.scopes`** declara **hard gates**: escopos que *exigem*
    autenticação do usuário para as operações que cobrem.
* **OAuth `scopes_supported`** (RFC 8414) declara o **vocabulário de escopo
    aceito**: todo escopo que o servidor de autorização honrará se
    solicitado.
* O diff (`scopes_supported` ∖ `config.scopes`) é a **camada opcional**:
    escopo que o comerciante aceita, mas não bloqueia, usado para anunciar
    recursos desbloqueados por autenticação sem exigir autenticação.
* **BCP `messages[]`** carrega **dicas contextuais de tempo de execução**: por solicitação
    avisos como `identity_optional` (veja
    [Autenticação opcional](#autenticacao-opcional)) sinalizando que
    a autenticação desbloquearia valor no contexto atual.

## Diretrizes gerais

### Para plataformas

* **DEVE** autenticar solicitações de endpoint de token usando um método anunciado em
    os metadados `token_endpoint_auth_methods_supported` da empresa
    ([RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }):
    * **Clientes confidenciais** (plataformas do lado do servidor que podem proteger uma
        credencial) **DEVEM** preferir métodos assimétricos -
        `private_key_jwt`
        ([RFC 7523 §2.2](https://datatracker.ietf.org/doc/html/rfc7523#section-2.2){ target="_blank" })
        ou `tls_client_auth`
        ([RFC 8705](https://datatracker.ietf.org/doc/html/rfc8705){ target="_blank" })
        — e **PODE** usar `client_secret_basic`
        ([RFC 6749 §2.3.1](https://datatracker.ietf.org/doc/html/rfc6749#section-2.3.1){ target="_blank" },
        [RFC 7617](https://datatracker.ietf.org/doc/html/rfc7617){ target="_blank" })
        onde a empresa o suportar.
    * **Clientes públicos** (nativos, desktop, extensão de navegador e tempos de
        execução de agente no dispositivo, por
        [RFC 8252 §8.5](https://datatracker.ietf.org/doc/html/rfc8252#section-8.5){ target="_blank" })
        **DEVEM** usar `none` e contar com PKCE com `S256`
        ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636){ target="_blank" })
        como prova de posse do código de autorização. Clientes públicos
        **NÃO DEVEM** incorporar um `client_secret`.

    As plataformas **DEVEM** selecionar o método mais forte oferecido pela empresa
    que seja compatível com o modelo de implantação da plataforma.

* **DEVE** incluir tokens de identidade do usuário no cabeçalho HTTP `Authorization`
    usando o esquema Bearer: `Authorization: Bearer <access_token>`
    ([RFC 6750 §2.1](https://datatracker.ietf.org/doc/html/rfc6750#section-2.1){ target="_blank" }).
* **DEVE** processar desafios `WWW-Authenticate: Bearer` por
    [RFC 6750 §3](https://datatracker.ietf.org/doc/html/rfc6750#section-3){ target="_blank" }
    nas respostas `401` e `403` para operações autenticadas pelo usuário.
    As plataformas **DEVEM** extrair o parâmetro `scope` (quando presente) para
    construir solicitações de autorização subsequentes e **DEVE** seguir
    o ponteiro `resource_metadata`
    ([RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728){ target="_blank" })
    quando presente para descobrir o servidor de autorização de proteção.
* **DEVE** implementar o fluxo do código de autorização OAuth 2.0
    ([RFC 6749 §4.1](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1){ target="_blank" })
    como mecanismo de vinculação de contas.
* **DEVE** usar PKCE
    ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636){ target="_blank" })
    com `code_challenge_method=S256` para todas as trocas de códigos de autorização.
* **DEVE** validar o parâmetro `iss` na resposta de autorização
    ([RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207){ target="_blank" })
    para evitar ataques de confusão. A plataforma **DEVE** verificar se o `iss`
    valor corresponde ao URI do emissor do servidor de autorização (conforme declarado em seu
    [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }
    metadados). Se os valores não corresponderem, a plataforma **DEVE**
    abortar e descartar a resposta de autorização.
* **DEVE** incluir um parâmetro `state` exclusivo e indecifrável no
    solicitação de autorização para evitar CSRF
    ([RFC 6749 §10.12](https://datatracker.ietf.org/doc/html/rfc6749#section-10.12){ target="_blank" }).
* Quando `config.providers` está presente, a plataforma **PODE** encadear
    identidade de um provedor listado por meio do
    [Fluxo IdP acelerado](#fluxo-de-idp-acelerado). Se nenhum provedor listado
    for compatível ou adequada, a plataforma **DEVE** recorrer ao direcionamento
    OAuth no domínio comercial por meio de [Discovery](#descoberta) (consulte
    [Provedores de identidade](#provedores-de-identidade)).
* Antes de iniciar o encadeamento de identidade com uma empresa, a plataforma
    **DEVE** oferecer ao usuário uma escolha de provedores de identidade disponíveis e
    indicar qual identidade do provedor será compartilhada com a empresa.
* Eventos de revogação e segurança:
    * **DEVE** ligar para o endpoint de revogação de token da empresa
        ([RFC 7009](https://datatracker.ietf.org/doc/html/rfc7009){ target="_blank" })
        quando um usuário inicia uma ação de desvinculação na plataforma.
    * **DEVE** apoiar
        [Perfil OpenID RISC 1.0](https://openid.net/specs/openid-risc-1_0-final.html){ target="_blank" }
        para lidar com atualizações assíncronas de contas e proteção entre contas
        eventos iniciados pela empresa.

### Para empresas

* **DEVE** implementar OAuth 2.0
    ([RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749){ target="_blank" }).
* **DEVE** publicar metadados do servidor de autorização via
    [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }
    em `/.well-known/oauth-authorization-server`.
* **DEVE** preencher `scopes_supported` em
    [RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }
    metadados para permitir plataformas
    para detectar incompatibilidades de escopo antes de iniciar um fluxo de autorização.
* **DEVE** retornar o parâmetro `iss` na resposta de autorização
    ([RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207){ target="_blank" }).
* **DEVE** aplicar o PKCE
    ([RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636){ target="_blank" })
    validação no endpoint do token para todas as trocas de código de autorização.
    Solicitações sem um `code_verifier` válido **DEVEM** ser rejeitadas.
* **DEVE** impor a correspondência exata de strings para o parâmetro `redirect_uri`
    durante solicitações de autorização para evitar redirecionamentos abertos e roubo de token.
    O `redirect_uri` na solicitação de token **DEVE** ser idêntico ao
    na solicitação de autorização. **Exceção — redirecionamentos de loopback:** Para
    redirecionar URIs direcionados a `127.0.0.1` ou `[::1]`, as empresas **DEVEM** ignorar
    o componente da porta e corresponda apenas ao esquema, host e caminho, para acomodar
    clientes nativos e de desktop que obtêm uma porta efêmera do sistema operacional em
    tempo de execução
    ([RFC 8252 §7.3](https://datatracker.ietf.org/doc/html/rfc8252#section-7.3){ target="_blank" }).
* **DEVE** declarar métodos de autenticação de cliente suportados em
    `token_endpoint_auth_methods_supported`
    ([RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }) e aplicar um dos métodos declarados no endpoint do token.
    As empresas **DEVEM** oferecer suporte a pelo menos um método de cliente
    confidencial assimétrico (`private_key_jwt` ou `tls_client_auth`) e **PODEM** suportar `none`
    para clientes públicos por
    [RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252){ target="_blank" }.
    Quando `none` é anunciado, as empresas **DEVEM** exigir PKCE com `S256` e
    **DEVEM** rejeitar qualquer resgate de código de autorização que não tenha um valor válido
    de `code_verifier`. Solicitações que falham no método de autenticação negociado
    **DEVEM** ser rejeitadas com `invalid_client`; solicitações que falham no PKCE
    **DEVEM** ser rejeitadas com `invalid_grant`.
* **DEVE** validar tokens de identidade do usuário em cada solicitação autenticada pelo usuário:
    verificar `iss`, `aud` (o identificador do servidor de recursos da empresa), `exp`,
    escopos e `client_id` / `azp` (ou equivalente) para confirmar se o token foi
    emitido para o cliente da plataforma autenticado
    ([RFC 9068 §4](https://datatracker.ietf.org/doc/html/rfc9068#section-4){ target="_blank" }).
* **DEVE** emitir um desafio `WWW-Authenticate: Bearer` por
    [RFC 6750 §3](https://datatracker.ietf.org/doc/html/rfc6750#section-3){ target="_blank" }
    em `401 Unauthorized` (`identity_required`) e `403 Forbidden`
    (`insufficient_scope`) respostas para operações autenticadas pelo usuário.
    Consulte [Tratamento de erros](#tratamento-de-erros) para obter a norma completa
    requisitos.
* **DEVE** implementar a revogação de token
    ([RFC 7009](https://datatracker.ietf.org/doc/html/rfc7009){ target="_blank" }).
    Revogar um `refresh_token` **DEVE** também invalidar imediatamente todos os
    `access_token`s emitidos a partir dele.
* **DEVE** suportar solicitações de revogação autenticadas com as mesmas
    credenciais de cliente usadas no endpoint do token.
* **PODE** declarar provedores de identidade externos confiáveis em
    `config.providers` (consulte [Provedores de identidade](#provedores-de-identidade)).
    As empresas **DEVEM** listar apenas fornecedores em que confiam explicitamente e
    **NÃO DEVE** listar seu próprio servidor de autorização.
* Quando a empresa lista provedores de identidade externos de `type: oauth2` em
    `config.providers`, a empresa **DEVE** apoiar a afirmação do portador JWT
    tipo de concessão
    ([RFC 7523](https://datatracker.ietf.org/doc/html/rfc7523){ target="_blank" })
    em seu endpoint de token para aceitar concessões de autorização JWT daqueles
    IdPs e **DEVE** incluir
    `urn:ietf:params:oauth:grant-type:jwt-bearer` em `grant_types_supported`
    em seus metadados RFC 8414.
* **DEVE** fornecer um fluxo de criação de conta se o usuário ainda não tiver
    uma conta ou retornar um `continue_url` em um erro `identity_required`
    resposta (consulte [Tratamento de erros](#tratamento-de-erros)) apontando para uma integração
    fluxo.
* **DEVE** oferecer suporte aos escopos BCP padrão, conforme definido no
    Seção [Escopos](#escopos).
* **DEVE** publicar metadados de recursos protegidos em
    `/.well-known/oauth-protected-resource`
    ([RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728){ target="_blank" })
    e referenciá-lo através do parâmetro `resource_metadata` em
    Desafios `WWW-Authenticate`. Isso permite que as plataformas descubram
    servidor de autorização protegendo o recurso sem depender de
    convenções de domínio e prepara a implantação para futuros delegados
    convenções de domínio. A empresa **DEVE** publicar esses metadados quando
    o servidor de autorização não reside no domínio comercial.
* **DEVE** apoiar
    [Perfil OpenID RISC 1.0](https://openid.net/specs/openid-risc-1_0-final.html){ target="_blank" }
    para sinalizar revogação e alterações de estado de conta nas plataformas.

## Descoberta

A descoberta do BCP é um pipeline de três etapas.

**Etapa 1 — Resolver o emissor do AS.** As plataformas buscam o negócio
metadados de recursos protegidos por
[RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728){ target="_blank" }
e use a entrada selecionada de `authorization_servers` como AS
emissor. O emissor do AS **PODE** estar hospedado em uma origem diferente da
domínio empresarial. Se a empresa não publicar nenhum recurso protegido
metadados, o emissor AS assume como padrão o domínio de negócios (host único
implantações).

**Etapa 2 — Buscar metadados AS.** Usando o emissor da Etapa 1, plataformas
resolver metadados do servidor de autorização por meio de uma hierarquia estrita de duas camadas.
URLs conhecidos são construídos por
[RFC 8414 §3.1](https://datatracker.ietf.org/doc/html/rfc8414#section-3.1){ target="_blank" }
(o segmento conhecido é inserido entre o host e qualquer emissor
caminho, não anexado).

1. **RFC 8414 (Primário):** Buscar
   `https://{host}/.well-known/oauth-authorization-server{path}`.
    * Resposta `2xx`: utilize estes metadados. Descoberta concluída.
    * `404 Not Found`: prossiga para o passo 2.
    * Qualquer outra resposta diferente de 2xx, erro de rede ou tempo limite: **DEVE**
      abortar. **NÃO DEVE** prosseguir para a etapa 2.

2. **Descoberta OIDC (substituto):** Buscar
   `{issuer}/.well-known/openid-configuration`.
    * Resposta `2xx`: utilize estes metadados. Descoberta concluída.
    * Qualquer resposta diferente de 2xx, erro de rede ou tempo limite: **DEVE** abortar.

As plataformas **NÃO DEVEM** falhar silenciosamente devido a qualquer erro que não seja
`404` na etapa 1.

**Etapa 3 — Valide o emissor.** O valor `issuer` no descoberto
metadados **DEVEM** corresponder byte por byte ao emissor AS selecionado na Etapa 1
(por
[RFC 8414 §3.3](https://datatracker.ietf.org/doc/html/rfc8414#section-3.3){ target="_blank" }).
As plataformas **NÃO DEVEM** normalizar (por exemplo, remover barras finais) antes
comparação.

## Fluxo de vinculação de contas

A vinculação de identidade usa o fluxo do código de autorização OAuth 2.0 com PKCE.

```text
Platform                              Business AS
   |                                       |
   |-- (1) Discover metadata via RFC 8414 -->

|
   |<-- authorization_endpoint, token_endpoint, scopes_supported --|
   |                                       |
   |-- (2) Authorization Request --------->

|
   |       response_type=code              |
   |       client_id, redirect_uri         |
   |       scope=<derived scope set>       |
   |       code_challenge (S256)           |
   |       state                           |
   |                                       |
   |       [user authenticates and         |
   |        grants consent at business]    |
   |                                       |
   |<-- (3) Authorization Response --------|
   |       code, state, iss                |
   |                                       |
   |  Validate: state matches, iss matches |
   |  discovered issuer URI                |
   |                                       |
   |-- (4) Token Request ----------------->

|
   |       grant_type=authorization_code   |
   |       code, redirect_uri              |
   |       code_verifier                   |
   |       client auth (per advertised     |
   |       token_endpoint_auth_method)     |
   |                                       |
   |<-- (5) Token Response ----------------|
   |       access_token, refresh_token     |
   |       token_type=Bearer, scope        |
```

**Etapa 2 — Conjunto de escopo:** As plataformas derivam o escopo de autorização definido do
mapa `config.scopes` da empresa (consulte [Derivação do escopo](#derivacao-do-escopo)).
As plataformas **DEVEM** solicitar apenas o conjunto de escopo derivado – não um superconjunto.

**Etapa 3 — Validação:** A plataforma **DEVE** verificar se o `state`
parâmetro corresponde ao valor enviado no passo 2, e que o parâmetro `iss`
corresponde ao URI `issuer` do servidor de autorização a partir dos metadados descobertos.
Se alguma das verificações falhar, a plataforma **DEVE** descartar a autorização
resposta.

**Etapa 4 — PKCE:** O `code_verifier` **DEVE** corresponder ao
`code_challenge` enviado na etapa 2. As empresas **DEVEM** rejeitar solicitações de token
onde `code_verifier` está ausente ou não é verificado em relação ao armazenado
`code_challenge`.

## Provedores de identidade

O mapa `config.providers` declara provedores de identidade externos confiáveis
a partir do qual a empresa aceitará identidade encadeada por meio do portador JWT
asserções para o [fluxo IdP acelerado](#fluxo-de-idp-acelerado). Cada
chave identifica um namespace de IdP e mapeia para uma matriz de entradas
de mecanismo — um IdP **PODE** oferecer vários mecanismos de aquisição de tokens
sob uma única chave. O mapa consiste em metadados aditivos no topo do
caminho OAuth direto sempre disponível no domínio comercial (consulte
[Descoberta](#descoberta)); para o caminho de encadeamento, é uma lista de
permissões fechada — uma empresa **DEVE** rejeitar uma concessão de autorização JWT
cujo `iss` não corresponde a uma entrada de mecanismo `oauth2` listada (consulte
[Emissão de token comercial](#emissao-de-token-comercial)).

* **Quando ausente ou vazio:** as plataformas executam OAuth direto no
    domínio comercial por meio de [Descoberta](#descoberta).
* **Quando presente:** plataformas **PODEM** selecionar uma entrada de mecanismo cujo
    `type` elas suportam e encadeiam a identidade através do
    [Fluxo IdP acelerado](#fluxo-de-idp-acelerado) — normalmente uma
    pertencente a um IdP para o qual elas já possuem um token upstream válido.
    Se nenhum mecanismo listado for compatível ou adequado, as plataformas **DEVEM**
    voltar para o OAuth direto no domínio comercial.
* **Auto-listagem proibida.** As empresas **NÃO DEVEM** listar seu próprio
    servidor de autorização em `config.providers`. Encadear-se a si mesma é
    degenerado (o mesmo servidor emitiria e validaria a asserção),
    e o OAuth direto já está disponível via [Descoberta](#descoberta).
    As plataformas **DEVEM** ignorar qualquer entrada do mecanismo `oauth2` cuja
    `auth_url` corresponde ao URI do emissor da própria empresa.

### Configuração do provedor

Cada chave em `config.providers` é um identificador de domínio reverso para um
namespace de IdP; seu valor é uma matriz de entradas de mecanismo.

Uma chave de provedor é um **identificador** de domínio reverso, não uma entidade portadora de esquema:
ela não declara nenhuma URL `schema`, então a
[Vinculação de Autoridade](overview.md#vinculacao-de-autoridade) (que vincula a URL
`schema` de uma entidade à sua autoridade de namespace) não se aplica aqui. A âncora
de confiança de um provedor é seu `auth_url`, regido pelas regras de descoberta abaixo;
vincular o `auth_url` à autoridade de namespace do provedor é um possível fortalecimento
futuro, rastreado separadamente.

Cada entrada é descrita pelo seu `type`:

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `type` | string aberta | Sim | Discriminador de mecanismo de provedor. `oauth2` é o único tipo definido nesta versão; versões futuras **PODEM** definir tipos adicionais como extensões ininterruptas. |
| `auth_url` | URI | Sim, para `oauth2` | URL base para descoberta de metadados do servidor de autorização. |
| `required_claims` | matriz de strings | Não, para `oauth2` | Nomes de declaração do OIDC Core §5.1 que a empresa exige na concessão de autorização JWT (por exemplo, `email`). Dica opcional de pré-filtro — consulte [Seleção de provedor](#selecao-de-provedor). |

O valor `type` é uma string aberta, não uma enumeração fechada. As plataformas
**DEVEM** tratar as entradas do provedor cujo `type` elas não suportam como filtradas
(consulte [Seleção de Provedor](#selecao-de-provedor)) em vez de rejeitar a
configuração do negócio.

Para provedores `oauth2`, as plataformas **DEVEM** descobrir o servidor de autorização
metadados de `auth_url` usando a mesma hierarquia de metadados de duas camadas que
[Discovery](#descoberta) Etapa 2 (RFC 8414 primário com inserção de caminho §3.1,
Fallback do OIDC somente em 404), tratando `auth_url` como o emissor. O
a etapa de recurso protegido não se aplica — `auth_url` já é o IdP
emissor - e a empresa valida o `iss` da concessão JWT contra ele por
[Emissão de token comercial](#emissao-de-token-comercial).

### Seleção de Provedor

As plataformas iteram sobre os pares `(provider key, mechanism entry)` no
mapa `config.providers` da empresa e selecionam uma entrada compatível
— normalmente uma pertencente a um IdP que já possui um token upstream
válido — para ativar o [Fluxo IdP Acelerado](#fluxo-de-idp-acelerado).
As entradas do mecanismo sob a mesma chave de provedor são alternativas; uma
plataforma pode corresponder a qualquer uma delas.

O `type` de um mecanismo determina se ele participa do modelo de token
e de escopo. O tipo `oauth2` encadeia identidade via troca de token
e contribui para os escopos do token emitido pela empresa. Outros tipos
**PODEM** não contribuir com escopos — a presença em `providers` não implica
participação no escopo ou modelo de emissão de tokens. A seleção é ativada
se a plataforma *suporta* o `type` de um mecanismo e mantém (ou pode
obter) uma identidade upstream adequada, independentemente de esse tipo
emitir um token.

Quando uma entrada de mecanismo declara `required_claims`, as plataformas **DEVEM**
filtrar essa entrada durante a seleção se a identidade upstream delas não tiver
nenhum dos nomes de declaração listados (por exemplo, se o token upstream não
carregar `email`). Isso evita uma tentativa de encadeamento desperdiçada que seria
rejeitada no endpoint do token. A aplicação reativa continua obrigatória (ver
[Encadeando erros no endpoint do token](#erros-de-encadeamento-no-endpoint-do-token))
porque nem toda empresa irá declarar `required_claims`, e a dica
expressa apenas a presença da reivindicação - restrições de valor (por exemplo, exigindo
`email_verified=true`) são aplicadas de forma reativa.

### Exemplo de perfil

Uma empresa que confia em um IdP externo para encadeamento, ao mesmo tempo que aceita
fluxos OAuth diretos (sempre disponíveis via descoberta):

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {},
    "capabilities": {
      "br.dev.bcp.common.identity_linking": [{
        "version": "{{ bcp_schema_version }}",
        "spec": "https://bcp.dev.br/specification/identity-linking",
        "schema": "https://bcp.dev.br/schemas/common/identity_linking.json",
        "config": {
          "providers": {
            "app.example.login": [
              {
                "type": "oauth2",
                "auth_url": "https://accounts.example-login.app/",
                "required_claims": ["email"]
              }
            ]
          },
          "scopes": {
            "br.dev.bcp.shopping.order:read":   {},
            "br.dev.bcp.shopping.order:manage": {}
          }
        }
      }]
    },
    "payment_handlers": {}
  }
}
```

A plataforma poderá utilizar o Fluxo IdP Acelerado com `app.example.login` se
já contém um token válido; caso contrário, ele executa o padrão
[Fluxo de vinculação de conta](#fluxo-de-vinculacao-de-contas) em relação ao domínio comercial
via [Descoberta](#descoberta).

## Fluxo de IdP acelerado

Depois que uma plataforma vincula a identidade do usuário a um IdP confiável, ela pode
encadear essa identidade para novos negócios sem redirecionamento de navegador: a
plataforma obtém uma **concessão de autorização JWT** do IdP e a apresenta
ao endpoint do token da empresa. A empresa valida a concessão e emite
seu próprio token de acesso sob sua própria autoridade.

Este fluxo traça o perfil do padrão de encadeamento de identidade e autorização em
[draft-ietf-oauth-identity-chaining](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-chaining-08){ target="_blank" }.
O BCP restringe a concessão de autorização JWT além do que as RFCs de base
exigem: `aud` **DEVE** ser um URI de valor único mais um `jti` exclusivo (consulte
[Concessão de autorização JWT](#concessao-de-autorizacao-jwt)).

### Fluxo

1. A plataforma descobre `config.providers` na capacidade de vinculação de
   identidade do negócio e seleciona um provedor para o qual já possui um token válido.
2. A plataforma solicita uma concessão de autorização JWT do IdP via token
   troca ([RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693){ target="_blank" })
   no ponto final do token do IdP:
    * `grant_type`: `urn:ietf:params:oauth:grant-type:token-exchange`
    * `subject_token`: token de acesso IdP existente da plataforma
    * `subject_token_type`: `urn:ietf:params:oauth:token-type:access_token`
    * `resource` e/ou `audience`: URI do emissor do servidor de autorização do
      negócio. As plataformas **DEVEM** incluir pelo menos um.
      [RFC 8693 §2.1](https://datatracker.ietf.org/doc/html/rfc8693#section-2.1){ target="_blank" }
      permite valores de URI em qualquer parâmetro; as implementações de IdP variam
      quanto ao que aceitam. O IdP mapeia o valor para a declaração `aud`
      na concessão resultante; quando ambos são enviados, eles **DEVEM** carregar
      valores idênticos.
    * `requested_token_type`: `urn:ietf:params:oauth:token-type:jwt`
3. O IdP valida o token em questão, verifica se a plataforma está autorizada
   a solicitar uma concessão para a empresa-alvo e retorna uma Concessão de
   autorização JWT de curta duração, com `issued_token_type` definido como
   `urn:ietf:params:oauth:token-type:jwt`.
4. A plataforma apresenta a concessão ao endpoint do token da empresa por meio do JWT
   concessão de declaração ao portador
   ([RFC 7523](https://datatracker.ietf.org/doc/html/rfc7523){ target="_blank" }):
    * `grant_type`: `urn:ietf:params:oauth:grant-type:jwt-bearer`
    * `assertion`: a concessão de autorização JWT
    * `scope`: o conjunto de escopo derivado (veja [Derivação de escopo](#derivacao-do-escopo))
5. A empresa valida a concessão, resolve a identidade do usuário e emite
   um token de acesso sob sua própria autoridade.
6. A plataforma usa o token emitido pela empresa via `Authorization: Bearer <access_token>`
   em solicitações subsequentes.

A plataforma **NÃO DEVE** apresentar um token IdP bruto diretamente para uma empresa.
O encadeamento de identidades garante que cada empresa emita tokens sob sua própria autoridade
com a política correta de vinculação de público e escopo.

### Concessão de autorização JWT

A concessão de autorização JWT é um JWT assinado
([RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519){ target="_blank" })
emitido pelo IdP que afirma a identidade do usuário para uso com um determinado
negócio. **Não** é um token de acesso — é uma credencial de curta duração que a
plataforma apresenta ao servidor de autorização da empresa para obter um.

A concessão **DEVE** estar em conformidade com
[RFC 7523 §3](https://datatracker.ietf.org/doc/html/rfc7523#section-3){ target="_blank" },
com duas restrições específicas do BCP:

* `aud` **DEVE** ser um valor único (o URI do emissor AS da empresa), não um
  array – o encadeamento visa um negócio por concessão.
* `jti` **DEVE** estar presente (RFC 7523 diz apenas MAY) para que as empresas possam aplicar
  proteção de reprodução de uso único (consulte [Considerações de segurança](#consideracoes-de-seguranca)).

`exp` **DEVE** não exceder 60 segundos após `iat`. O IdP **PODE**
incluem declarações adicionais para transmitir o contexto de autorização (registros de consentimento,
atributos do usuário, etc.).

### Emissão de token comercial

Ao receber uma concessão de autorização JWT em seu terminal de token, o
o servidor de autorização da empresa **DEVE** validar a afirmação por
[RFC 7523 §3](https://datatracker.ietf.org/doc/html/rfc7523#section-3){ target="_blank" },
com os seguintes requisitos específicos do BCP:

* `iss` **DEVE** corresponder ao `auth_url` de uma entrada do mecanismo `oauth2`
  listado em `config.providers`.
* `aud` **DEVE** corresponder exatamente ao URI do emissor AS da empresa.
* A assinatura JWT **DEVE** ser verificada em relação ao `jwks_uri` do IdP; se
  JWKS não pode ser recuperado, o negócio **DEVE** falhar no fechamento.

Depois que a asserção é validada, a empresa resolve o usuário a partir de
`sub` (provisionamento automático permitido) e emite um token de acesso com escopo para
o subconjunto de escopos solicitados cuja política por escopo é atendida pelas
reivindicações da concessão (`acr`, `auth_time`, `amr`, etc.). Se nenhum
escopo solicitado puder ser satisfeito, a empresa **DEVE** devolver `invalid_scope`
por [RFC 6749 §5.2](https://datatracker.ietf.org/doc/html/rfc6749#section-5.2){ target="_blank" };
as plataformas se recuperam solicitando uma concessão intensificada do IdP ou executando
OAuth direto. Se a interação do usuário for necessária (aceitação dos termos,
integração), a empresa **DEVE** rejeitar a concessão com `invalid_grant`
(consulte [Erros de encadeamento no endpoint do token](#erros-de-encadeamento-no-endpoint-do-token));
as plataformas se recuperam executando o [Fluxo de vinculação de conta](#fluxo-de-vinculacao-de-contas)
contra um provedor interativo.

**Reivindicações para resolução do usuário.** Além de `sub`, as empresas geralmente
precisam de reivindicações adicionais para provisionar uma nova conta com um
identificador de contato utilizável, ou para exibir dicas de experiência do usuário
quando uma conta existente pode corresponder.
A chave de identidade estável por IdP é `(iss, sub)`. Para provedores
`oauth2`, os IdPs **DEVEM** incluir
[Declarações padrão do OIDC Core §5.1](https://openid.net/specs/openid-connect-core-1_0-31.html#StandardClaims){ target="_blank" }
— particularmente `email` e `email_verified` — na concessão de autorização JWT
quando disponível e o usuário tiver consentido. As empresas
**NÃO DEVEM** vincular automaticamente contas entre IdPs por e-mail correspondente ou
qualquer outra reivindicação, e **DEVEM** exigir vinculação mediada pelo usuário
(o usuário se autentica na conta existente) antes de mesclar identidades. Veja
[Considerações de segurança](#consideracoes-de-seguranca).

### Erros de encadeamento no endpoint do token

As falhas de validação usam o formato de erro de token-endpoint padrão do OAuth 2.0
([RFC 6749 §5.2](https://datatracker.ietf.org/doc/html/rfc6749#section-5.2){ target="_blank" }).
Falhas específicas da concessão JWT (assinatura, repetição de `iss`, `aud`, `exp`, `jti`,
provedor não reconhecido, interação do usuário necessária) mapeiam para `invalid_grant`
de acordo com [RFC 7523 §3.1](https://datatracker.ietf.org/doc/html/rfc7523#section-3.1){ target="_blank" }.
As empresas **PODEM** incluir `error_description` e `error_uri` para ajudar no
diagnóstico ou apontar documentação de integração; as plataformas **NÃO DEVEM**
tratar `error_description` como legível por máquina.

**Declarações ausentes ou insuficientes.** Quando a concessão de autorização JWT
não possui uma reivindicação exigida pela empresa (por exemplo, `email` para
resolução de conta), o negócio **DEVE** rejeitar com `invalid_grant`. A
empresa **PODE** incluir `error_description` nomeando a reivindicação ausente
para diagnóstico humano (por exemplo, `"missing required claim: email"`); as plataformas
**NÃO DEVEM** analisá-lo para recuperação automatizada e **DEVEM** recorrer
ao OAuth direto, onde a empresa pode solicitar ao usuário a informação ausente.
As empresas **DEVEM** anunciar os requisitos de reivindicação padrão
via `required_claims` (ver
[Configuração do provedor](#configuracao-do-provedor)) para que as plataformas possam
pré-filtrar; requisitos além do OIDC Core §5.1 **DEVEM** ser documentados
em materiais voltados para o desenvolvedor.

### Ciclo de vida do token

As concessões de asserção do portador JWT não estabelecem sessões de longa duração:
as empresas **NÃO DEVEM** emitir tokens de atualização em resposta, uma vez que
sobreviveria à sessão do IdP e concederia acesso continuado após o usuário
revoga o relacionamento do IdP
([draft-ietf-oauth-identity-chaining §5.4](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-identity-chaining-08#section-5.4){ target="_blank" }).
Quando um token emitido pela empresa expira, a plataforma obtém uma nova
concessão JWT do IdP e a apresenta novamente.

A revogação não se propaga pela cadeia. Ao desvincular, as plataformas
**DEVEM** chamar o endpoint de revogação
([RFC 7009](https://datatracker.ietf.org/doc/html/rfc7009){ target="_blank" })
em *ambas* as camadas — o IdP e o negócio.

## Requisitos de IdP

Os requisitos desta seção se aplicam a provedores de identidade de
`type: oauth2`. Outros tipos de provedores definem sua própria descoberta e
requisitos de apresentação de prova (consulte [Extensibilidade futura](#extensibilidade-futura)).

Provedores de identidade de `type: oauth2` listados em `config.providers` **DEVEM**
publicar metadados do servidor de autorização via
[RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }
ou OpenID Connect Discovery. Os metadados **DEVEM** incluir:

* `revocation_endpoint` — para suportar a revogação de token de acordo com o
    Seção [Ciclo de vida do token](#ciclo-de-vida-do-token).
* `jwks_uri` — para que as empresas possam verificar a assinatura na autorização JWT
    subvenções emitidas pelo IdP.
* `urn:ietf:params:oauth:grant-type:token-exchange` em `grant_types_supported`
    — para ativar o fluxo IdP acelerado.

Ao processar solicitações de troca de token para concessões de autorização JWT,
o IdP **DEVE**:

* Autenticar a plataforma e verificar se ela está autorizada a apresentar o
    token de sujeito
    ([RFC 8693 §2.1](https://datatracker.ietf.org/doc/html/rfc8693#section-2.1){ target="_blank" }).
* Verificar que o negócio-alvo (identificado por `resource` e/ou `audience`,
    que **DEVE** carregar valores idênticos quando ambos são enviados - consulte
    [Fluxo](#fluxo)) é uma parte confiável conhecida e que o usuário autorizou o
    compartilhamento de identidade com ele. O IdP **NÃO DEVE** emitir concessões para
    empresas que o usuário não autorizou.
* Emitir uma concessão de autorização JWT em conformidade com os
    requisitos de [Concessão de autorização JWT](#concessao-de-autorizacao-jwt).
* Retornar `issued_token_type` como `urn:ietf:params:oauth:token-type:jwt`.

Os IdPs **DEVEM** preencher as declarações padrão do OIDC Core §5.1 nas
concessões de autorização JWT quando o usuário consentiu em compartilhá-las — no
mínimo `email` e `email_verified` quando aplicável — para apoiar o
provisionamento de contas e dicas de UX para o negócio. As reivindicações padrão
são consultivas; a identificação estável por IdP permanece `(iss, sub)`.

## Escopos

Os escopos definem as permissões autenticadas pelo usuário que uma empresa concede a
uma plataforma. As empresas declaram os escopos que oferecem em `config.scopes` de
sua entrada `br.dev.bcp.common.identity_linking`. Cada chave é a string do escopo OAuth como
aparece no fio (`{capability}:{scope}`, por ex.
`br.dev.bcp.shopping.order:read`); cada valor é um objeto de política por escopo.

Listar um escopo em `config.scopes` declara que as operações correspondentes
exigem um token de identidade do usuário. Operações *não* controladas por qualquer
escopo listado operam em qualquer nível de acesso que a empresa permita - público,
autenticado pelo agente ou não. A empresa define a política de acesso
para operações fora do escopo; o BCP não prescreve um padrão.

### Formato do token de escopo

Os tokens de escopo seguem a convenção `{capability-name}:{scope-name}`:

* `br.dev.bcp.shopping.order:read`
* `br.dev.bcp.shopping.order:manage`
* `br.dev.bcp.shopping.checkout:manage`

O nome da capacidade usa a nomenclatura DNS reversa do BCP. O nome do escopo denota
a **permissão** sendo concedida - normalmente um grupo de operação em um
recurso (`read`, `manage`, `write`) ou uma operação de ponto de entrada (`create`)
definido pela especificação de cada capacidade.

Os nomes dos escopos **DEVEM** corresponder ao padrão `^[a-z][a-z0-9_]*$`. Capacidades
de terceiros seguem a mesma convenção usando seu próprio nome DNS reverso:
`com.example.loyalty:points`.

A especificação de cada recurso define seus escopos **bem conhecidos** — o
conjunto padrão que as plataformas esperam. As empresas **PODEM** declarar escopos
**personalizados** adicionais seguindo a mesma convenção para bloquear operações em
granularidade mais fina (por exemplo, para bloquear `complete` independentemente do
escopo bem conhecido `br.dev.bcp.shopping.checkout:manage`, ou exigir autenticação
elevada para compras de alto valor). As plataformas **DEVEM** tratar qualquer
escopo listado em `config.scopes` — bem conhecido ou personalizado — como controlando
suas operações atrás da autenticação do usuário.

### Política e metadados por escopo

O valor de cada escopo é um objeto aberto que carrega políticas por escopo e
metadados. `{}` vazio significa "autenticação do usuário necessária, nada mais". Campos
possíveis incluem restrições de autenticação (`min_acr`, `max_token_age`,
`require_mfa`), metadados declarativos (`claims` produzidos quando concedidos),
ou outra configuração específica do escopo. As plataformas **DEVEM** ignorar
campos não reconhecidos.

Os escopos anunciados **DEVEM** aplicar-se uniformemente em todos os caminhos de identidade. O
mesmo mapa `config.scopes` rege a disponibilidade do escopo, quer a plataforma tenha
obtido a identidade do usuário via OAuth direto, quer via o
[Fluxo IdP acelerado](#fluxo-de-idp-acelerado). A política por escopo determina
quais asserções satisfazem um escopo; empresas que aplicam `min_acr` (por
exemplo) **DEVEM** impor o mesmo limite, independentemente do caminho.

#### `description`

Descrição opcional legível por humanos do escopo que as plataformas podem usar
apresentar e explicar o contexto (requisito e valor) ao usuário.

<!-- ucp:example schema=common/identity_linking def=scope_policy -->
```json
{
  "description": {
    "plain": "Manage your orders: cancel, return, or modify post-purchase.",
    "markdown": "**Manage your orders**: cancel, return, or modify post-purchase."
  }
}
```

As empresas **DEVEM** fornecer uma descrição para cada escopo que declaram.
As plataformas **PODEM** exibir o texto para informar seu próprio consentimento UX.

### Derivação do Escopo

As plataformas derivam o escopo de autorização definido a partir do `config.scopes`
do negócio antes de iniciar o fluxo de vinculação de contas:

1. Ler `config.scopes` da entrada de capacidade `br.dev.bcp.common.identity_linking`
   da empresa.
2. Filtrar para escopos cujo prefixo de capacidade esteja no conjunto de
   capacidade negociado — ignorando os escopos dos recursos que a plataforma não suporta.
3. Do conjunto restante, selecionar os escopos que a plataforma pretende usar
   (informado por quais operações planeja chamar; consulte as especificações de cada recurso
   para mapeamentos de operação para escopo).
4. Aplicar a política por escopo de cada escopo selecionado ao construir a
   solicitação de autorização.

Se nenhum escopo for necessário para as operações que a plataforma pretende chamar, a
plataforma pode pular o fluxo de vinculação de identidade – as operações funcionam com acesso
público ou autenticado pelo agente. No entanto, a vinculação ainda pode ser benéfica para
desbloquear personalização nativa da sessão (endereços salvos, preços para membros,
visibilidade do histórico de pedidos, etc.); o comerciante resolve isso a partir do
contexto autenticado do usuário, independentemente de quais escopos foram concedidos.

### Apresentação de consentimento

As telas de consentimento são renderizadas pelo servidor de autorização da empresa. Esta
especificação não define strings de descrição de escopo — o servidor de autorização
é responsável por apresentar texto de consentimento legível para os
escopos que suporta. As telas de consentimento **DEVEM** agrupar escopos relacionados
de forma inteligível, em vez de listar operações individuais: por exemplo, "Permitir que
[plataforma] visualize seu histórico de pedidos" em vez de "conceder
`br.dev.bcp.shopping.order:read`."

## Tratamento de erros

### `identity_required`

Quando uma operação é controlada por um escopo listado em `config.scopes` e o
a solicitação chega com um usuário ausente, expirado, inválido ou não verificável
token de identidade, a empresa **DEVE** retornar:

* HTTP `401 Unauthorized`
* Um cabeçalho de desafio `WWW-Authenticate: Bearer` por
    [RFC 6750 §3](https://datatracker.ietf.org/doc/html/rfc6750#section-3){ target="_blank" }
* Um corpo de resposta de erro BCP contendo uma mensagem com
    `code: "identity_required"`

O cabeçalho `WWW-Authenticate` **DEVE** incluir um parâmetro `realm` definido como
o URI do emissor da empresa conforme declarado em
[RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }
metadados. Quando a solicitação incluía um token, mas ele era inválido, expirou ou
não verificável, o cabeçalho **DEVE** também incluir `error="invalid_token"` e
**PODE** incluir `error_description` conforme RFC 6750 §3. Quando nenhum token foi
apresentado, o parâmetro `error` **DEVE** ser omitido (RFC 6750 §3.1).

O cabeçalho **DEVE** incluir um parâmetro `resource_metadata`
([RFC 9728 §5.1](https://datatracker.ietf.org/doc/html/rfc9728#section-5.1){ target="_blank" })
apontando para o documento de metadados de recursos protegidos
(`/.well-known/oauth-protected-resource`).

A empresa **PODE** incluir um `continue_url` no corpo da resposta para
**fluxos de integração não OAuth** (por exemplo, criação de conta, aceitação de termos)
onde o usuário deve concluir uma etapa hospedada antes de autenticar novamente.
`continue_url` **NÃO DEVE** ser usado para transmitir um OAuth pré-preparado
solicitação de autorização; a plataforma constrói sua própria autorização
solicitação do desafio `WWW-Authenticate` e metadados descobertos,
incluindo valores PKCE, `state` e `redirect_uri` que possui.

**Nenhum token apresentado** (primeira solicitação para uma operação fechada — `error` omitido de acordo com RFC 6750 §3.1):

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="https://merchant.example.com",
                  resource_metadata="https://merchant.example.com/.well-known/oauth-protected-resource"
Content-Type: application/json

{
  "messages": [
    {
      "type": "error",
      "code": "identity_required",
      "content": "User identity is required to access order history.",
      "severity": "requires_buyer_review"
    }
  ]
}
```

**Token presente, mas inválido ou expirado** (`error="invalid_token"` incluído de acordo com RFC 6750 §3):

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="https://merchant.example.com",
                  error="invalid_token",
                  error_description="The access token expired",
                  resource_metadata="https://merchant.example.com/.well-known/oauth-protected-resource"
Content-Type: application/json

{
  "messages": [
    {
      "type": "error",
      "code": "identity_required",
      "content": "User identity is required to access order history.",
      "severity": "requires_buyer_review"
    }
  ]
}
```

### `insufficient_scope`

Quando uma solicitação chega com um token de identidade de usuário válido, mas o token
não tem um escopo exigido pela operação (ou falha em uma política de nível de escopo
como `min_acr` ou `max_token_age`), a empresa **DEVE** retornar:

* HTTP `403 Forbidden`
* Um cabeçalho de desafio `WWW-Authenticate: Bearer` de acordo com RFC 6750 §3
* Um corpo de resposta de erro BCP contendo uma mensagem com
    `code: "insufficient_scope"`

O cabeçalho `WWW-Authenticate` **DEVE** incluir:

* `realm="<business issuer URI>"`
* `error="insufficient_scope"`
* `scope="<space-separated full required scope set for the operation>"`

e **DEVE** incluir um parâmetro `resource_metadata` apontando para o
documento de metadados de recursos protegidos (RFC 9728).

O parâmetro `scope` **DEVE** listar o conjunto **completo** de escopos necessários
para a operação, não apenas os ausentes. A plataforma compara o
conjunto completo em relação aos escopos já concedidos em seu token atual e usa
autorização incremental para solicitar apenas os escopos que ainda não possui,
evitando solicitações de consentimento redundantes para escopos que o usuário já
aprovou.

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer realm="https://merchant.example.com",
                  error="insufficient_scope",
                  scope="br.dev.bcp.shopping.order:read br.dev.bcp.shopping.order:manage",
                  resource_metadata="https://merchant.example.com/.well-known/oauth-protected-resource"
Content-Type: application/json

{
  "messages": [
    {
      "type": "error",
      "code": "insufficient_scope",
      "content": "This operation requires scopes: br.dev.bcp.shopping.order:read, br.dev.bcp.shopping.order:manage",
      "severity": "requires_buyer_review"
    }
  ]
}
```

> **Nota:** `identity_required` e `insufficient_scope` são intencionalmente
> distintos. As plataformas **NÃO DEVEM** reagir a uma resposta `insufficient_scope`
> reiniciando um novo fluxo de vinculação de conta — em vez disso, elas **DEVEM** solicitar
> apenas o(s) escopo(s) ausente(s) por meio de autorização incremental, para preservar
> escopos concedidos anteriormente.

## Autenticação Opcional

Um mecanismo para a **empresa** sinalizar para a **plataforma** que
a autenticação está disponível e forneceria valor no contexto atual,
mesmo que a operação tenha sido bem-sucedida sem ela. A plataforma poderá então apresentar
este sinal ao usuário.

### `identity_optional`

As empresas **DEVEM** incluir este código informativo nas
respostas quando a autenticação estiver disponível e puder desbloquear
significativamente capacidades adicionais no contexto atual. O `content`
transmite o prompt de valor do negócio para a plataforma (por exemplo,
"Inscreva-se para obter preços para membros e resultados personalizados.").

<!-- ucp:example schema=shopping/checkout extract=$.messages target=$.messages -->
```json
{
  "messages": [
    {
      "type": "info",
      "code": "identity_optional",
      "content": "Sign in for member pricing and personalized results."
    }
  ]
}
```

## Considerações de segurança

* **PKCE.** PKCE (`S256`) é NECESSÁRIO para todos os fluxos de código de autorização.
  PKCE simples (`plain`) **NÃO DEVE** ser usado. As empresas **DEVEM** rejeitar
  trocas de códigos de autorização sem um `code_verifier` válido.
* **Autenticação de cliente.** As empresas negociam a autenticação de cliente via
  `token_endpoint_auth_methods_supported`
  ([RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }).
  Clientes confidenciais **DEVEM** preferir métodos assimétricos
  (`private_key_jwt`, `tls_client_auth`) sobre `client_secret_basic` para
  eliminar o risco de vazamento de segredo compartilhado. Clientes públicos (nativos, desktop e
  agentes no dispositivo por
  [RFC 8252 §8.5](https://datatracker.ietf.org/doc/html/rfc8252#section-8.5){ target="_blank" })
  não podem manter um `client_secret` confidencial e **DEVEM** usar `none`; para
  esses clientes, PKCE com `S256` é a prova de posse que
  autentica a concessão de autorização. As empresas **NÃO DEVEM** exigir
  `client_secret_basic` como único método ao atender plataformas nativas
  ou de agente.
* **Prevenção de ataques mistos.** As plataformas **DEVEM** validar o `iss`
  parâmetro na resposta de autorização
  ([RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207){ target="_blank" }).
  As empresas **DEVEM**
  retornar `iss` em cada resposta de autorização. Sem validação de `iss`,
  um invasor que controla um servidor de autorização pode redirecionar um
  código de autorização da vítima para um servidor diferente.
* **Desafios de autenticação.** As empresas **DEVEM** emitir
  desafios `WWW-Authenticate: Bearer` por
  [RFC 6750 §3](https://datatracker.ietf.org/doc/html/rfc6750#section-3){ target="_blank" }
  nas respostas `401` e `403` para operações autenticadas pelo usuário. As plataformas
  **DEVEM** processar os parâmetros estruturados `scope` e `error` para acionar
  decisões de fluxo de autorização; `error_description` é apenas uma dica legível
  por humanos e **NÃO DEVE** ser usado para decisões de controle de fluxo. O
  parâmetro `realm` **DEVE** corresponder ao URI do emissor da empresa para que as plataformas
  possam correlacionar o desafio com o servidor de autorização correto.
* **Exatidão de `redirect_uri`.** As empresas **DEVEM** impor a correspondência exata
  de string para `redirect_uri`. Implementações de correspondência parcial ou de prefixo
  são uma fonte comum de vulnerabilidades de redirecionamento aberto e roubo de token.
* **Exatidão de `issuer`.** O valor `issuer` nos metadados RFC 8414 e o
  parâmetro `iss` nas respostas de autorização **DEVEM** ser idênticos
  (byte por byte). As plataformas **NÃO DEVEM** normalizar antes da comparação.
  A normalização (por exemplo, remoção de barras finais) é uma fonte conhecida de
  Bypass de validação `iss`.
* **Segurança no transporte.** Toda a comunicação entre a plataforma e o negócio
  **DEVE** usar HTTPS com no mínimo TLS 1.2
  ([RFC 6749 §1.6](https://datatracker.ietf.org/doc/html/rfc6749#section-1.6){ target="_blank" }).
* **`scopes_supported`.** As empresas **DEVEM** preencher `scopes_supported` em
  Metadados RFC 8414. As plataformas **DEVEM** verificar se o conjunto de escopo derivado é
  um subconjunto de `scopes_supported` antes de iniciar o fluxo de autorização, para
  falhar rapidamente em incompatibilidades de escopo, em vez de na tela de consentimento.
* **Revogação de token.** As plataformas **DEVEM** revogar tokens de identidade do usuário no
  ponto de extremidade de revogação da empresa (RFC 7009) quando um usuário desvincula sua conta.
  As empresas **DEVEM** rejeitar solicitações subsequentes que apresentem tokens revogados.
* **Vida útil da concessão JWT.** As concessões de autorização JWT **DEVEM** ter vida curta;
  a declaração `exp` **DEVE** não ser superior a 60 segundos após `iat`. Vidas
  curtas limitam a janela para roubo e repetição de concessões.
* **Uso único da concessão JWT.** As empresas **DEVEM** impor o uso único das
  concessões de autorização JWT rastreando a reivindicação `jti` dentro da janela de
  validade da concessão; uma vida curta estreita a janela de repetição, mas apenas
  o rastreamento do `jti` a fecha.

* **Retransmissão de concessões.** As empresas **NÃO DEVEM** armazenar ou encaminhar
  concessões de autorização JWT recebidas de plataformas. As concessões são credenciais
  ao portador com escopo para um único público (`aud`) e um único uso.
* **Vinculação de contas entre IdPs.** A federação reduz os limites de confiança:
  uma empresa que vincula automaticamente contas de provedores listados com base em
  qualquer reivindicação declarada pelo IdP (e-mail, telefone, nome) estende o
  processo de verificação do IdP para um risco de tomada de conta. Um provedor que
  emite `email_verified=true` para um e-mail que o usuário não controla
  pode sequestrar qualquer conta da empresa que compartilha esse e-mail. O
  identificador estável por IdP é `(iss, sub)`; outras reivindicações são consultivas.
  As empresas **DEVEM** exigir vinculação mediada pelo usuário — o usuário
  demonstrando controle da conta existente por meio da autenticação da sessão
  atual ou equivalente — antes de mesclar contas entre IdPs.

## Extensibilidade Futura

O esquema foi projetado para acomodar mecanismos de provedores não OAuth como
extensões inquebráveis. O discriminador `provider.type` é obrigatório, uma
string aberta: `oauth2` é o único tipo definido nesta versão, e o esquema
reserva espaço para tipos futuros – atestado de carteira, credenciais
verificáveis ou outros protocolos de prova de identidade. Versões futuras
poderão definir valores `type` adicionais, com sua própria mecânica de
descoberta e apresentação de provas.

**Regra de compatibilidade futura para plataformas:** Quando `config` contém campos
não definidos nesta versão da especificação, as plataformas **DEVEM** ignorar esses
campos. As plataformas **DEVEM** tratar as entradas do provedor com um valor não suportado
de `type` como filtradas e, em seguida, aplicar as regras em
[Provedores de identidade](#provedores-de-identidade) para o que resta.

## Exemplos

### Metadados do servidor de autorização

Exemplo de metadados hospedados em `/.well-known/oauth-authorization-server` por
[RFC 8414](https://datatracker.ietf.org/doc/html/rfc8414){ target="_blank" }:

<!-- ucp:example skip reason="OAuth metadata, not BCP payload" -->
```json
{
  "issuer": "https://merchant.example.com",
  "authorization_endpoint": "https://merchant.example.com/oauth2/authorize",
  "token_endpoint": "https://merchant.example.com/oauth2/token",
  "revocation_endpoint": "https://merchant.example.com/oauth2/revoke",
  "jwks_uri": "https://merchant.example.com/oauth2/jwks",
  "scopes_supported": [
    "br.dev.bcp.shopping.order:read",
    "br.dev.bcp.shopping.order:manage"
  ],
  "response_types_supported": ["code"],
  "grant_types_supported": [
    "authorization_code",
    "refresh_token",
    "urn:ietf:params:oauth:grant-type:jwt-bearer"
  ],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": [
    "private_key_jwt",
    "tls_client_auth",
    "client_secret_basic",
    "none"
  ],
  "authorization_response_iss_parameter_supported": true,
  "service_documentation": "https://merchant.example.com/docs/oauth2"
}
```

Nota: `authorization_response_iss_parameter_supported: true` anuncia
suporte a [RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207){ target="_blank" }. `code_challenge_methods_supported: ["S256"]` sinaliza PKCE.
Ambos **DEVEM** estar presentes em metadados compatíveis com BCP. O
tipo de concessão `urn:ietf:params:oauth:grant-type:jwt-bearer` indica que
a empresa aceita concessões de autorização JWT de IdPs confiáveis por meio do
[Fluxo IdP acelerado](#fluxo-de-idp-acelerado).

`token_endpoint_auth_methods_supported` lista todos os métodos que o negócio
aceita. O exemplo anuncia métodos assimétricos (`private_key_jwt`,
`tls_client_auth`) para clientes confidenciais, `client_secret_basic` para
compatibilidade legada e `none` para clientes públicos (nativos, desktop e
agentes no dispositivo por
[RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252){ target="_blank" });
quando `none` é anunciado, é necessário PKCE com `S256`. Negócios que
não atendem clientes públicos **PODEM** omitir `none`.

### Perfil Empresarial (`/.well-known/bcp`)

O formato de `config.scopes` reflete a política do negócio.

#### Varejista B2C

Catálogo público, checkout como convidado (sem necessidade de escopo), operações
de pedido controladas por vinculação ao usuário:

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {},
    "capabilities": {
      "br.dev.bcp.common.identity_linking": [{
        "version": "{{ bcp_schema_version }}",
        "spec": "https://bcp.dev.br/specification/identity-linking",
        "schema": "https://bcp.dev.br/schemas/common/identity_linking.json",
        "config": {
          "scopes": {
            "br.dev.bcp.shopping.order:read":    {},
            "br.dev.bcp.shopping.order:manage":  {}
          }
        }
      }]
    },
    "payment_handlers": {}
  }
}
```

**Lendo esta configuração:**

* `br.dev.bcp.shopping.order:read` e `:manage` — listados → é necessária
  autenticação do usuário para obtê-los.
* Catálogo, checkout, carrinho e tudo mais — não listados → nenhum escopo de
  autenticação do usuário é necessário. Acesso público/autenticado por agente. O
  usuário ainda pode solicitar, ou o agente ainda pode oferecer, vinculação para
  acesso a recursos adicionais como personalização, endereços e credenciais
  salvas, preços de fidelidade, etc.

#### Atacadista B2B

Sem check-out de convidado – toda transação requer um usuário autenticado:

<!-- ucp:example schema=profile def=business_schema -->
```json
{
  "ucp": {
    "version": "{{ bcp_schema_version }}",
    "services": {},
    "capabilities": {
      "br.dev.bcp.common.identity_linking": [{
        "version": "{{ bcp_schema_version }}",
        "spec": "https://bcp.dev.br/specification/identity-linking",
        "schema": "https://bcp.dev.br/schemas/common/identity_linking.json",
        "config": {
          "scopes": {
            "br.dev.bcp.shopping.checkout:manage":  {},
            "br.dev.bcp.shopping.order:read":       {},
            "br.dev.bcp.shopping.order:manage":     {}
          }
        }
      }]
    },
    "payment_handlers": {}
  }
}
```

**A diferença:** `br.dev.bcp.shopping.checkout:manage` agora está listado. No
exemplo B2C, isso não bloqueia o checkout; qualquer pessoa pode iniciar uma sessão
de convidado. Aqui, o comerciante exige que o usuário esteja autenticado para
todas as operações de checkout — criar, atualizar, concluir e cancelar.

Se o usuário é elegível para B2B, quais preços ele vê, quais condições de pagamento
aplicar – esses são atributos do usuário que o comerciante resolve em tempo de execução, não
escopos adicionais.

### Passo a passo de ponta a ponta

**Configuração:** Plataforma (agente de compras AI) + Negócios (varejista B2C do
exemplo acima).

**Capacidades negociadas:** `br.dev.bcp.shopping.checkout`,
`br.dev.bcp.shopping.order`, `br.dev.bcp.common.identity_linking`.

**Etapa 1 — Derivação do escopo.** A plataforma lê o `config.scopes` do negócio:

* `br.dev.bcp.shopping.order:read` (ler histórico de pedidos)
* `br.dev.bcp.shopping.order:manage` (cancelar/devolver)

O usuário deseja que o agente possa ler o histórico de pedidos e cancelar pedidos
em seu nome, então a plataforma solicita ambos os escopos.

Conjunto de escopo derivado: `br.dev.bcp.shopping.order:read br.dev.bcp.shopping.order:manage`

**Etapa 2 — Descoberta.** Buscas de plataforma
`https://merchant.example.com/.well-known/oauth-authorization-server`,
recebe `2xx`, extrai `authorization_endpoint` e `token_endpoint`.
Verifica se ambos os escopos estão em `scopes_supported`.

**Etapa 3 — Solicitação de autorização.** Plataforma gera par PKCE
(`code_verifier`, `code_challenge`), encaminha o usuário para:

```text
GET https://merchant.example.com/oauth2/authorize
  ?response_type=code
  &client_id=platform-client-id
  &redirect_uri=https://agent.example.com/callback
  &scope=br.dev.bcp.shopping.order:read br.dev.bcp.shopping.order:manage
  &code_challenge=<S256-hash>
  &code_challenge_method=S256
  &state=<random>
```

Os caracteres reservados em `redirect_uri` e `:` em tokens de escopo devem ser
codificado em porcentagem na solicitação real; eles são mostrados decodificados aqui para facilitar a leitura.

**Etapa 4 — Resposta de autorização.** O usuário autentica e consente.
A empresa redireciona para:

```text
https://agent.example.com/callback
  ?code=<auth-code>
  &state=<random>
  &iss=https://merchant.example.com
```

A plataforma valida que `state` corresponde e que `iss` é igual ao `issuer` descoberto.

**Etapa 5 — Troca de token.** A plataforma chama o endpoint do token:

```http
POST https://merchant.example.com/oauth2/token
Authorization: Basic <base64(client_id:client_secret)>
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=<auth-code>
&redirect_uri=https://agent.example.com/callback
&code_verifier=<verifier>
```

A empresa valida `code_verifier` em relação ao `code_challenge` armazenado, retorna:

<!-- ucp:example skip reason="OAuth metadata, not BCP payload" -->
```json
{
  "access_token": "<token>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "<refresh>",
  "scope": "br.dev.bcp.shopping.order:read br.dev.bcp.shopping.order:manage"
}
```

Plataforma agora inclui `Authorization: Bearer <token>` em solicitações subsequentes
para terminais de recursos autenticados pelo usuário.
