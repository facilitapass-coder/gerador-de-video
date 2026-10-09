"""Análise: quadros a cada 2 s, folha de contato e volume médio da voz."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..marca import Marca
from ..util import ffmpeg, formatar_tempo
from .importacao import sondar


def extrair_quadros(clip: Path, pasta: Path, intervalo: float = 2.0, largura: int = 360) -> list[tuple[float, Path]]:
    """Um quadro a cada `intervalo` segundos, começando em t=0."""
    pasta.mkdir(parents=True, exist_ok=True)
    for antigo in pasta.glob("q_*.jpg"):
        antigo.unlink()
    ffmpeg(
        ["-i", clip, "-vf", f"fps=1/{intervalo},scale={largura}:-2", "-q:v", "4", str(pasta / "q_%04d.jpg")],
        f"extrair quadros de {clip.name}",
    )
    quadros = sorted(pasta.glob("q_*.jpg"))
    return [(i * intervalo, q) for i, q in enumerate(quadros)]


def folha_de_contato(
    quadros: list[tuple[float, Path]], destino: Path, titulo: str, marca: Marca, colunas: int = 5
) -> Path:
    """Grade com os quadros e o tempo de cada um, para escolher trechos sem abrir o vídeo."""
    if not quadros:
        raise ValueError("sem quadros")
    with Image.open(quadros[0][1]) as primeiro:
        w, h = primeiro.size
    escala = 260 / max(w, h)
    tw, th = int(w * escala), int(h * escala)
    rotulo, margem, cab = 28, 12, 60
    linhas = (len(quadros) + colunas - 1) // colunas
    folha = Image.new("RGB", (margem + colunas * (tw + margem), cab + linhas * (th + rotulo + margem)), marca.cor_rgb("marinho"))
    d = ImageDraw.Draw(folha)
    f_tit = ImageFont.truetype(str(marca.fonte_ttf("negrito")), 26)
    f_rot = ImageFont.truetype(str(marca.fonte_ttf("regular")), 18)
    d.text((margem, 16), titulo, font=f_tit, fill="white")
    for i, (t, caminho) in enumerate(quadros):
        x = margem + (i % colunas) * (tw + margem)
        y = cab + (i // colunas) * (th + rotulo + margem)
        with Image.open(caminho) as q:
            folha.paste(q.resize((tw, th)), (x, y))
        d.text((x + 4, y + th + 3), formatar_tempo(t), font=f_rot, fill=marca.cores["laranja"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    folha.save(destino, quality=88)
    return destino


def medir_volume(arquivo: Path, inicio: float | None = None, duracao: float | None = None) -> dict:
    """Volume médio e de pico em dBFS (volumedetect)."""
    args = []
    if inicio is not None:
        args += ["-ss", f"{inicio:.3f}"]
    if duracao is not None:
        args += ["-t", f"{duracao:.3f}"]
    proc = ffmpeg([*args, "-i", arquivo, "-vn", "-af", "volumedetect", "-f", "null", "-"], f"medir volume de {Path(arquivo).name}")
    media = re.search(r"mean_volume:\s*(-?[\d.]+|-inf) dB", proc.stderr)
    pico = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", proc.stderr)
    conv = lambda m: float("-inf") if not m or m.group(1) == "-inf" else float(m.group(1))  # noqa: E731
    return {"media_db": conv(media), "pico_db": conv(pico)}


def detectar_silencios(arquivo: Path, limiar_db: float = -35, minimo: float = 0.25) -> list[tuple[float, float]]:
    """Pausas da narração: lista de (início, fim) em segundos."""
    proc = ffmpeg(
        ["-i", arquivo, "-vn", "-af", f"silencedetect=noise={limiar_db}dB:d={minimo}", "-f", "null", "-"],
        f"detectar pausas em {Path(arquivo).name}",
    )
    inicios = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", proc.stderr)]
    fins = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", proc.stderr)]
    return [(max(0.0, a), b) for a, b in zip(inicios, fins)]


def analisar(clips: list[Path], pasta_saida: Path, marca: Marca, intervalo: float = 2.0) -> list[dict]:
    resultados = []
    for clip in clips:
        info = sondar(clip)
        item = {"arquivo": str(clip), **info.resumo()}
        base = pasta_saida / clip.stem
        if info.tipo == "video":
            quadros = extrair_quadros(clip, base / "quadros", intervalo)
            folha = folha_de_contato(
                quadros, base / f"{clip.stem}_folha.jpg", f"{clip.name} · {info.duracao:.1f}s · {info.orientacao}", marca
            )
            item.update(quadros=len(quadros), folha_de_contato=str(folha))
        if info.tem_audio:
            item["volume"] = medir_volume(clip)
        resultados.append(item)
    return resultados
