"""Fotos de fonte licenciada (origem obrigatória) e correção do canal alfa do logo."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from ..marca import Marca, Problema
from ..util import ErroFacilita, garantir_saida_segura, sem_acentos

EXT_FOTO = {".jpg", ".jpeg", ".png", ".webp"}


def verificar_fotos(fotos: list, base: Path, marca: Marca) -> tuple[list[Path], list[Problema]]:
    """Cada foto é {arquivo, origem}. Sem origem, ou de fonte não licenciada, é recusada."""
    caminhos, problemas = [], []
    for i, f in enumerate(fotos or []):
        if isinstance(f, str):
            f = {"arquivo": f}
        arquivo = Path(f.get("arquivo", ""))
        arquivo = arquivo if arquivo.is_absolute() else base / arquivo
        origem = f.get("origem")
        if origem and sem_acentos(str(origem)).lower().strip() in {"ia", "inteligencia artificial", "gerada por ia"}:
            problemas.append(Problema("erro", "imagem por IA ainda não é aceita (P1, só fundos e ilustrações, "
                                      "nunca hotel, quarto ou prato reais).", arquivo.name))
        else:
            problemas += marca.verificar_origem(origem, arquivo.name or f"foto {i + 1}", "foto")
        if not arquivo.exists():
            problemas.append(Problema("erro", "arquivo não encontrado.", str(arquivo)))
        elif arquivo.suffix.lower() not in EXT_FOTO:
            problemas.append(Problema("erro", "formato de foto não aceito (JPG, PNG, WEBP).", arquivo.name))
        caminhos.append(arquivo)
    return caminhos, problemas


def corrigir_alfa_logo(origem: Path, destino: Path, limiar: int = 40) -> dict:
    """Torna transparentes os pixels quase pretos (fundo preto deixado por exportação ruim).

    Nunca altera o arquivo de origem: grava uma cópia em `destino`.
    """
    origem, destino = Path(origem), Path(destino)
    if not origem.exists():
        raise ErroFacilita(f"Logo não encontrado: {origem}")
    garantir_saida_segura(destino, [origem])
    with Image.open(origem) as im:
        rgba = np.array(im.convert("RGBA"))
    rgb = rgba[..., :3].astype(int)
    quase_preto = (rgb.max(axis=2) <= limiar) & (rgba[..., 3] > 0)
    rgba[quase_preto, 3] = 0
    # suaviza a borda: pixels escuros, mas não pretos, ficam semitransparentes
    escuros = (rgb.max(axis=2) > limiar) & (rgb.max(axis=2) <= limiar * 2) & (rgba[..., 3] > 0)
    fator = (rgb.max(axis=2)[escuros] - limiar) / float(limiar)
    rgba[escuros, 3] = (rgba[escuros, 3] * fator).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    bbox = img.getchannel("A").getbbox()
    if bbox:
        img = img.crop(bbox)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    return {"origem": str(origem), "destino": str(destino), "pixels_removidos": int(quase_preto.sum()), "tamanho": img.size}
