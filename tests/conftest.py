"""Fixtures: marca de teste (logo marcador de posição) e mídia sintética gerada pelo ffmpeg."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from facilita_studio.marca import Marca

RAIZ = Path(__file__).resolve().parent.parent

if not os.environ.get("CHROMIUM_PATH") and Path("/opt/pw-browsers/chromium").exists():
    os.environ["CHROMIUM_PATH"] = "/opt/pw-browsers/chromium"


def ff(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


@pytest.fixture
def marca(tmp_path) -> Marca:
    pasta = tmp_path / "marca"
    (pasta / "logo").mkdir(parents=True)
    shutil.copy(RAIZ / "marca" / "marca.yaml", pasta / "marca.yaml")
    img = Image.new("RGBA", (600, 150), (0, 0, 0, 255))
    ImageDraw.Draw(img).rectangle((20, 20, 580, 130), fill=(232, 87, 42, 255))
    img.save(pasta / "logo" / "laranja-principal.png")
    (pasta / "selo").mkdir()
    selo = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(selo).ellipse((0, 0, 299, 299), fill=(201, 153, 42, 255))
    selo.save(pasta / "selo" / "xpert-xcaret.png")
    return Marca.carregar(pasta)


@pytest.fixture(scope="session")
def midia(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("midia")
    ff("-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=4", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", p / "praia_horizontal.mp4")
    ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=30:d=4", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", p / "piscina_vertical.mp4")
    ff("-f", "lavfi", "-i", "sine=f=200:d=4:sample_rate=48000", "-af",
       "volume='0.5*(between(t,0,1.4)+between(t,1.8,3.6))':eval=frame", p / "narracao.wav")
    ff("-f", "lavfi", "-i", "sine=f=500:d=10:sample_rate=48000", "-af", "volume=0.8", p / "trilha.mp3")
    return p


def criar_roteiro(pasta: Path, midia: Path, extra_meta: str = "", blocos: str | None = None) -> tuple[Path, Path]:
    roteiro = pasta / "roteiro.md"
    roteiro.write_text(
        f"""---
titulo: Teste Praia
narracao: {midia / 'narracao.wav'}
musica: {midia / 'trilha.mp3'}
musica_origem: Artlist
cta: Comente PRAIA
respiro_final: 1.5
{extra_meta}---

""" + (blocos or """## Bloco 1 · Abertura
- tempo: 0:00–0:01.6
- imagem: praia
- tela: Abertura

Primeira fala.

## Bloco 2 · Piscina
- tempo: 0:01.6–0:04
- imagem: piscina
- tela: Piscina
- transicao: fade

Segunda fala. [pausa 0.3s]
"""), encoding="utf-8")
    clips = pasta / "clips.yaml"
    clips.write_text(
        f"""clips:
  - arquivo: {midia / 'praia_horizontal.mp4'}
    origem: Gravação do Richard
    descricao: praia e mar
  - arquivo: {midia / 'piscina_vertical.mp4'}
    origem: Drive oficial Xcaret
    descricao: piscina
""", encoding="utf-8")
    return roteiro, clips
