# Gerenciador de pagamentos Pix

Manipulador `br.dev.bcp.pix`, versão `{{ bcp_schema_version }}`, usa o esquema
`schemas/handlers/pix/pix.json`.

## Visão geral

Esse manipulador modela cobranças dinâmicas únicas do Pix. O PSP do beneficiário cria uma
cobrança dinâmica de valor fixo; o pagador efetua o pagamento a partir de qualquer instituição
financeira habilitada para Pix, escaneando o QR Code ou copiando e colando o payload do BR Code.

Pix inverte o fluxo habitual dos manipuladores de cartões. Com os cartões, uma plataforma muitas vezes adquire
uma credencial e a envia para a empresa. No Pix, a cobrança é criada pela empresa
por meio do seu PSP e retornada na resposta de checkout para exibição.
A confirmação da liquidação chega à empresa por meio do webhook do PSP.

Este manipulador está limitado a cobranças únicas. Pagamentos recorrentes via Pix ou iniciação
de pagamento via Open Finance requerem um manipulador separado.

## Participantes

| Participante | Função |
| :---------- | :--- |
| **Pagador** | Paga no aplicativo do banco escaneando o QR Code ou copiando o código Pix (copia e cola). |
| **Plataforma** | Descobre o manipulador, seleciona Pix e exibe a cobrança. |
| **Negócios** | Cria a cobrança através do seu PSP, recebe notificações de liquidação e reconcilia. |
| **PSP Beneficiário** | Emite a cobrança dinâmica e notifica a empresa após a liquidação. |

## Pré-requisitos

- **Negócios**: contrata um PSP beneficiário e armazena as credenciais de API do provedor em seu
  back-end. As credenciais do PSP nunca viajam em cargas úteis de descoberta ou resposta.
- **Plataforma**: não é necessária integração com PSP. A plataforma só precisa suportar
  a exibição da cobrança Pix retornada.

## Declaração do manipulador

Declaração de descoberta de negócios:

```json
{
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

Declaração da plataforma:

```json
{
  "id": "pix_platform_001",
  "version": "{{ bcp_schema_version }}",
  "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/pix-payment-handler",
  "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/handlers/pix/pix.json",
  "available_instruments": [{ "type": "pix" }],
  "config": { "environment": "production", "platform_id": "plat_abc" }
}
```

As declarações de resposta carregam a configuração do tempo de execução. A carga real viaja como
um `pix_payment_instrument` em `payment.instruments`.

## Aquisição de instrumentos

1. A plataforma seleciona Pix durante a finalização da compra.
2. A empresa aciona seu PSP para criar uma cobrança dinâmica para o total do checkout.
3. O PSP retorna `provider_payment_id`, `copia_e_cola` e `expires_at`.
4. A empresa devolve um instrumento de pagamento Pix com tipo de credencial
   `pix_charge`.
5. A plataforma exibe o QR Code ou o código copia e cola até `expires_at`.

A carga útil `copia_e_cola` é um payload de BR Code (EMV) que já codifica o beneficiário
e o valor. A reconciliação usa `provider_payment_id`.

## Processamento

1. O pagador efetua o pagamento Pix no aplicativo do banco.
2. A rede Pix liquida os valores junto ao PSP beneficiário.
3. O PSP notifica a empresa por webhook.
4. A empresa verifica a vinculação e o valor antes de aceitar a liquidação.
5. A ordem avança após a confirmação da liquidação.

### Mapeamento de erros

| Situação | `error_code` sugerido |
| :-------- | :--------------------- |
| A cobrança expirou sem pagamento | `payment_expired` |
| Descasamento do montante liquidado ou falha genérica | `payment_failed` |
| PSP beneficiário indisponível | `processor_unavailable` |

O estado de reembolso é representado pela capacidade de devolução, não por este manipulador.

## Segurança

- A credencial pode incluir `binding` para associar a cobrança Pix ao
  checkout e à identidade do beneficiário.
- As credenciais da API do PSP permanecem no back-end da empresa e nunca entram nas cargas
  úteis de descoberta, esquema ou resposta.
- As plataformas **NÃO DEVEM** apresentar a cobrança após `expires_at`.
