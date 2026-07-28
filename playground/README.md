# Playground

Fonte do playground estático publicado pelo MkDocs.

`scenario.json` contém apenas as entradas determinísticas. `generate.py` produz
os arquivos de `snapshots/`, que são consumidos pelo JavaScript sem executar
backend, agentes ou provedores externos.

`web/` contém somente a interface estática publicada dentro da página MkDocs.
O hook copia esse diretório para `playground/app/` no site gerado, preservando
os caminhos públicos existentes sem depender de qualquer pacote em `apps/`.

Os dados apresentados como protocolo devem ser gerados e validados. Textos de
interface ficam nos snapshots por idioma; CSS e JavaScript não devem conter
payloads BCP ou A2A escritos manualmente.

Para verificar que os snapshots estão atualizados:

```bash
uv run python playground/generate.py --check
```
