<div class="landing-page" markdown="1">

<section class="bcp-hero" markdown="1">
<div class="bcp-hero__content" markdown="1">

<span class="bcp-eyebrow">Padrão aberto / Rascunho</span>

# Protocolo Comercial Brasileiro

A linguagem comum para plataformas, agentes de IA e empresas brasileiras — da
descoberta ao checkout — com Pix, NF-e, identidade fiscal, tributos e meios de
pagamento locais incorporados.

<div class="bcp-actions" markdown="1">
<a class="bcp-button bcp-button--primary" href="specification/overview/">Ler a especificação</a>
<a class="bcp-button" href="core-concepts/">Conceitos básicos</a>
</div>

</div>

<div class="bcp-hero__mark">
<img src="assets/bcp-logo.svg" alt="Marca do protocolo BCP">
</div>
</section>

<div class="bcp-band" markdown="1">
<section class="bcp-section" markdown="1">

## Feito para flexibilidade, segurança e escala

<div class="bcp-grid" markdown="1">
<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">01</span>

### Aberto e extensível

Um padrão aberto com capacidades e extensões construídas pela comunidade, para
que o ecossistema opere em uma linguagem comum, sem integrações sob medida.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">02</span>

### Empresas no centro

Os vendedores continuam como comerciantes responsáveis, preservando a relação
com o cliente e as regras que tornam cada negócio único.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">03</span>

### Infraestrutura brasileira nativa

Pix, NF-e/NFC-e, identidade CPF/CNPJ e fluxos de marketplace são conceitos de
primeira classe do protocolo.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">04</span>

### Escalável e universal

Um desenho independente de interface, adequado de MEIs a grandes empresas, em
conversas, experiências visuais e voz.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">05</span>

### Seguro e privado

Vínculo de contas via OAuth 2.0 e mandatos de pagamento tornam a autorização
explícita, auditável e apoiada por consentimento assinado.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">06</span>

### Interoperável por design

Transportes REST e JSON-RPC, com suporte a MCP, A2A e AP2, permitem integrar
sistemas sem criar um contrato proprietário a cada conexão.
</div>
</div>

</section>
</div>

<section class="bcp-section" markdown="1">
<div class="bcp-grid bcp-grid--two" markdown="1">
<div markdown="1">

## Uma sessão de checkout em qualquer interface

<p class="bcp-section__lead">
Lógica complexa de carrinho, preços dinâmicos, impostos e faturamento são
negociados por um objeto de sessão unificado que qualquer agente ou plataforma
pode compreender.
</p>

<a class="bcp-button" href="specification/checkout/">Especificação de checkout</a>

</div>

<div class="bcp-code-panel" markdown="1">
<pre><span class="comment">// POST /bcp/checkout-sessions</span>
{
  <span class="key">"bcp"</span>: { <span class="key">"version"</span>: <span class="value">"{{ bcp_schema_version }}"</span> },
  <span class="key">"id"</span>: <span class="value">"chk_8f2a91"</span>,
  <span class="key">"status"</span>: <span class="value">"ready_for_complete"</span>,
  <span class="key">"currency"</span>: <span class="value">"BRL"</span>,
  <span class="key">"payment"</span>: { <span class="key">"method"</span>: <span class="value">"pix"</span> },
  <span class="key">"invoice"</span>: { <span class="key">"type"</span>: <span class="value">"nfe"</span>, <span class="key">"cpf_cnpj"</span>: <span class="value">"***"</span> },
  <span class="key">"totals"</span>: [ ... ]
}</pre>
</div>
</div>
</section>

<div class="bcp-band" markdown="1">
<section class="bcp-section bcp-sponsors" markdown="1">

## Quem apoia o BCP

<p class="bcp-section__lead">
O BCP é desenvolvido com apoio de um conjunto de entidades com papéis
complementares, dentre eles CEIA-UFG, SEBRAE e AI Brasil.
</p>

<div class="swiper bcp-sponsors-swiper">
<div class="swiper-wrapper">
<a class="swiper-slide bcp-card bcp-sponsor-card bcp-sponsor-card--akcit" href="https://akcit.ufg.br/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo bcp-sponsor-logo--akcit" src="assets/akcit-logo-purple.png" alt="Logo do AKCIT">
<span class="bcp-sponsor-card__url">akcit.ufg.br ↗</span>
</a>
<a class="swiper-slide bcp-card bcp-sponsor-card bcp-sponsor-card--ceia" href="https://ceia.ufg.br/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo bcp-sponsor-logo--ceia" src="assets/ceia-logo-white.png" alt="Logo do CEIA">
<span class="bcp-sponsor-card__url">ceia.ufg.br ↗</span>
</a>
<a class="swiper-slide bcp-card bcp-sponsor-card bcp-sponsor-card--aibrasil" href="https://aibrasil.ai/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo" src="assets/aibrasil-logo-white.png" alt="Logo do AI Brasil">
<span class="bcp-sponsor-card__url">aibrasil.ai ↗</span>
</a>
<a class="swiper-slide bcp-card bcp-sponsor-card" href="https://sebrae.com.br/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo" src="assets/sebrae-logo-white.png" alt="Logo do Sebrae">
<span class="bcp-sponsor-card__url">sebrae.com.br ↗</span>
</a>
</div>
<div class="swiper-pagination"></div>
<div class="swiper-button-prev"></div>
<div class="swiper-button-next"></div>
</div>

</section>
</div>

<section class="bcp-section bcp-cta" markdown="1">

## Comece agora

<p>O BCP é um padrão aberto. Especificação, documentação e implementações de referência evoluem publicamente, com espaço para feedback e contribuições.</p>

<div class="bcp-actions" markdown="1">
<a class="bcp-button bcp-button--primary" href="roadmap/">Ver o roteiro</a>
<a class="bcp-button" href="partners/">Tornar-se parceiro</a>
</div>
</section>

</div>
