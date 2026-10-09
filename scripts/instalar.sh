#!/usr/bin/env bash
# Instala o Facilita Studio no computador (macOS ou Linux).
#   bash scripts/instalar.sh            instala
#   bash scripts/instalar.sh --teste    instala e gera peças de teste com mídia sintética
set -euo pipefail
cd "$(dirname "$0")/.."
RAIZ="$(pwd)"

echo "== Facilita Studio: instalação em $RAIZ"

# 1. Python 3.10+
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Preciso do Python 3.10 ou mais novo."
  [ "$(uname)" = "Darwin" ] && echo "No Mac: brew install python@3.12  (Homebrew: https://brew.sh)"
  exit 1
fi
echo "Python: $($PY --version)"

# 2. ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    read -r -p "ffmpeg não encontrado. Instalar agora com Homebrew (brew install ffmpeg)? [s/N] " r
    if [[ "$r" =~ ^[sS]$ ]]; then brew install ffmpeg; else echo "Instale o ffmpeg e rode de novo."; exit 1; fi
  else
    echo "Instale o ffmpeg (Mac: brew install ffmpeg · Ubuntu: sudo apt install ffmpeg) e rode de novo."
    exit 1
  fi
fi
echo "ffmpeg: $(ffmpeg -version | head -1)"

# 3. Ambiente Python isolado em .venv
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -e '.[dev]'

# 4. Chromium do Playwright (renderiza as imagens). Com CHROMIUM_PATH definido, usa esse navegador.
if [ -z "${CHROMIUM_PATH:-}" ]; then
  .venv/bin/python -m playwright install chromium \
    || echo "AVISO: não baixei o Chromium. As imagens não vão sair até rodar: .venv/bin/python -m playwright install chromium"
fi

# 5. Pastas de trabalho
mkdir -p projetos saida

echo
echo "== Conferindo a marca"
.venv/bin/facilita marca || true

if [ "${1:-}" = "--teste" ]; then
  echo
  echo "== Teste com mídia sintética (exemplos/amostras)"
  .venv/bin/python exemplos/gerar_amostras.py
  M=exemplos/amostras/marca-teste
  .venv/bin/facilita --marca "$M" imagem exemplos/oferta-xcaret.yaml --formato feed --formato story --permitir-fonte-substituta
  .venv/bin/facilita --marca "$M" cobertura exemplos/xcaret-arte/roteiro.md --clips exemplos/xcaret-arte/clips.yaml
  echo
  echo "Teste ok. Imagens em saida/imagens/. Para um Reels de teste (leva 1–2 min):"
  echo "  .venv/bin/facilita --marca $M montar exemplos/xcaret-arte/roteiro.md --clips exemplos/xcaret-arte/clips.yaml --previa --permitir-fonte-substituta"
fi

cat <<FIM

Pronto. Para usar, em cada terminal novo:
  cd "$RAIZ"
  source .venv/bin/activate
  facilita novo "Xcaret Arte"        # cria projetos/xcaret-arte/ com clips/, audio/, fotos/ e modelos
  facilita --help

Antes da primeira peça real, copie para a pasta marca/:
  - fontes/Poppins-*.ttf   (marca/fontes/LEIA-ME.md)
  - logo/laranja-principal.png   (marca/logo/LEIA-ME.md)
  - selo/xpert-xcaret.png        (marca/selo/LEIA-ME.md), se for usar o selo
FIM
