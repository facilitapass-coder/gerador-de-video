"""Legendas queimadas na imagem, a partir do texto aprovado da narração no roteiro.

A transcrição automática depende de serviço externo (só com aprovação do Richard);
enquanto isso, a fonte das legendas é o próprio roteiro, já revisado. O tempo de cada
frase é repartido dentro do bloco pelo número de caracteres. Os nomes da marca são
corrigidos pelo dicionário (`dicionario_marca`) e um `.srt` sai ao lado do MP4 para a
revisão obrigatória.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..marca import Marca
from .roteiro import _PAUSA, Bloco


@dataclass
class Frase:
    inicio: float
    fim: float
    texto: str  # pode ter "\n" entre as duas linhas


def _linhas(palavras: list[str], maximo: int) -> list[str]:
    linhas, atual = [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if len(teste) <= maximo or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def frases_do_bloco(bloco: Bloco, maximo: int) -> list[str]:
    """Divide a narração em frases de até 2 linhas, respeitando pontuação e pausas marcadas."""
    texto = _PAUSA.sub(" | ", bloco.narracao)
    partes = [p.strip() for p in re.split(r"(?<=[.!?;])\s+|\s*\|\s*", texto) if p.strip()]
    saida = []
    for parte in partes:
        linhas = _linhas(parte.split(), maximo)
        for i in range(0, len(linhas), 2):
            saida.append("\n".join(linhas[i : i + 2]))
    return saida


def montar_frases(blocos: list[Bloco], marca: Marca, ate: float | None = None) -> list[Frase]:
    maximo = int(marca.video.get("legenda_max_caracteres", 32))
    frases: list[Frase] = []
    for b in blocos:
        if b.inicio is None or b.fim is None:
            continue
        textos = [marca.corrigir_grafia(t) for t in frases_do_bloco(b, maximo)]
        if not textos:
            continue
        pesos = [max(4, len(t)) for t in textos]
        total, t = sum(pesos), b.inicio
        for texto, peso in zip(textos, pesos):
            fim = t + (b.fim - b.inicio) * peso / total
            if ate is not None and t >= ate:
                break
            frases.append(Frase(round(t, 3), round(min(fim - 0.05, ate) if ate else fim - 0.05, 3), texto))
            t = fim
    return frases


def _ts_srt(s: float) -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    seg, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{seg:02d},{ms:03d}"


def _ts_ass(s: float) -> str:
    cs = int(round(s * 100))
    h, cs = divmod(cs, 360_000)
    m, cs = divmod(cs, 6_000)
    seg, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{seg:02d}.{cs:02d}"


def salvar_srt(frases: list[Frase], destino: Path) -> Path:
    blocos = [f"{i}\n{_ts_srt(f.inicio)} --> {_ts_srt(f.fim)}\n{f.texto}\n" for i, f in enumerate(frases, 1)]
    destino.write_text("\n".join(blocos), encoding="utf-8")
    return destino


def _cor_ass(hex_cor: str, alfa: int = 0) -> str:
    h = hex_cor.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alfa:02X}{b}{g}{r}".upper()


def salvar_ass(frases: list[Frase], destino: Path, marca: Marca) -> Path:
    """Texto branco em Poppins SemiBold sobre caixa marinho, centrado logo acima da zona da legenda do Instagram."""
    v = marca.video
    z = v["zona_segura"]
    fonte = marca.dados["fonte"]["familia"] if marca.caminho_fonte("seminegrito") else "DejaVu Sans"
    estilo = (
        f"Style: Marca,{fonte},{v.get('legenda_tamanho', 54)},&H00FFFFFF,&H00FFFFFF,"
        f"{_cor_ass(marca.cores['marinho'], 0x30)},{_cor_ass(marca.cores['marinho'], 0x30)},"
        f"-1,0,0,0,100,100,0,0,3,14,0,2,{z['esquerda']},{z['direita']},{z['base'] + 30},1"
    )
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {v['largura']}", f"PlayResY: {v['altura']}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding",
        estilo, "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for f in frases:
        texto = f.texto.replace("{", "(").replace("}", ")").replace("\n", "\\N")
        linhas.append(f"Dialogue: 0,{_ts_ass(f.inicio)},{_ts_ass(f.fim)},Marca,,0,0,0,,{texto}")
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def escapar_filtro(caminho: Path) -> str:
    """Caminho seguro dentro de um filtro do ffmpeg (ass=...)."""
    s = str(Path(caminho).resolve()).replace("\\", "/")
    return s.replace(":", "\\:").replace("'", "\\'").replace(",", "\\,")
