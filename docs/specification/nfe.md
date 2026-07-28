# Extensão da NF-e

`br.dev.bcp.shopping.nfe` estende `order`.

## Visão geral

Carrega no pedido a **referência** da Nota Fiscal eletrônica emitida: chave de
acesso, links do DANFE e do XML autorizado e data de emissão. Nem o modelo nem o
protocolo de autorização trafegam: o **modelo** (55/65) é derivável da chave de
acesso (dígitos 21-22), e o **protocolo de autorização** (`nProt`) vive no XML
autorizado e no domínio do emissor — o comprador verifica a nota pela chave, não
pelo protocolo. Minimização: id de provedor e metadado de emissão ficam do lado
de dentro.

Somente a referência viaja no fio. Os dados pessoais do comprador permanecem nos
sistemas fiscais do vendedor, apoiando a minimização de dados da LGPD e preservando os
deveres de retenção fiscal do vendedor.

O bloco é opcional no JSON Schema porque a obrigação de emissão de NF-e
depende do regime do vendedor e do tipo de comprador.

## Descoberta

```json
{
  "capabilities": {
    "br.dev.bcp.shopping.nfe": [
      {
        "version": "{{ bcp_schema_version }}",
        "extends": "br.dev.bcp.shopping.order",
        "spec": "https://bcp.dev.br/{{ bcp_version }}/specification/nfe",
        "schema": "https://bcp.dev.br/{{ bcp_version }}/schemas/shopping/nfe.json"
      }
    ]
  }
}
```

## Composição do esquema

- `order.nfe` é um novo objeto opcional somente de resposta.
- Esquema: `schemas/shopping/nfe.json`.

## Campos

| Campo | Tipo | Obrigatório | Descrição |
| :---- | :--- | :------- | :---------- |
| `access_key` | string | Sim | Chave de acesso da NF-e com 44 dígitos identificando o documento na SEFAZ. |
| `danfe_url` | URI | Não | Documento DANFE legível por humanos, geralmente PDF. |
| `xml_url` | URI | Não | Documento XML autorizado. |
| `issued_at` | data-hora | Não | Carimbo de data/hora da emissão. |

## Regras normativas

1. Quando o vendedor é obrigado a emitir uma NF-e, o pedido **DEVE** receber o
   bloco `nfe` após autorização do documento.
2. O bloco **NÃO DEVE** conter dados pessoais do comprador. Ele carrega apenas
   referências ao documento.
3. Emissão, assinatura, autorização e escrituração contábil são responsabilidades
   do vendedor e ficam fora do formato de fio do protocolo.

## Exemplo

Trecho da resposta do pedido:

```json
{
  "id": "ord_789",
  "nfe": {
    "access_key": "35260519131243000197550010000012341000012349",
    "danfe_url": "https://notas.example.com.br/danfe/12345.pdf",
    "xml_url": "https://notas.example.com.br/xml/12345.xml",
    "issued_at": "2026-07-03T14:30:00-03:00"
  }
}
```
