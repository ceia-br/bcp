(() => {
  const root = document.getElementById("bcp-playground");
  const script = document.currentScript;
  if (!root || !script) return;

  const locale = root.dataset.locale === "en" ? "en" : "pt-BR";
  const labels = {
    "pt-BR": {
      previous: "Voltar",
      next: "Avançar",
      reset: "Reiniciar",
      conversation: "Conversa",
      protocol: "Estado dos protocolos",
      noProtocol: "Esta etapa não possui payload protocolar estruturado.",
      request: "Requisição",
      response: "Resposta",
      checkout: "Checkout BCP",
      ap2: "AP2",
      step: "Checkpoint",
      stepNavigation: "Navegação entre checkpoints",
      loadError: "Não foi possível carregar o cenário estático.",
    },
    en: {
      previous: "Previous",
      next: "Next",
      reset: "Reset",
      conversation: "Conversation",
      protocol: "Protocol state",
      noProtocol: "This step has no structured protocol payload.",
      request: "Request",
      response: "Response",
      checkout: "BCP checkout",
      ap2: "AP2",
      step: "Checkpoint",
      stepNavigation: "Checkpoint navigation",
      loadError: "The static scenario could not be loaded.",
    },
  }[locale];
  const assetBase = new URL("./", script.src);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function localized(value) {
    if (!value || typeof value !== "object") return value;
    return value[locale] ?? value["pt-BR"] ?? value.en;
  }

  function codeBlock(title, value) {
    if (value === undefined || value === null) return null;
    const section = element("section", "bcp-pg-code");
    section.append(element("h4", "bcp-pg-code__title", title));
    const pre = element("pre", "bcp-pg-code__body");
    pre.setAttribute("aria-label", title);
    pre.tabIndex = 0;
    pre.textContent = JSON.stringify(value, null, 2);
    section.append(pre);
    return section;
  }

  async function loadScenario() {
    const manifestResponse = await fetch(new URL("snapshots/manifest.json", assetBase));
    if (!manifestResponse.ok) throw new Error(`manifest: ${manifestResponse.status}`);
    const manifest = await manifestResponse.json();
    const steps = await Promise.all(
      manifest.steps.map(async (path) => {
        const response = await fetch(new URL(`snapshots/${path}`, assetBase));
        if (!response.ok) throw new Error(`${path}: ${response.status}`);
        return response.json();
      }),
    );
    return { manifest, steps };
  }

  function buildShell(manifest, steps) {
    root.replaceChildren();
    root.className = "bcp-pg";

    const metadata = element("div", "bcp-pg-meta");
    for (const [name, value] of Object.entries(manifest.protocols)) {
      metadata.append(element("span", "bcp-pg-badge", `${name} ${value}`));
    }
    root.append(metadata);

    const progress = element("nav", "bcp-pg-progress");
    progress.setAttribute("aria-label", labels.stepNavigation);
    root.append(progress);

    const heading = element("header", "bcp-pg-heading");
    heading.setAttribute("aria-atomic", "true");
    heading.setAttribute("aria-live", "polite");
    const kicker = element("p", "bcp-pg-kicker");
    const title = element("h2", "bcp-pg-title");
    const narrative = element("p", "bcp-pg-narrative");
    heading.append(kicker, title, narrative);
    root.append(heading);

    const columns = element("div", "bcp-pg-columns");
    const conversation = element("section", "bcp-pg-panel");
    conversation.append(element("h3", "bcp-pg-panel__title", labels.conversation));
    const messages = element("div", "bcp-pg-messages");
    conversation.append(messages);

    const protocol = element("section", "bcp-pg-panel");
    protocol.append(element("h3", "bcp-pg-panel__title", labels.protocol));
    const protocolBody = element("div", "bcp-pg-protocol");
    protocol.append(protocolBody);
    columns.append(conversation, protocol);
    root.append(columns);

    const controls = element("div", "bcp-pg-controls");
    const previous = element("button", "md-button", labels.previous);
    const reset = element("button", "md-button", labels.reset);
    const next = element("button", "md-button md-button--primary", labels.next);
    for (const button of [previous, reset, next]) button.type = "button";
    controls.append(previous, reset, next);
    root.append(controls);

    let index = 0;

    function render() {
      const step = steps[index];
      kicker.textContent = `${labels.step} ${index + 1} / ${steps.length} · ${localized(step.act)}`;
      title.textContent = localized(step.title);
      narrative.textContent = localized(step.narrative);

      progress.replaceChildren();
      steps.forEach((item, itemIndex) => {
        const button = element("button", "bcp-pg-progress__step", String(itemIndex + 1));
        button.type = "button";
        button.title = localized(item.title);
        button.setAttribute("aria-label", `${labels.step} ${itemIndex + 1}: ${localized(item.title)}`);
        if (itemIndex === index) button.setAttribute("aria-current", "step");
        if (itemIndex < index) button.classList.add("is-complete");
        button.addEventListener("click", () => {
          index = itemIndex;
          render();
        });
        progress.append(button);
      });

      messages.replaceChildren();
      for (const message of step.conversation) {
        const article = element("article", `bcp-pg-message bcp-pg-message--${message.actor}`);
        article.append(element("strong", "bcp-pg-message__actor", localized(message.actor_label)));
        article.append(element("p", "bcp-pg-message__text", localized(message.text)));
        messages.append(article);
      }

      protocolBody.replaceChildren();
      const data = step.protocol;
      if (!data) {
        protocolBody.append(element("p", "bcp-pg-empty", labels.noProtocol));
      } else {
        const badgeRow = element("div", "bcp-pg-protocol__badges");
        for (const badge of data.badges ?? []) {
          badgeRow.append(element("span", "bcp-pg-badge", badge));
        }
        protocolBody.append(badgeRow);
        for (const block of [
          codeBlock(labels.request, data.request),
          codeBlock(labels.response, data.response),
          codeBlock(labels.checkout, data.checkout),
          codeBlock(labels.ap2, data.ap2),
        ]) {
          if (block) protocolBody.append(block);
        }
      }

      previous.disabled = index === 0;
      next.disabled = index === steps.length - 1;
    }

    previous.addEventListener("click", () => {
      if (index > 0) index -= 1;
      render();
    });
    next.addEventListener("click", () => {
      if (index < steps.length - 1) index += 1;
      render();
    });
    reset.addEventListener("click", () => {
      index = 0;
      render();
    });
    render();
  }

  loadScenario()
    .then(({ manifest, steps }) => buildShell(manifest, steps))
    .catch((error) => {
      const message = element("p", "bcp-pg-error", labels.loadError);
      message.setAttribute("role", "alert");
      root.replaceChildren(message);
      console.error(error);
    });
})();
