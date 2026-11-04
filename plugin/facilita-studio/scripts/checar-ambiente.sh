#!/usr/bin/env bash
# Confere o que o Facilita Studio precisa no computador. Não instala nada sozinho.
MODELO="${FACILITA_WHISPER_MODELO:-$HOME/.facilita-studio/modelos/ggml-small.bin}"
falta=0
ok()   { printf "  ✅ %s\n" "$1"; }
erro() { printf "  ❌ %s\n     → %s\n" "$1" "$2"; falta=1; }
mac=0; [ "$(uname)" = "Darwin" ] && mac=1

echo "Facilita Studio · conferindo o computador"
if command -v node >/dev/null 2>&1 && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ]; then ok "Node $(node --version)"
else erro "Node 18 ou mais novo" "$([ $mac = 1 ] && echo 'brew install node' || echo 'https://nodejs.org (versão LTS)')"; fi
if command -v python3 >/dev/null 2>&1; then ok "$(python3 --version)"
else erro "Python 3" "$([ $mac = 1 ] && echo 'brew install python@3.12' || echo 'https://python.org')"; fi
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')"
  ffmpeg -hide_banner -filters 2>/dev/null | grep -q " aexciter " || printf "  ⚠️  ffmpeg sem o filtro aexciter: o perfil de voz 'abafado' não vai funcionar%s\n" "$([ $mac = 1 ] && echo ' (use brew install ffmpeg-full)')"
else erro "ffmpeg" "$([ $mac = 1 ] && echo 'brew install ffmpeg-full && brew link --force ffmpeg-full' || echo 'sudo apt install ffmpeg  ·  Windows: winget install Gyan.FFmpeg')"; fi
if command -v whisper-cli >/dev/null 2>&1; then ok "whisper-cli (transcrição local)"
else erro "whisper-cli (transcrição para legendas)" "$([ $mac = 1 ] && echo 'brew install whisper-cpp' || echo 'https://github.com/ggml-org/whisper.cpp')"; fi
if [ -f "$MODELO" ]; then ok "modelo do whisper em $MODELO"
else erro "modelo do whisper (ggml-small.bin, ~466 MB)" "mkdir -p \"$(dirname "$MODELO")\" && curl -L -o \"$MODELO\" https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"; fi

echo
if [ $falta = 0 ]; then echo "Tudo pronto."; else echo "Instale o que está com ❌ e rode de novo."; fi
exit $falta
