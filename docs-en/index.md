<div class="landing-page" markdown="1">

<section class="bcp-hero" markdown="1">
<div class="bcp-hero__content" markdown="1">

<span class="bcp-eyebrow">Open standard / Draft</span>

# Brazilian Commerce Protocol

The common language for platforms, AI agents, and Brazilian businesses, from
discovery to checkout, with Pix, NF-e, fiscal identity, taxes, and local rails
built in.

<div class="bcp-actions" markdown="1">
<a class="bcp-button bcp-button--primary" href="specification/overview/">Read the spec</a>
<a class="bcp-button" href="core-concepts/">Core concepts</a>
</div>

</div>

<div class="bcp-hero__mark">
<img src="assets/bcp-logo.svg" alt="BCP protocol mark">
</div>
</section>

<div class="bcp-band" markdown="1">
<section class="bcp-section" markdown="1">

## Built for flexibility, security, and scale

<div class="bcp-grid" markdown="1">
<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">01</span>

### Open and extensible

An open standard with community-driven capabilities and extensions, so the
ecosystem operates through one language without custom builds.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">02</span>

### Businesses at the center

Merchants remain the merchant of record, keeping ownership of customer
relationships and business logic.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">03</span>

### Local rails, native

Pix, NF-e/NFC-e invoicing, CPF/CNPJ identity, and marketplace flows are
first-class protocol concepts.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">04</span>

### Scalable and universal

Surface-agnostic design for any business, from MEI to enterprise, across chat,
visual commerce, and voice.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">05</span>

### Secure and private

OAuth 2.0 account linking and payment mandates keep authorization explicit,
auditable, and backed by signed consent.
</div>

<div class="bcp-card" markdown="1">
<span class="bcp-card__tag">06</span>

### Interoperable by design

REST and JSON-RPC transports with MCP, A2A, and AP2 support built in, so systems
can integrate without custom contracts.
</div>
</div>

</section>
</div>

<section class="bcp-section" markdown="1">
<div class="bcp-grid bcp-grid--two" markdown="1">
<div markdown="1">

## One checkout session, every surface

<p class="bcp-section__lead">
Complex cart logic, dynamic pricing, tax and invoice handling are negotiated
through a unified session object that any agent or platform can speak.
</p>

<a class="bcp-button" href="specification/checkout/">Checkout spec</a>

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

## Who supports BCP

<p class="bcp-section__lead">
BCP is developed with the support of a group of entities with complementary
roles, among them CEIA-UFG, SEBRAE, and AI Brasil.
</p>

<div class="swiper bcp-sponsors-swiper">
<div class="swiper-wrapper">
<a class="swiper-slide bcp-card bcp-sponsor-card bcp-sponsor-card--akcit" href="https://akcit.ufg.br/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo bcp-sponsor-logo--akcit" src="assets/akcit-logo-purple.png" alt="AKCIT logo">
<span class="bcp-sponsor-card__url">akcit.ufg.br ↗</span>
</a>
<a class="swiper-slide bcp-card bcp-sponsor-card bcp-sponsor-card--ceia" href="https://ceia.ufg.br/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo bcp-sponsor-logo--ceia" src="assets/ceia-logo-white.png" alt="CEIA logo">
<span class="bcp-sponsor-card__url">ceia.ufg.br ↗</span>
</a>
<a class="swiper-slide bcp-card bcp-sponsor-card bcp-sponsor-card--aibrasil" href="https://aibrasil.ai/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo" src="assets/aibrasil-logo-white.png" alt="AI Brasil logo">
<span class="bcp-sponsor-card__url">aibrasil.ai ↗</span>
</a>
<a class="swiper-slide bcp-card bcp-sponsor-card" href="https://sebrae.com.br/" target="_blank" rel="noopener">
<img class="bcp-sponsor-logo" src="assets/sebrae-logo-white.png" alt="Sebrae logo">
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

## Get started today

<p>BCP is an open standard. The specification, documentation, and reference implementations evolve in public, with feedback and contributions welcome.</p>

<div class="bcp-actions" markdown="1">
<a class="bcp-button bcp-button--primary" href="roadmap/">View the roadmap</a>
<a class="bcp-button" href="partners/">Become a partner</a>
</div>
</section>

</div>
