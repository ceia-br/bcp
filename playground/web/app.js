(() => {
  const currentScript = document.currentScript;
  const appRoot = currentScript?.getRootNode() || window.__bcpPlaygroundMountRoot || document;
  const locale = currentScript?.dataset.lang === "en" || appRoot.host?.dataset.lang === "en"
    ? "en"
    : "pt-BR";
  const snapshotsSource = currentScript?.dataset.snapshots
    || appRoot.host?.dataset.snapshotsBase
    || "../../assets/playground/snapshots/";
  const snapshotsBase = new URL(snapshotsSource, currentScript?.src || window.location.href);

  const copy = {
    "pt-BR": {
      heroEyebrow: "Fluxo de compra",
      heroTitle: "Playground do BCP",
      heroCopy: "A compra ponta a ponta com um vendedor conhecido. À esquerda está a conversa correspondente a cada etapa. À direita, as trocas A2A, BCP e MCP que a sustentam.",
      client: "Cliente",
      clientCopy: "a pessoa que conversa somente com seu agente",
      buyer: "Agente cliente",
      buyerCopy: "o assistente que age em nome do cliente",
      seller: "Agente vendedor",
      sellerCopy: "o agente da loja que executa o comércio",
      conversation: "Conversa entre cliente e agente cliente",
      buyerSellerConversation: "Conversa entre agente cliente e agente vendedor",
      buyerAction: "Ação do agente cliente",
      sellerAction: "Ação do agente vendedor",
      under: "POR BAIXO DOS PANOS",
      noDocuments: "Esta etapa não troca documentos entre os agentes.",
      previous: "← Voltar",
      next: "Continuar →",
      reset: "Reiniciar",
      step: "PASSO",
      of: "DE",
      request: "Request",
      response: "Response",
      awaiting: "Aguardando pagamento",
      paid: "Pagamento confirmado",
      preparing: "Liquidação recebida. Preparando o pedido.",
      simulatePayment: "Simular pagamento",
      copyCode: "Copiar código",
      copied: "copiado ✓",
      order: "Pedido confirmado",
      orderLabel: "Pedido",
      carrier: "Transportadora",
      tracking: "Rastreio",
      estimated: "Previsão",
      authorized: "autorizada",
      copyTracking: "copiar",
      loadError: "Não foi possível carregar os snapshots do playground.",
    },
    en: {
      heroEyebrow: "Purchase flow",
      heroTitle: "BCP Playground",
      heroCopy: "An end-to-end purchase with one known seller. The conversation for each stage is on the left. The A2A, BCP, and MCP exchanges behind it are on the right.",
      client: "Customer",
      clientCopy: "the person who talks only to their agent",
      buyer: "Buyer agent",
      buyerCopy: "the assistant acting for the customer",
      seller: "Seller agent",
      sellerCopy: "the store agent executing commerce",
      conversation: "Conversation between customer and buyer agent",
      buyerSellerConversation: "Conversation between buyer and seller agents",
      buyerAction: "Buyer agent action",
      sellerAction: "Seller agent action",
      under: "UNDER THE HOOD",
      noDocuments: "This stage does not exchange documents between the agents.",
      previous: "← Previous",
      next: "Continue →",
      reset: "Reset",
      step: "STEP",
      of: "OF",
      request: "Request",
      response: "Response",
      awaiting: "Awaiting payment",
      paid: "Payment confirmed",
      preparing: "Settlement received. Preparing the order.",
      simulatePayment: "Simulate payment",
      copyCode: "Copy code",
      copied: "copied ✓",
      order: "Order confirmed",
      orderLabel: "Order",
      carrier: "Carrier",
      tracking: "Tracking",
      estimated: "Estimated delivery",
      authorized: "authorized",
      copyTracking: "copy",
      loadError: "The playground snapshots could not be loaded.",
    },
  }[locale];

  let steps = [];
  let index = 0;
  let paymentDone = false;

  function byId(id) {
    return appRoot.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function localized(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return value;
    return value[locale] ?? value["pt-BR"] ?? value.en ?? value;
  }

  function highlightJson(value) {
    const json = JSON.stringify(value, null, 2)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
    return json.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        let className = "tok-num";
        if (/^"/.test(match)) className = /:$/.test(match) ? "tok-key" : "tok-str";
        else if (/true|false/.test(match)) className = "tok-bool";
        else if (/null/.test(match)) className = "tok-null";
        return `<span class="${className}">${match}</span>`;
      },
    );
  }

  function jsonBlock(document) {
    const { kind, name, payload } = document;
    const label = kind === "request" ? copy.request : copy.response;
    if (payload === undefined) return "";
    return `<div class="uth-io uth-io--${kind}">
      <div class="uth-io__label">
        <span class="uth-io__kind">${escapeHtml(label)}</span>
        <code class="uth-io__name">${escapeHtml(name)}</code>
      </div>
      <pre class="code">${highlightJson(payload)}</pre>
    </div>`;
  }

  function stepPanel(step) {
    const documents = step.documents || [];
    return `<section class="uth-step open" data-step="${escapeHtml(step.id)}">
      ${documents.length
        ? documents.map(jsonBlock).join("")
        : `<p class="uth-empty">${escapeHtml(copy.noDocuments)}</p>`}
    </section>`;
  }

  function conversationHeading(messages) {
    const actors = new Set(messages.map((message) => message.actor));
    if (actors.has("buyer_agent") && actors.has("seller_agent")) {
      return copy.buyerSellerConversation;
    }
    if (actors.has("client")) return copy.conversation;
    return actors.has("seller_agent") ? copy.sellerAction : copy.buyerAction;
  }

  function brl(cents) {
    return new Intl.NumberFormat(locale === "en" ? "en-US" : "pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(cents / 100);
  }

  function shirtSvg(color) {
    return `<svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M22 13 L12 19 L7 28 L16 34 L22 30 L22 53 Q22 55 24 55 L40 55 Q42 55 42 53 L42 30 L48 34 L57 28 L52 19 L42 13 L37 13 Q32 20 27 13 Z"
        fill="${escapeHtml(color)}" stroke="rgba(0,0,0,.35)" stroke-width="1.2" stroke-linejoin="round" />
    </svg>`;
  }

  function productCard(product) {
    return `<div class="pcard ${product.best ? "pcard--best" : ""}">
      <div class="pcard__img">${shirtSvg(product.color)}</div>
      <div class="pcard__body">
        <div class="pcard__title">${escapeHtml(product.title)}</div>
        <div class="pcard__meta">${escapeHtml(localized(product.meta))}</div>
        <div class="pcard__foot">
          <span class="pcard__price">${brl(product.price)}</span>
          <span class="pcard__badge ${product.best ? "pcard__badge--best" : ""}">${escapeHtml(localized(product.badge))}</span>
        </div>
      </div>
    </div>`;
  }

  function productWidget(step) {
    const items = step.widget?.type === "products" ? step.widget.items : [];
    if (!items.length) return "";
    return `<div class="pcards ${items.length === 1 ? "pcards--single" : ""}">${items.map(productCard).join("")}</div>`;
  }

  function shippingWidget(step) {
    const options = step.widget?.type === "shipping" ? step.widget.options : [];
    if (!options.length) return "";
    return `<div class="shipping-options">${options.map((option) => `
      <div class="shipping-option ${option.selected ? "shipping-option--selected" : ""}">
        <div>
          <strong>${escapeHtml(option.title)}</strong>
          <span>${escapeHtml(option.carrier)}</span>
        </div>
        <div class="shipping-option__price">${brl(option.price)}</div>
        <div class="shipping-option__eta">${escapeHtml(option.description)}</div>
      </div>`).join("")}</div>`;
  }

  function fakeQr(seed) {
    const size = 25;
    let hash = 2166136261;
    for (const character of seed) {
      hash ^= character.charCodeAt(0);
      hash = Math.imul(hash, 16777619);
    }
    const random = () => {
      hash ^= hash << 13;
      hash ^= hash >>> 17;
      hash ^= hash << 5;
      return (hash >>> 0) / 4294967296;
    };
    const inFinder = (row, column) =>
      (row < 7 && column < 7) || (row < 7 && column >= size - 7) ||
      (row >= size - 7 && column < 7);
    let modules = "";
    for (let row = 0; row < size; row += 1) {
      for (let column = 0; column < size; column += 1) {
        if (!inFinder(row, column) && random() <= 0.5) {
          modules += `<rect x="${column}" y="${row}" width="1" height="1"/>`;
        }
      }
    }
    const finder = (row, column) =>
      `<rect x="${column}" y="${row}" width="7" height="7"/><rect x="${column + 1}" y="${row + 1}" width="5" height="5" fill="#fff"/><rect x="${column + 2}" y="${row + 2}" width="3" height="3" fill="#0a0c10"/>`;
    return `<svg viewBox="0 0 ${size} ${size}" shape-rendering="crispEdges" fill="#0a0c10">${modules}${finder(0, 0)}${finder(0, size - 7)}${finder(size - 7, 0)}</svg>`;
  }

  function pixWidget(step) {
    const pix = step.widget?.type === "pix" ? step.widget : null;
    if (!pix) return "";
    const qr = `<div class="pixw__qr">${fakeQr(pix.code)}</div>`;
    if (paymentDone) {
      return `<div class="pixw">${qr}
        <div class="pixw__side">
          <span class="pixw__label">Pix</span>
          <div class="pixw__amount">${brl(pix.amount)}</div>
          <div class="pixw__status"><span class="pix-dot pix-dot--paid"></span>${copy.paid}</div>
          <div class="pixw__note">${copy.preparing}</div>
        </div>
      </div>`;
    }
    return `<div class="pixw">
      ${qr}
      <div class="pixw__side">
        <span class="pixw__label">Pix</span>
        <div class="pixw__amount">${brl(pix.amount)}</div>
        <span class="pixw__label">Copia e cola</span>
        <div class="pixw__code">${escapeHtml(pix.code)}</div>
        <div class="pixw__actions">
          <button class="btn btn--sm" data-copy="${escapeHtml(pix.code)}">${copy.copyCode}</button>
          <button class="btn btn--primary btn--sm" id="pix-pay">${copy.simulatePayment}</button>
        </div>
        <div class="pixw__status"><span class="pix-dot pix-dot--wait"></span>${copy.awaiting}</div>
      </div>
    </div>`;
  }

  function orderWidget(step) {
    const order = step.widget?.type === "order" ? step.widget : null;
    if (!order) return "";
    return `<div class="orderw">
      <div class="orderw__head"><span class="orderw__check">✓</span>${copy.order}</div>
      <div class="orderw__rows">
        <div class="orderw__row"><span class="orderw__k">${copy.orderLabel}</span><span class="orderw__v">${escapeHtml(order.id)}</span></div>
        <div class="orderw__row"><span class="orderw__k">NF-e</span><span class="orderw__v">${escapeHtml(order.nfe)} · ${copy.authorized}</span></div>
        <div class="orderw__row"><span class="orderw__k">${copy.carrier}</span><span class="orderw__v">${escapeHtml(order.carrier)}</span></div>
        <div class="orderw__row"><span class="orderw__k">${copy.tracking}</span><span class="orderw__v track">${escapeHtml(order.tracking)} <button class="btn btn--sm" data-copy="${escapeHtml(order.tracking)}">${copy.copyTracking}</button></span></div>
        <div class="orderw__row"><span class="orderw__k">${copy.estimated}</span><span class="orderw__v">${escapeHtml(localized(order.eta))}</span></div>
      </div>
    </div>`;
  }

  function richWidget(step) {
    if (step.widget?.type === "products") return productWidget(step);
    if (step.widget?.type === "shipping") return shippingWidget(step);
    if (step.widget?.type === "pix") return pixWidget(step);
    if (step.widget?.type === "order") return orderWidget(step);
    return "";
  }

  function renderChat() {
    const step = steps[index];
    const messages = step.conversation || [];
    const rich = richWidget(step);
    const preferredActor = messages.some((message) => message.actor === "seller_agent")
      ? "seller_agent"
      : "buyer_agent";
    const richIndex = messages.map((message) => message.actor).lastIndexOf(preferredActor);
    byId("chat-kicker").textContent = conversationHeading(messages);
    byId("how-chat").innerHTML = messages.map((message, messageIndex) => {
      const actorClass = message.actor === "client"
        ? "client"
        : message.actor === "seller_agent" ? "seller" : "ai";
      const initials = message.actor === "client"
        ? "C"
        : message.actor === "seller_agent" ? (locale === "en" ? "SA" : "AV")
          : (locale === "en" ? "BA" : "AC");
      const actorLabel = message.actor_label
        ? localized(message.actor_label)
        : message.actor === "client" ? copy.client
          : message.actor === "seller_agent" ? copy.seller : copy.buyer;
      const widget = messageIndex === richIndex ? rich : "";
      return `<div class="chat__msg chat__msg--${actorClass} ${widget ? "chat__msg--rich" : ""}">
        <span class="chat__avatar">${initials}</span>
        <div class="chat__bubble"><span class="chat__who">${escapeHtml(actorLabel)}</span>${escapeHtml(localized(message.text))}${widget}</div>
      </div>`;
    }).join("");
    wireCopyButtons();
  }

  function wireCopyButtons() {
    const payButton = byId("pix-pay");
    if (payButton) {
      const paymentStepId = steps[index].id;
      payButton.addEventListener("click", () => {
        paymentDone = true;
        render();
        setTimeout(() => {
          if (steps[index]?.id === paymentStepId && index < steps.length - 1) {
            index += 1;
            render();
          }
        }, 1200);
      });
    }
    appRoot.querySelectorAll("button[data-copy]").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(button.dataset.copy);
        } catch {
          return;
        }
        const original = button.textContent;
        button.textContent = copy.copied;
        setTimeout(() => { button.textContent = original; }, 1400);
      });
    });
  }

  function render() {
    const step = steps[index];
    const waitingForPayment = step.widget?.type === "pix" && !paymentDone;
    byId("how-kicker").textContent = `${copy.step} ${index + 1} ${copy.of} ${steps.length}`;
    byId("how-title").textContent = localized(step.title);
    byId("how-narrative").textContent = localized(step.description);
    byId("how-progress").style.width = `${((index + 1) / steps.length) * 100}%`;
    byId("how-prev").disabled = index === 0;
    byId("how-next").disabled = index === steps.length - 1 || waitingForPayment;
    byId("how-uth").innerHTML = stepPanel(step);
    renderStepper();
    renderChat();
  }

  function renderStepper() {
    const paymentIndex = steps.findIndex((step) => step.widget?.type === "pix");
    byId("stepper").innerHTML = steps.map((step, stepIndex) => {
      const locked = !paymentDone && paymentIndex !== -1 && stepIndex > paymentIndex;
      const state = stepIndex === index
        ? "active"
        : stepIndex < index ? "done" : locked ? "locked" : "";
      return `<button class="stepper__dot ${state}" type="button" data-step-index="${stepIndex}"
        aria-label="${copy.step} ${stepIndex + 1}: ${escapeHtml(localized(step.title))}"
        ${locked ? "disabled" : ""}
        aria-current="${stepIndex === index ? "step" : "false"}">${stepIndex + 1}</button>`;
    }).join("");
    appRoot.querySelectorAll("[data-step-index]").forEach((button) => {
      button.addEventListener("click", () => {
        index = Number(button.dataset.stepIndex);
        render();
      });
    });
    byId("stepper").querySelector(".active")?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }

  function translateStaticUi() {
    byId("hero-eyebrow").textContent = copy.heroEyebrow;
    byId("hero-title").textContent = copy.heroTitle;
    byId("hero-copy").textContent = copy.heroCopy;
    byId("cast-client-title").textContent = copy.client;
    byId("cast-client-copy").textContent = copy.clientCopy;
    byId("cast-buyer-title").textContent = copy.buyer;
    byId("cast-buyer-copy").textContent = copy.buyerCopy;
    byId("cast-seller-title").textContent = copy.seller;
    byId("cast-seller-copy").textContent = copy.sellerCopy;
    byId("under-title").textContent = copy.under;
    byId("chat-kicker").textContent = copy.conversation;
    byId("how-prev").textContent = copy.previous;
    byId("how-next").textContent = copy.next;
    byId("how-reset").textContent = copy.reset;
  }

  async function loadSteps() {
    const manifestResponse = await fetch(new URL("manifest.json", snapshotsBase));
    if (!manifestResponse.ok) throw new Error(`manifest: ${manifestResponse.status}`);
    const manifest = await manifestResponse.json();
    const checkpoints = await Promise.all(manifest.steps.map(async (path) => {
      const response = await fetch(new URL(path, snapshotsBase));
      if (!response.ok) throw new Error(`${path}: ${response.status}`);
      return response.json();
    }));
    return checkpoints.flatMap((checkpoint) =>
      checkpoint.protocol.events.map((event, eventIndex) => ({
        ...event,
        id: `${checkpoint.id}-${eventIndex + 1}`,
        sourceId: checkpoint.id,
        eventIndex,
        eventCount: checkpoint.protocol.events.length,
        checkpoint,
      })),
    );
  }

  byId("how-next").addEventListener("click", () => {
    if (index < steps.length - 1) index += 1;
    render();
  });
  byId("how-prev").addEventListener("click", () => {
    if (index > 0) index -= 1;
    render();
  });
  byId("how-reset").addEventListener("click", () => {
    index = 0;
    paymentDone = false;
    render();
  });

  translateStaticUi();
  loadSteps()
    .then((loadedSteps) => {
      steps = loadedSteps;
      render();
    })
    .catch((error) => {
      byId("how-title").textContent = copy.loadError;
      console.error(error);
    });
})();
