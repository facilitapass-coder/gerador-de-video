#!/usr/bin/env bash
# Gera o arquivo de venda do plugin: plugin/dist/facilita-studio-v<versão>.zip
#   bash plugin/empacotar.sh
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
ORIGEM="$AQUI/facilita-studio"
VERSAO="$(python3 -c "import json;print(json.load(open('$ORIGEM/.claude-plugin/plugin.json'))['version'])")"
DIST="$AQUI/dist"; mkdir -p "$DIST"
TMP="$(mktemp -d)"
# copia só o que vai para o cliente (sem dependências, testes ou mídia)
(cd "$ORIGEM" && tar --exclude node_modules --exclude ./modelo/projetos --exclude './modelo/public/pecas/*' \
  --exclude out --exclude .DS_Store --exclude .git -cf - .) | (mkdir -p "$TMP/facilita-studio" && cd "$TMP/facilita-studio" && tar -xf -)
# nada de mídia ou segredo dentro do pacote
if find "$TMP" \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.wav' -o -iname '.env' \) | grep -q .; then
  echo "Encontrei mídia ou .env no pacote. Abortei."; exit 1
fi
ARQ="$DIST/facilita-studio-v$VERSAO.zip"
rm -f "$ARQ"
(cd "$TMP" && zip -qr -X "$ARQ" facilita-studio)
rm -rf "$TMP"
echo "Pacote: $ARQ ($(du -h "$ARQ" | cut -f1))"
