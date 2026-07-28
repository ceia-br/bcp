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

# Glossário

Este glossário fornece uma captura de melhor esforço dos acrônimos e termos usados
em toda a especificação BCP. Novas entradas devem ser adicionadas em ordem alfabética
dentro de sua respectiva categoria.

**Observação:** Mesmo com este glossário, é preferível que o primeiro uso de um
acrônimo em cada arquivo Markdown de especificação indique o termo completo (por exemplo,
"Padrão de segurança de dados da indústria de cartões de pagamento (PCI-DSS)").

## Protocolo

| Termo | Sigla | Definição |
| :------------------------------ | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Protocolo de pagamentos do agente** | AP2 | Um protocolo aberto projetado para permitir que agentes de IA interoperem com segurança e concluam pagamentos de forma autônoma. O BCP aproveita o AP2 para mandatos de pagamento seguros. |
| **Protocolo Agente2Agente** | A2A | Um padrão aberto para comunicação segura e colaborativa entre diversos agentes de IA. O BCP pode usar A2A como camada de transporte.                                 |
| **Capacidade** | - | Um recurso central independente que uma empresa suporta (por exemplo, Checkout, Identity Linking). As capacidades são os “verbos” fundamentais do BCP.                   |
| **Provedor de credenciais** | CP | Uma entidade confiável (como uma carteira digital ou um PSP participante do Open Finance Brasil) responsável por gerenciar e executar com segurança o pagamento e as credenciais de identidade do usuário.                     |
| **Extensão** | - | Um recurso opcional que aumenta outro recurso por meio do campo `extends`. As extensões aparecem em `ucp.capabilities[]` junto com os recursos principais.   |
| **Protocolo de Contexto do Modelo** | MCP | Um protocolo que padroniza como os modelos de IA se conectam a dados e ferramentas externas. Os recursos do BCP são mapeados 1:1 para as ferramentas do MCP.                                         |
| **Perfil** | - | Um documento JSON hospedado por empresas e plataformas em um URI conhecido, declarando sua identidade, recursos suportados e endpoints.                  |
| **Protocolo Comercial Brasileiro** | BCP | O padrão definido neste documento, permitindo a interoperabilidade entre entidades comerciais por meio de recursos padronizados e descoberta.                   |

## Comércio

| Termo | Sigla | Definição |
| :--------------------------- | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Negócios** | - | A entidade que vende bens ou serviços. No BCP, eles atuam como **Comerciante de Registro (MoR)**, mantendo a responsabilidade financeira e a propriedade do pedido. |
| **Comerciante de Registro** | MoR | A entidade legal responsável pela venda, incluindo responsabilidade financeira e propriedade do pedido.                                                         |
| **Provedor de serviços de pagamento** | PSP | O provedor de infraestrutura financeira que processa pagamentos, autorizações e liquidações em nome da empresa.                             |
| **Plataforma** | - | A superfície voltada para o consumidor (agente de IA, aplicativo, site) que atua em nome do usuário para descobrir empresas e facilitar o comércio.                     |

## Pagamentos

O Pix é o meio de pagamento padrão do BCP, via o manipulador de pagamento
`handlers/pix`. Os termos de cartão abaixo (CVV, PCI-DSS, PAN, SCA, 3DS) só se
aplicam quando um manipulador de pagamento baseado em cartão é usado para
interoperabilidade — não fazem parte do fluxo Pix.

| Termo | Sigla | Definição |
| :---------------------------------------------------------- | :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pix** | - | O arranjo de pagamento instantâneo do Banco Central do Brasil (BACEN). É o meio de pagamento padrão do BCP, referenciado no protocolo por meio do manipulador `handlers/pix`. |
| **Open Finance Brasil** | - | O ecossistema regulado pelo BACEN para compartilhamento padronizado de dados e serviços financeiros entre instituições, mediante consentimento do usuário. Sustenta a autorização de pagamentos Pix e a atuação de Provedores de Credenciais (CP) no BCP. |
| **Valor de verificação do cartão** | CVV | O código de segurança de 3 ou 4 dígitos em cartões de pagamento usado para verificar transações sem cartão presente.                                                                    |
| **Padrão de segurança de dados da indústria de cartões de pagamento** | PCI-DSS | Um conjunto de padrões de segurança projetados para garantir que todas as empresas que aceitam, processam, armazenam ou transmitem informações de cartão de crédito mantenham um ambiente seguro. |
| **Número da conta principal** | PAN | O número exclusivo do cartão de pagamento (normalmente de 13 a 19 dígitos) que identifica o emissor do cartão e a conta do titular do cartão.                                                  |
| **Autenticação Forte do Cliente** | SCA | Um requisito da PSD2 (regulação europeia) de que os prestadores de serviços de pagamento apliquem autenticação multifatorial para pagamentos eletrônicos com cartão.                                               |
| **3D seguro** | 3DS | Um protocolo projetado para adicionar uma camada de segurança adicional para transações on-line com cartão de crédito e débito por meio da autenticação do titular do cartão.                         |

## Conformidade e regulamentação

| Termo | Sigla | Definição |
| :------------------------------------- | :------ | :--------------------------------------------------------------------------------------------------------------------- |
| **Lei Geral de Proteção de Dados** | LGPD | A lei brasileira de proteção de dados pessoais (Lei 13.709/2018). Rege a minimização de dados e o tratamento de informações do comprador e do vendedor nas extensões do BCP, como [NF-e](nfe.md). |
| **Lei de Privacidade do Consumidor da Califórnia** | CCPA | Uma lei estadual destinada a aumentar os direitos de privacidade e a proteção do consumidor para residentes da Califórnia, Estados Unidos. |
| **Regulamento Geral de Proteção de Dados** | RGPD | Um regulamento da legislação da UE sobre proteção de dados e privacidade na União Europeia e no Espaço Económico Europeu.            |
| **Conheça seu cliente** | KYC | O processo de verificação da identidade dos clientes para prevenir fraude, lavagem de dinheiro e financiamento do terrorismo.          |

## Padrões e especificações

| Termo | Sigla | Definição |
| :------------------------------------------------- | :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Organização Internacional de Padronização** | ISO | Um órgão internacional de definição de padrões composto por representantes de diversas organizações nacionais de normalização. Referenciado no BCP para códigos de país (ISO 3166-1), códigos de moeda (ISO 4217) e formatos de data (ISO 8601). |
| **Credencial digital verificável** | VDC | Uma credencial assinada pelo emissor (conjunto de declarações) cuja autenticidade pode ser verificada criptograficamente. Usado no BCP para autorizações de pagamento seguras.                                                                            |
