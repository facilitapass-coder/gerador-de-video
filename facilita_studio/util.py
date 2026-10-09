"""Funções compartilhadas: chamadas ao ffmpeg, caminhos de saída e manifestos."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Iterable, Sequence

from . import __version__


class ErroFacilita(Exception):
    """Erro com mensagem pensada para quem usa a ferramenta, não para quem programa."""


def exigir_programa(nome: str) -> str:
    caminho = shutil.which(nome)
    if not caminho:
        raise ErroFacilita(f"Programa '{nome}' não encontrado. Instale o ffmpeg (que inclui o ffprobe).")
    return caminho


def rodar(cmd: Sequence[str], descricao: str = "") -> subprocess.CompletedProcess:
    """Roda um comando e transforma falha em ErroFacilita com o final do log."""
    proc = subprocess.run(list(map(str, cmd)), capture_output=True, text=True)
    if proc.returncode != 0:
        cauda = "\n".join(proc.stderr.strip().splitlines()[-15:])
        raise ErroFacilita(f"Falha ao {descricao or 'rodar ' + str(cmd[0])}:\n{cauda}")
    return proc


def ffmpeg(args: Sequence[str], descricao: str = "") -> subprocess.CompletedProcess:
    exigir_programa("ffmpeg")
    return rodar(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args], descricao)


def sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def slug(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", sem_acentos(texto).lower()).strip("-")
    return s or "peca"


def impressao_arquivo(caminho: Path) -> dict:
    """Identifica um arquivo de origem (tamanho + hash do 1º MB) sem ler vídeos inteiros."""
    caminho = Path(caminho)
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        h.update(f.read(1024 * 1024))
    return {"arquivo": str(caminho), "bytes": caminho.stat().st_size, "sha256_1mb": h.hexdigest()}


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def garantir_saida_segura(destino: Path, origens: Iterable[Path]) -> None:
    """Originais intocados: recusa qualquer escrita sobre um arquivo de origem."""
    destino_r = Path(destino).resolve()
    for origem in origens:
        if origem is None:
            continue
        if Path(origem).resolve() == destino_r:
            raise ErroFacilita(f"Recusado: a saída {destino} sobrescreveria o arquivo original {origem}.")


def proxima_versao(pasta: Path, base: str, extensao: str) -> Path:
    """saida/<base>_v01.<ext>, _v02... Cada versão fica guardada; nada é sobrescrito."""
    pasta.mkdir(parents=True, exist_ok=True)
    n = 1
    while (pasta / f"{base}_v{n:02d}.{extensao}").exists():
        n += 1
    return pasta / f"{base}_v{n:02d}.{extensao}"


def salvar_manifesto(caminho: Path, dados: dict) -> Path:
    """Cada peça guarda roteiro, arquivos usados e parâmetros, para ser refeita igual."""
    dados = {"ferramenta": f"facilita-studio {__version__}", **dados}
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return caminho


def segundos(valor) -> float:
    """Aceita 12, 12.5, '12', '0:12', '1:02.5' e devolve segundos."""
    if valor is None:
        raise ValueError("tempo vazio")
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().lower().rstrip("s")
    partes = texto.split(":")
    total = 0.0
    for parte in partes:
        total = total * 60 + float(parte.replace(",", "."))
    return total


def formatar_tempo(s: float) -> str:
    m, resto = divmod(max(0.0, s), 60)
    return f"{int(m)}:{resto:04.1f}"
