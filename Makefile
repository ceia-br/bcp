.DEFAULT_GOAL := help

DOCS_LABEL := draft
DOCS_CONFIG := mkdocs.yml
DOCS_EN_CONFIG := mkdocs.en.yml
DOCS_SITE_ROOT ?= $(CURDIR)/site
DOCS_SITE_DIR ?= $(DOCS_SITE_ROOT)/$(DOCS_LABEL)

.PHONY: help install check validate playground-check playground-fonts docs-build docs-serve docs-clean

help: ## Lista os comandos disponiveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Instala as dependencias de docs
	uv sync --group docs

check: validate playground-check ## Valida protocolo e snapshots do playground

validate: ## Validador local dos schemas e fixtures (+ lint ucp-schema, se instalado)
	scripts/validate.sh

playground-check: ## Valida e compara os snapshots estaticos do playground
	uv run --group playground python playground/generate.py --check

playground-fonts: ## Regenera os subsets WOFF2 das fontes do playground
	uv run --group fonts python scripts/vendor_playground_fonts.py

docs-build: ## Monta o rascunho do site local em site/draft
	SITE_URL=$${SITE_URL:-https://bcp.dev.br/$(DOCS_LABEL)/} \
	BCP_PT_URL=$${BCP_PT_URL:-/$(DOCS_LABEL)/} \
	BCP_EN_URL=$${BCP_EN_URL:-/$(DOCS_LABEL)/en/} \
	MKDOCS_SITE_DIR=$(DOCS_SITE_DIR) \
	uv run --group docs mkdocs build --strict -f $(DOCS_CONFIG)
	SITE_URL=$${SITE_URL:-https://bcp.dev.br/$(DOCS_LABEL)/}en/ \
	BCP_PT_URL=$${BCP_PT_URL:-/$(DOCS_LABEL)/} \
	BCP_EN_URL=$${BCP_EN_URL:-/$(DOCS_LABEL)/en/} \
	MKDOCS_SITE_DIR=$(DOCS_SITE_DIR)/en \
	uv run --group docs mkdocs build --strict -f $(DOCS_EN_CONFIG)
	@mkdir -p "$(DOCS_SITE_ROOT)"
	@mkdir -p "$(DOCS_SITE_ROOT)/en"
	@rm -rf "$(DOCS_SITE_ROOT)/latest"
	@ln -s "$(DOCS_LABEL)" "$(DOCS_SITE_ROOT)/latest"
	@printf '%s\n' \
		'[' \
		'  {' \
		'    "version": "$(DOCS_LABEL)",' \
		'    "title": "$(DOCS_LABEL)",' \
		'    "aliases": ["latest"]' \
		'  }' \
		']' \
		> "$(DOCS_SITE_ROOT)/versions.json"
	@cp "$(DOCS_SITE_ROOT)/versions.json" "$(DOCS_SITE_DIR)/versions.json"
	@printf '%s\n' \
		'<!doctype html>' \
		'<html lang="pt-BR">' \
		'<head>' \
		'  <meta charset="utf-8">' \
		'  <meta name="viewport" content="width=device-width, initial-scale=1">' \
		'  <meta http-equiv="refresh" content="0; url=$(DOCS_LABEL)/">' \
		'  <link rel="canonical" href="$(DOCS_LABEL)/">' \
		'  <title>BCP Docs</title>' \
		'  <script>location.replace("$(DOCS_LABEL)/" + location.search + location.hash)</script>' \
		'</head>' \
		'<body>' \
		'  <p><a href="$(DOCS_LABEL)/">Acessar a documentação mais recente do BCP.</a></p>' \
		'</body>' \
		'</html>' \
		> "$(DOCS_SITE_ROOT)/index.html"
	@printf '%s\n' \
		'<!doctype html>' \
		'<html lang="en">' \
		'<head>' \
		'  <meta charset="utf-8">' \
		'  <meta name="viewport" content="width=device-width, initial-scale=1">' \
		'  <meta http-equiv="refresh" content="0; url=../$(DOCS_LABEL)/en/">' \
		'  <link rel="canonical" href="../$(DOCS_LABEL)/en/">' \
		'  <title>BCP Docs — English</title>' \
		'  <script>location.replace("../$(DOCS_LABEL)/en/" + location.search + location.hash)</script>' \
		'</head>' \
		'<body>' \
		'  <p><a href="../$(DOCS_LABEL)/en/">Open the latest BCP documentation in English.</a></p>' \
		'</body>' \
		'</html>' \
		> "$(DOCS_SITE_ROOT)/en/index.html"

docs-serve: docs-build ## Sobe preview local do site em /
	uv run --group docs python -m http.server $${PORT:-8000} --bind 0.0.0.0 --directory site

docs-clean: ## Remove o site local gerado
	rm -rf site
