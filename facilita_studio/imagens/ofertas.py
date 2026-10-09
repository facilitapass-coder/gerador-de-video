"""Regras de oferta da casa, validadas antes de qualquer peça ser gerada.

- aeroporto de saída sempre explícito (ex.: GRU);
- validade e condições de pagamento presentes;
- all inclusive => bagagem só de mão;
- parcelamento sempre sobre o total de duas pessoas (o casal).
"""

from __future__ import annotations

import datetime as dt
import re

from ..marca import Problema
from ..util import sem_acentos

CAMPOS_TEXTO_PARCELA_PESSOA = re.compile(r"\d+\s*x.*por\s+pessoa|por\s+pessoa.*\d+\s*x", re.IGNORECASE)


def reais(valor: float) -> str:
    """12990.5 -> 'R$ 12.990,50'; inteiros sem centavos."""
    inteiro = abs(valor - round(valor)) < 0.005
    texto = f"{valor:,.0f}" if inteiro else f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "§").replace(".", ",").replace("§", ".")


def _data(valor) -> dt.date | None:
    if isinstance(valor, dt.date):
        return valor
    texto = str(valor).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(texto, fmt).date()
        except ValueError:
            pass
    return None


def _bagagem_de_mao(valor) -> bool:
    v = sem_acentos(str(valor or "")).lower()
    return "mao" in v and "despach" not in v


def validar(oferta: dict | None, hoje: dt.date | None = None) -> tuple[list[Problema], dict]:
    """Devolve (problemas, textos prontos para o modelo)."""
    if not oferta:
        return [], {}
    hoje = hoje or dt.date.today()
    p: list[Problema] = []
    onde = "oferta"

    aeroporto = str(oferta.get("aeroporto_saida") or "").strip().upper()
    if not aeroporto:
        p.append(Problema("erro", "aeroporto de saída não informado (ex.: aeroporto_saida: GRU).", onde))

    validade = _data(oferta.get("validade")) if oferta.get("validade") else None
    if not oferta.get("validade"):
        p.append(Problema("erro", "validade da oferta não informada (ex.: validade: 2026-11-30).", onde))
    elif validade is None:
        p.append(Problema("erro", f"validade '{oferta.get('validade')}' não entendida (use AAAA-MM-DD ou DD/MM/AAAA).", onde))
    elif validade < hoje:
        p.append(Problema("erro", f"oferta vencida em {validade:%d/%m/%Y}.", onde))

    pagamento = str(oferta.get("pagamento") or "").strip()
    if not pagamento:
        p.append(Problema("erro", "condições de pagamento não informadas (ex.: pagamento: 10x sem juros no cartão).", onde))

    all_inclusive = bool(oferta.get("all_inclusive"))
    bagagem = oferta.get("bagagem")
    if all_inclusive and not _bagagem_de_mao(bagagem):
        p.append(Problema("erro", "pacote all inclusive: a bagagem é só de mão (bagagem: mão).", onde))

    total = oferta.get("valor_total_casal")
    parcelas = int(oferta.get("parcelas") or 1)
    if oferta.get("valor_por_pessoa") is not None:
        if total is None:
            total = float(oferta["valor_por_pessoa"]) * 2
        elif abs(float(oferta["valor_por_pessoa"]) * 2 - float(total)) > 0.01:
            p.append(Problema("erro", "valor_por_pessoa × 2 não bate com valor_total_casal.", onde))
    if total is None:
        p.append(Problema("erro", "informe valor_total_casal (o parcelamento é sobre o total de duas pessoas).", onde))
    parcela = float(total) / parcelas if total is not None else None
    if oferta.get("valor_parcela") is not None and parcela is not None:
        if abs(float(oferta["valor_parcela"]) - parcela) > 0.01:
            p.append(
                Problema("erro", f"valor_parcela {reais(float(oferta['valor_parcela']))} não é o total do casal "
                         f"÷ {parcelas} ({reais(parcela)}).", onde)
            )

    textos: dict = {}
    if not [x for x in p if x.nivel == "erro"]:
        textos = {
            "aeroporto": aeroporto,
            "saida": f"Saindo de {aeroporto}",
            "validade": f"Válido até {validade:%d/%m/%Y}",
            "pagamento": pagamento,
            "bagagem": "Bagagem de mão" if _bagagem_de_mao(bagagem) else (f"Bagagem: {bagagem}" if bagagem else ""),
            "all_inclusive": "All inclusive" if all_inclusive else "",
            "parcelas": parcelas,
            "parcela": reais(parcela) if parcela is not None else "",
            "total": reais(float(total)) if total is not None else "",
            "preco_linha": (f"{parcelas}x de {reais(parcela)} por casal" if parcelas > 1 else f"{reais(float(total))} por casal"),
            "total_linha": f"Total {reais(float(total))} para 2 pessoas",
            "noites": oferta.get("noites"),
            "datas": oferta.get("datas", ""),
            "condicoes": oferta.get("condicoes", ""),
        }
    return p, textos


def verificar_textos_livres(campos: dict) -> list[Problema]:
    """Parcelamento 'por pessoa' escrito à mão contraria a regra do casal."""
    problemas = []
    for chave, valor in _textos(campos):
        if CAMPOS_TEXTO_PARCELA_PESSOA.search(valor):
            problemas.append(Problema("erro", "parcelamento 'por pessoa': a regra é parcelar o total do casal.", chave))
    return problemas


def _textos(dados, prefixo: str = ""):
    if isinstance(dados, str):
        yield prefixo, dados
    elif isinstance(dados, dict):
        for k, v in dados.items():
            yield from _textos(v, f"{prefixo}.{k}" if prefixo else str(k))
    elif isinstance(dados, list):
        for i, v in enumerate(dados):
            yield from _textos(v, f"{prefixo}[{i}]")
