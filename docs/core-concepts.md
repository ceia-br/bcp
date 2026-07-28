<div class="bcp-doc-page" markdown="1">

<span class="bcp-eyebrow">Documentação</span>

# Conceitos básicos

<p class="bcp-doc-page__lead">
O BCP define como empresas, plataformas, agentes de IA e provedores de pagamento
interagem com blocos de construção padronizados — sem exigir uma integração
customizada para cada par de participantes.
</p>

<div class="bcp-list" markdown="1">
<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">§1</span><h2>Papéis</h2></div>

Empresas expõem catálogo e checkout. Plataformas e agentes de IA orquestram a
descoberta e a compra em nome do usuário. Provedores de pagamento liquidam as
transações pelos meios brasileiros. Um participante pode implementar mais de um
papel.
</div>

<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">§2</span><h2>Capacidades</h2></div>

O protocolo é modular: busca e consulta de catálogo, construção de carrinho,
vínculo de identidade, checkout e gestão de pedidos. Cada implementação declara
as capacidades suportadas e negocia versões em cada sessão.
</div>

<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">§3</span><h2>Sessões de checkout</h2></div>

Um objeto de sessão compartilhado acompanha itens, totais, entrega, impostos e
estado de pagamento durante todo o ciclo de vida, em qualquer interface.
</div>

<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">§4</span><h2>Extensões brasileiras</h2></div>

Requisitos nacionais são módulos de primeira classe: mandatos Pix, NF-e/NFC-e,
identificação do comprador por CPF/CNPJ, transparência tributária e fluxos de
marketplace.
</div>
</div>

</div>
