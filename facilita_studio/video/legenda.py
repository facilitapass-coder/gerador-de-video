"""Legenda do post do Reels: texto, CTA e lembrete da e-Visa quando o destino é o México."""

from __future__ import annotations

from pathlib import Path

from ..marca import Marca, Problema
from ..util import sem_acentos
from .roteiro import Roteiro

DESTINOS_MEXICO = {"mexico", "cancun", "riviera maya", "playa del carmen", "xcaret", "tulum", "cozumel"}


def destino_mexico(rot: Roteiro) -> bool:
    texto = sem_acentos(" ".join(str(rot.meta.get(k, "")) for k in ("destino", "titulo"))).lower()
    return any(d in texto for d in DESTINOS_MEXICO)


def montar_legenda(rot: Roteiro, marca: Marca) -> tuple[str, list[Problema]]:
    partes = []
    corpo = str(rot.meta.get("legenda") or "").strip()
    if not corpo:
        corpo = rot.titulo
    partes.append(corpo)
    if rot.cta:
        partes.append(f"{rot.cta} que a gente te manda os detalhes.")
    if destino_mexico(rot):
        partes.append(marca.dados["avisos"]["evisa_mexico"].strip())
    hashtags = rot.meta.get("hashtags") or []
    if hashtags:
        partes.append(" ".join(h if str(h).startswith("#") else f"#{h}" for h in hashtags))
    texto = "\n\n".join(partes) + "\n"
    return texto, marca.verificar_texto(texto, "legenda")


def salvar_legenda(rot: Roteiro, marca: Marca, pasta_saida: Path) -> tuple[Path, list[Problema]]:
    texto, problemas = montar_legenda(rot, marca)
    pasta = Path(pasta_saida) / "reels" / rot.slug
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{rot.slug}_legenda.txt"
    destino.write_text(texto, encoding="utf-8")
    return destino, problemas
