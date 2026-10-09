"""Importação: lê resolução, duração e orientação de clips e áudios."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..util import ErroFacilita, exigir_programa, rodar

EXT_VIDEO = {".mp4", ".mov", ".m4v"}
EXT_AUDIO = {".wav", ".m4a", ".mp3", ".aac"}


@dataclass
class InfoMidia:
    arquivo: str
    tipo: str  # "video" | "audio"
    duracao: float
    largura: int = 0
    altura: int = 0
    rotacao: int = 0
    fps: float = 0.0
    tem_audio: bool = False

    @property
    def largura_efetiva(self) -> int:
        """Dimensão como o ffmpeg vai exibir (ele aplica a rotação do celular)."""
        return self.altura if self.rotacao in (90, 270) else self.largura

    @property
    def altura_efetiva(self) -> int:
        return self.largura if self.rotacao in (90, 270) else self.altura

    @property
    def orientacao(self) -> str:
        if self.tipo != "video":
            return "-"
        w, h = self.largura_efetiva, self.altura_efetiva
        if h > w:
            return "vertical"
        return "horizontal" if w > h else "quadrado"

    def resumo(self) -> dict:
        d = asdict(self)
        d.update(orientacao=self.orientacao, largura_efetiva=self.largura_efetiva, altura_efetiva=self.altura_efetiva)
        return d


def _rotacao(stream: dict) -> int:
    rot = stream.get("tags", {}).get("rotate")
    for sd in stream.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = sd["rotation"]
    try:
        return int(float(rot or 0)) % 360
    except ValueError:
        return 0


def _fps(texto: str | None) -> float:
    if not texto or texto == "0/0":
        return 0.0
    num, _, den = texto.partition("/")
    return float(num) / float(den or 1)


def sondar(caminho: Path | str) -> InfoMidia:
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroFacilita(f"Arquivo não encontrado: {caminho}")
    ext = caminho.suffix.lower()
    if ext not in EXT_VIDEO | EXT_AUDIO:
        raise ErroFacilita(f"Formato não aceito: {caminho.name} (aceitos: MP4, MOV, WAV, M4A, MP3).")
    exigir_programa("ffprobe")
    proc = rodar(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(caminho)],
        f"ler {caminho.name}",
    )
    dados = json.loads(proc.stdout)
    streams = dados.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic") != 1), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duracao = float(dados.get("format", {}).get("duration") or (video or audio or {}).get("duration") or 0)
    if video and ext in EXT_VIDEO:
        return InfoMidia(
            arquivo=str(caminho),
            tipo="video",
            duracao=duracao,
            largura=int(video.get("width", 0)),
            altura=int(video.get("height", 0)),
            rotacao=_rotacao(video),
            fps=_fps(video.get("avg_frame_rate") or video.get("r_frame_rate")),
            tem_audio=audio is not None,
        )
    if audio:
        return InfoMidia(arquivo=str(caminho), tipo="audio", duracao=duracao, tem_audio=True)
    raise ErroFacilita(f"{caminho.name} não tem faixa de vídeo nem de áudio legível.")


def listar_midias(entradas: list[Path | str]) -> list[Path]:
    arquivos: list[Path] = []
    for e in map(Path, entradas):
        if e.is_dir():
            arquivos += sorted(p for p in e.rglob("*") if p.suffix.lower() in EXT_VIDEO | EXT_AUDIO)
        else:
            arquivos.append(e)
    return arquivos


def tabela(infos: list[InfoMidia]) -> str:
    linhas = ["| Arquivo | Tipo | Duração (s) | Resolução | Orientação | Áudio |", "| --- | --- | --- | --- | --- | --- |"]
    for i in infos:
        res = f"{i.largura_efetiva}×{i.altura_efetiva}" if i.tipo == "video" else "-"
        linhas.append(
            f"| {Path(i.arquivo).name} | {i.tipo} | {i.duracao:.1f} | {res} | {i.orientacao} | {'sim' if i.tem_audio else 'não'} |"
        )
    return "\n".join(linhas)
