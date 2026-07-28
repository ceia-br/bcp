(() => {
  const STYLE_OVERRIDES = `
    :host {
      display: block;
      width: 100%;
      color-scheme: dark;
    }

    .uth {
      position: relative;
      top: auto;
    }

    .uth__body {
      max-height: none;
      overflow: visible;
    }
  `;

  function adaptStyles(source) {
    return source
      .replaceAll(":root {", ":host {")
      .replaceAll("  html {", "  :host {")
      .replaceAll("  body {", "  :host {");
  }

  async function mountPlayground(host) {
    if (host.dataset.mounted === "true") return;
    host.dataset.mounted = "true";
    host.setAttribute("aria-busy", "true");
    host.closest(".md-content__inner")?.querySelector(":scope > h1")?.remove();

    try {
      const response = await fetch(new URL(host.dataset.source, window.location.href), {
        cache: "no-cache",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const parsed = new DOMParser().parseFromString(await response.text(), "text/html");
      const main = parsed.querySelector("main.shell");
      const applicationScript = parsed.querySelector("body > script:last-of-type");
      const applicationSource = applicationScript?.getAttribute("src");
      if (!main || !applicationScript || !applicationSource) {
        throw new Error("estrutura do Playground incompleta");
      }
      const applicationUrl = new URL(applicationSource, response.url);
      const applicationResponse = await fetch(applicationUrl, { cache: "no-cache" });
      if (!applicationResponse.ok) throw new Error(`HTTP ${applicationResponse.status}`);

      const shadow = host.shadowRoot || host.attachShadow({ mode: "open" });
      shadow.replaceChildren();

      const styles = document.createElement("style");
      styles.textContent = adaptStyles(
        [...parsed.querySelectorAll("style")].map((style) => style.textContent).join("\n")
      ) + STYLE_OVERRIDES;
      shadow.append(styles, document.importNode(main, true));

      const script = document.createElement("script");
      script.dataset.lang = host.dataset.lang;
      for (const [name, value] of Object.entries(applicationScript.dataset)) {
        script.dataset[name] = name === "snapshots"
          ? new URL(value, applicationUrl).href
          : value;
      }
      host.dataset.snapshotsBase = script.dataset.snapshots;
      script.textContent = await applicationResponse.text();
      window.__bcpPlaygroundMountRoot = shadow;
      try {
        shadow.append(script);
      } finally {
        delete window.__bcpPlaygroundMountRoot;
      }

      host.removeAttribute("aria-busy");
    } catch (error) {
      host.dataset.mounted = "false";
      host.removeAttribute("aria-busy");
      host.textContent = `Não foi possível carregar o Playground: ${error.message}`;
    }
  }

  function mountAll() {
    document.querySelectorAll("[data-bcp-playground]").forEach(mountPlayground);
  }

  mountAll();
  window.document$?.subscribe(mountAll);
})();
