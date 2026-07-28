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

# Referência de esquema

Esta página fornece uma referência para todos os modelos e tipos de dados de capacidade usados
dentro do BCP.

## Esquemas de capacidade

{{ auto_generate_schema_reference('.', 'reference', include_extensions=False) }}

## Esquemas de tipo

{{ auto_generate_schema_reference('types', 'reference', include_extensions=False) }}

### Instrumento de pagamento selecionado {: #payment-instrument-selected-payment-instrument }

{{ extension_schema_fields('types/payment_instrument.json#/$defs/selected_payment_instrument', 'reference') }}

### Solicitação de paginação {: #pagination-request }

{{ extension_schema_fields('types/pagination.json#/$defs/request', 'reference') }}

### Resposta de paginação {: #pagination-response }

{{ extension_schema_fields('types/pagination.json#/$defs/response', 'reference') }}

### Código de erro {: #error-code }

{{ schema_fields('types/error_code', 'reference') }}

### Código de aviso {: #warning-code }

{{ schema_fields('types/warning_code', 'reference') }}

### Código de informação {: #info-code }

{{ schema_fields('types/info_code', 'reference') }}

## Esquemas de extensão

{{ auto_generate_schema_reference('.', 'reference', include_capability=False) }}

## Esquemas de manipulador de pagamento

{{ auto_generate_schema_reference('handlers/pix', 'reference', base_dir='schemas') }}

## Metadados BCP <span id="services"></span> <span id="ap2-checkout-response"></span> <span id="ap2-complete-request"></span>

Os esquemas a seguir definem a estrutura dos metadados BCP usados na descoberta
e respostas.

### Perfil de descoberta de plataforma

A estrutura de nível superior de um documento de perfil de plataforma (hospedado em um URI anunciado pela plataforma).

{{ extension_schema_fields('ucp.json#/$defs/platform_schema', 'reference') }}

### Perfil de descoberta de negócios

A estrutura de nível superior de um documento de descoberta de negócios (`/.well-known/bcp`).

{{ extension_schema_fields('ucp.json#/$defs/business_schema', 'reference') }}

### Metadados de resposta de checkout {: #ucp-response-checkout-schema }

O objeto `ucp` incluído nas respostas de checkout.

{{ extension_schema_fields('ucp.json#/$defs/response_checkout_schema', 'reference') }}

### Metadados de resposta do carrinho {: #ucp-response-cart-schema }

O objeto `ucp` incluído nas respostas do carrinho.

{{ extension_schema_fields('ucp.json#/$defs/response_cart_schema', 'reference') }}

### Metadados de resposta do catálogo {: #ucp-response-catalog-schema }

O objeto `ucp` incluído nas respostas do catálogo.

{{ extension_schema_fields('ucp.json#/$defs/response_catalog_schema', 'reference') }}

### Metadados de resposta do pedido {: #ucp-response-order-schema }

O objeto `ucp` incluído em respostas de pedidos ou eventos.

{{ extension_schema_fields('ucp.json#/$defs/response_order_schema', 'reference') }}

### Capacidade

Este objeto descreve um único recurso ou extensão. Aparece na
matriz `capabilities` em perfis de descoberta e respostas, com campos
obrigatórios ligeiramente diferentes em cada contexto.

#### Capacidade (descoberta) {: #discovery }

Conforme visto nos perfis de descoberta.

{{ extension_schema_fields('capability.json#/$defs/platform_schema', 'reference') }}

#### Capacidade (resposta) {: #response }

Conforme visto nas mensagens de resposta.

{{ extension_schema_fields('capability.json#/$defs/response_schema', 'reference') }}
