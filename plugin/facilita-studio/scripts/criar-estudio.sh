#!/usr/bin/env bash
# Cria o espaço de criação do cliente a partir do modelo do plugin.
#   bash criar-estudio.sh <pasta-destino>
set -euo pipefail
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="${1:?Informe a pasta de destino}"
if [ -e "$DESTINO/package.json" ]; then echo "Já existe um estúdio em $DESTINO (nada foi alterado)."; exit 0; fi
mkdir -p "$DESTINO"
# copia o modelo sem dependências nem peças de teste
(cd "$PLUGIN/modelo" && tar --exclude node_modules --exclude ./projetos --exclude './public/pecas/*' --exclude out -cf - .) | (cd "$DESTINO" && tar -xf -)
mkdir -p "$DESTINO/projetos" "$DESTINO/public/pecas" "$DESTINO/public/marca" "$DESTINO/public/fontes"
[ -f "$DESTINO/CLAUDE.estudio.md" ] && mv "$DESTINO/CLAUDE.estudio.md" "$DESTINO/CLAUDE.md"
mkdir -p "$DESTINO/ferramentas"
cp "$PLUGIN/scripts/estudio.py" "$PLUGIN/scripts/checar-ambiente.sh" "$DESTINO/ferramentas/"
cd "$DESTINO"
echo "Instalando o Remotion (pode levar alguns minutos)..."
npm install --no-audit --no-fund --loglevel=error
npx tsc --noEmit && echo "Estúdio criado em $(pwd)"
