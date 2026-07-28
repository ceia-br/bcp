<div class="bcp-doc-page" markdown="1">

<span class="bcp-eyebrow">Documentation</span>

# Core Concepts

<p class="bcp-doc-page__lead">
BCP defines how businesses, platforms, AI agents, and payment providers interact
through standardized building blocks, so no pair of participants needs a custom
integration.
</p>

<div class="bcp-list" markdown="1">
<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">S1</span><h2>Roles</h2></div>

Businesses expose catalogs and checkout. Platforms and AI agents orchestrate
discovery and purchase on behalf of users. Payment providers settle transactions
over Brazilian rails. Any participant can implement any role.
</div>

<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">S2</span><h2>Capabilities</h2></div>

The protocol is modular: catalog search and lookup, cart building, identity
linking, checkout, and order management. Implementations declare supported
capabilities and negotiate versions per session.
</div>

<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">S3</span><h2>Checkout Sessions</h2></div>

A shared session object carries line items, totals, fulfillment, taxes, and
payment state through its lifecycle, created, negotiated, and completed across
every surface.
</div>

<div class="bcp-list-item" markdown="1">
<div class="bcp-list-item__title"><span class="bcp-list-item__num">S4</span><h2>Brazilian Extensions</h2></div>

National requirements are standard modules, not afterthoughts: Pix payment
mandates, NF-e/NFC-e electronic invoicing, CPF/CNPJ buyer identification,
Brazilian tax transparency, and marketplace flows.
</div>
</div>

</div>
