#!/usr/bin/env bash
# Instala o Facilita Studio a partir da pasta descompactada do .zip.
#   bash instalar.sh
# 1) copia o plugin para uma pasta fixa (~/facilita-studio, ou FACILITA_DESTINO)
# 2) registra e instala no Claude Code pelo comando `claude`, se ele existir
# 3) se não existir, mostra os dois comandos para colar no chat
set -euo pipefail
ORIGEM="$(cd "$(dirname "$0")" && pwd)"
DESTINO="${FACILITA_DESTINO:-$HOME/facilita-studio}"
case "$DESTINO" in ""|"/"|"$HOME"|"$HOME/") echo "Destino inválido: $DESTINO"; exit 1;; esac
VERSAO="$(python3 -c "import json;print(json.load(open('$ORIGEM/.claude-plugin/plugin.json'))['version'])" 2>/dev/null || echo "?")"

echo "== Facilita Studio v$VERSAO"
if [ "$ORIGEM" != "$DESTINO" ]; then
  mkdir -p "$DESTINO"
  # substitui a versão anterior inteira (o plugin não guarda dados do cliente)
  (cd "$ORIGEM" && tar --exclude node_modules --exclude .DS_Store -cf - .) | (cd "$DESTINO" && rm -rf ./skills ./scripts ./modelo && tar -xf -)
fi
echo "Plugin guardado em: $DESTINO (não apague esta pasta)"

if command -v claude >/dev/null 2>&1; then
  if claude plugin marketplace list 2>/dev/null | grep "facilita-studio" >/dev/null; then
    claude plugin marketplace update facilita-studio
  else
    claude plugin marketplace add "$DESTINO"
  fi
  claude plugin install facilita-studio@facilita-studio || true
  echo
  echo "Instalado. Abra uma conversa nova e escreva: quero começar o estúdio"
else
  echo
  echo "Falta um passo: cole estes dois comandos no chat do Claude Code, um de cada vez:"
  echo
  echo "  /plugin marketplace add $DESTINO"
  echo "  /plugin install facilita-studio@facilita-studio"
  echo
  echo "Depois abra uma conversa nova e escreva: quero começar o estúdio"
fi
