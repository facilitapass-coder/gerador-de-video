"""Gera mídia sintética (clips, narração, música, logo e foto de teste) em exemplos/amostras/.

Serve só para experimentar a ferramenta sem os arquivos reais. Nada aqui é material
de marca: o logo é um marcador de posição com fundo preto (para testar a correção de
alfa) e os clips são padrões de teste do ffmpeg.

    python exemplos/gerar_amostras.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PASTA = Path(__file__).parent / "amostras"
RAIZ = Path(__file__).resolve().parent.parent
CANDIDATAS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONTE = next((f for f in CANDIDATAS if Path(f).exists()), None)


def fonte(tamanho: int):
    return ImageFont.truetype(FONTE, tamanho) if FONTE else ImageFont.load_default(size=tamanho)


def _fonte_ffmpeg() -> str:
    """Caminho da fonte escapado para o drawtext (C:/... vira C\\:/...)."""
    return FONTE.replace(":", "\\\\:").replace(" ", "\\\\ ") if FONTE else ""


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def clip(nome: str, w: int, h: int, dur: float, cor: str) -> None:
    rotulo = nome.replace("_", " ").upper()
    texto = (f",drawtext=fontfile={_fonte_ffmpeg()}:text='{rotulo}':fontsize={h // 12}:fontcolor=white:"
             f"x=(w-tw)/2:y=(h-th)/2:box=1:boxcolor=black@0.5") if FONTE else ""
    ff("-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=30:d={dur}",
       "-f", "lavfi", "-i", f"color=c={cor}:s={w}x{h}:r=30:d={dur}",
       "-filter_complex",
       f"[0:v][1:v]blend=all_mode=overlay:all_opacity=0.6{texto}",
       "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(PASTA / f"{nome}.mp4"))


def narracao(dur: float, falas: list[tuple[float, float]]) -> None:
    """Imita uma voz: tom modulado nos trechos de fala, silêncio nas pausas."""
    expr = "+".join(f"between(t,{a},{b})" for a, b in falas)
    ff("-f", "lavfi", "-i", f"sine=f=180:d={dur}:sample_rate=48000",
       "-af", f"tremolo=f=5:d=0.6,volume='0.5*({expr})':eval=frame", str(PASTA / "narracao.wav"))


def musica(dur: float) -> None:
    ff("-f", "lavfi", "-i", f"sine=f=440:d={dur}:sample_rate=48000",
       "-f", "lavfi", "-i", f"sine=f=660:d={dur}:sample_rate=48000",
       "-filter_complex", "[0:a][1:a]amix=inputs=2,volume=0.8", "-c:a", "libmp3lame", "-q:a", "4",
       str(PASTA / "trilha.mp3"))


def logo() -> None:
    img = Image.new("RGB", (900, 200), "black")  # fundo preto de propósito
    d = ImageDraw.Draw(img)
    d.ellipse((20, 30, 160, 170), fill="#E8572A")
    d.text((190, 55), "LOGO EXEMPLO", font=fonte(80), fill="#E8572A")
    img.save(PASTA / "logo-exemplo-fundo-preto.png")


def foto(nome: str, w: int = 1600, h: int = 1200) -> None:
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(40 + 120 * t), int(150 - 60 * t), int(200 - 80 * t)))
    d.text((60, 60), "FOTO DE TESTE", font=fonte(70), fill="white")
    img.save(PASTA / nome, quality=90)


def marca_teste() -> Path:
    """Pasta de marca só para teste: marca.yaml real + logo e selo marcadores de posição."""
    pasta = PASTA / "marca-teste"
    for sub in ("logo", "selo"):
        (pasta / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy(RAIZ / "marca" / "marca.yaml", pasta / "marca.yaml")
    shutil.copy(PASTA / "logo-exemplo-fundo-preto.png", pasta / "logo" / "laranja-principal.png")
    selo = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(selo).ellipse((0, 0, 299, 299), fill="#C9992A")
    selo.save(pasta / "selo" / "xpert-xcaret.png")
    return pasta


def main() -> int:
    PASTA.mkdir(parents=True, exist_ok=True)
    clip("fachada_drone", 1920, 1080, 12, "0x1d6fa5")   # horizontal
    clip("piscina_rooftop", 1080, 1920, 10, "0x2aa5a0")  # vertical
    clip("quarto_suite", 1920, 1080, 8, "0x8a6d3b")
    clip("restaurante_prato", 1080, 1920, 9, "0xa53b2a")
    clip("arte_mural", 1920, 1080, 10, "0x6a3ba5")
    clip("show_noite", 1920, 1080, 6, "0x202050")
    falas = [(0.2, 5.6), (6.1, 12.5), (13.0, 19.6), (20.1, 26.4), (26.9, 33.0), (33.6, 39.4), (39.9, 44.6)]
    narracao(45.0, falas)
    musica(60.0)
    logo()
    foto("piscina_teste.jpg")
    foto("quarto_teste.jpg")
    marca_teste()
    print(f"Amostras em {PASTA} (marca de teste em {PASTA / 'marca-teste'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
