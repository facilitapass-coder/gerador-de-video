"""Comparação entre duas versões de uma peça, a partir dos manifestos (.json) gravados em cada exportação."""

from __future__ import annotations

import json
from pathlib import Path

from .util import ErroFacilita

CAMPOS_BLOCO = ("tela", "clip", "clip_inicio", "duracao", "enquadramento", "foco", "situacao")
CAMPOS_PARAMETRO = ("voz_ganho_db", "musica_volume", "musica_volume_final", "transicao", "respiro_final", "cta_duracao", "legendas")


def _ler(caminho: Path) -> dict:
    caminho = Path(caminho)
    if caminho.is_dir():
        caminho = caminho / "manifesto.json"
    elif caminho.suffix.lower() != ".json":
        caminho = caminho.with_suffix(".json")
    if not caminho.exists():
        raise ErroFacilita(f"Manifesto não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def _fmt(v) -> str:
    if isinstance(v, str) and ("/" in v or "\\" in v):
        return Path(v).name
    return "—" if v in (None, "") else str(v)


def comparar(antes: Path | str, depois: Path | str) -> list[str]:
    a, b = _ler(Path(antes)), _ler(Path(depois))
    if a.get("tipo") != b.get("tipo"):
        raise ErroFacilita(f"Tipos diferentes: {a.get('tipo')} × {b.get('tipo')}.")
    linhas: list[str] = []
    if a.get("tipo") == "reels":
        if a["roteiro"].get("sha256") != b["roteiro"].get("sha256"):
            linhas.append("Roteiro: texto alterado")
        if (a.get("ajustes") or {}) != (b.get("ajustes") or {}):
            linhas.append(f"Ajustes: {a.get('ajustes') or '—'} → {b.get('ajustes') or '—'}")
        blocos_a = {x["bloco"]: x for x in a.get("blocos", [])}
        blocos_b = {x["bloco"]: x for x in b.get("blocos", [])}
        for n in sorted(set(blocos_a) | set(blocos_b)):
            if n not in blocos_b:
                linhas.append(f"Bloco {n}: removido")
                continue
            if n not in blocos_a:
                linhas.append(f"Bloco {n}: novo")
                continue
            for campo in CAMPOS_BLOCO:
                va, vb = blocos_a[n].get(campo), blocos_b[n].get(campo)
                if isinstance(va, float) and isinstance(vb, float) and abs(va - vb) < 0.01:
                    continue
                if _fmt(va) != _fmt(vb):  # mesmo arquivo em outra pasta não é mudança
                    linhas.append(f"Bloco {n} · {campo}: {_fmt(va)} → {_fmt(vb)}")
        for campo in CAMPOS_PARAMETRO:
            va, vb = a.get("parametros", {}).get(campo), b.get("parametros", {}).get(campo)
            if va != vb:
                linhas.append(f"Parâmetro {campo}: {_fmt(va)} → {_fmt(vb)}")
        ma, mb = a.get("medidas", {}), b.get("medidas", {})
        for campo in ("duracao", "voz_acima_da_musica_db"):
            if ma.get(campo) != mb.get(campo):
                linhas.append(f"Medida {campo}: {_fmt(ma.get(campo))} → {_fmt(mb.get(campo))}")
        if bool(a.get("legendas_srt")) != bool(b.get("legendas_srt")):
            linhas.append(f"Legendas: {'sim' if a.get('legendas_srt') else 'não'} → {'sim' if b.get('legendas_srt') else 'não'}")
        if bool(a.get("selo")) != bool(b.get("selo")):
            linhas.append(f"Selo: {'sim' if a.get('selo') else 'não'} → {'sim' if b.get('selo') else 'não'}")
    else:
        ca, cb = a.get("peca_conteudo", {}), b.get("peca_conteudo", {})
        for chave in sorted(set(ca) | set(cb)):
            if ca.get(chave) != cb.get(chave):
                linhas.append(f"{chave}: {json.dumps(ca.get(chave), ensure_ascii=False)} → {json.dumps(cb.get(chave), ensure_ascii=False)}")
    return linhas or ["Sem diferenças nos textos, blocos e parâmetros."]
