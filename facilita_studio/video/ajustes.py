"""Ajuste por pedido: frases como "tira o bloco 5" ou "voz mais alta" refazem o corte sem recomeçar.

Os pedidos viram um arquivo `<roteiro>.ajustes.yaml` ao lado do roteiro. O roteiro do
Richard não é alterado; `facilita montar` lê os dois e grava uma nova versão do Reels.

Pedidos entendidos (maiúsculas e acentos não importam):

    tira o bloco 5              volta o bloco 5
    voz mais alta / mais baixa  música mais alta / mais baixa
    troca o clip do bloco 3 por quarto.mp4 @ 0:02
    texto do bloco 2: Piscinas com vista
    bloco 1 desfocado | bloco 1 foco 0.3 | bloco 1 centro
    com fade | sem transição
    com legendas | sem legendas
    com selo | sem selo
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..util import ErroFacilita, segundos, sem_acentos
from .roteiro import Roteiro, _enquadramento

PASSO_VOZ_DB = 2.0
PASSO_MUSICA = 0.02
EXEMPLOS = __doc__.split("Pedidos entendidos (maiúsculas e acentos não importam):")[1].strip("\n")


def caminho_ajustes(roteiro: Path) -> Path:
    roteiro = Path(roteiro)
    return roteiro.with_name(roteiro.stem + ".ajustes.yaml")


def carregar(roteiro: Path) -> dict:
    p = caminho_ajustes(roteiro)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def salvar(roteiro: Path, ajustes: dict) -> Path:
    p = caminho_ajustes(roteiro)
    cabecalho = "# Ajustes pedidos sobre o roteiro (gerado por `facilita ajustar`; pode editar à mão).\n"
    p.write_text(cabecalho + yaml.safe_dump(ajustes, allow_unicode=True, sort_keys=True), encoding="utf-8")
    return p


def _bloco(aj: dict, n: int) -> dict:
    return aj.setdefault("blocos", {}).setdefault(int(n), {})


def interpretar(pedido: str, aj: dict, marca_video: dict) -> str:
    """Aplica um pedido ao dicionário de ajustes e devolve a descrição do que mudou."""
    original = pedido.strip()
    p = sem_acentos(original).lower().strip().rstrip(".!")

    m = re.match(r"(?:tira|tirar|remove|remover|corta|cortar|sem)\s+(?:o\s+)?bloco\s+(\d+)$", p)
    if m:
        n = int(m.group(1))
        aj["remover"] = sorted(set(aj.get("remover", [])) | {n})
        return f"bloco {n} removido"
    m = re.match(r"(?:volta|voltar|devolve|recoloca)\s+(?:o\s+)?bloco\s+(\d+)$", p)
    if m:
        n = int(m.group(1))
        aj["remover"] = sorted(set(aj.get("remover", [])) - {n})
        return f"bloco {n} de volta"

    m = re.match(r"voz\s+(?:um\s+pouco\s+)?mais\s+(alta|baixa)$", p)
    if m:
        delta = PASSO_VOZ_DB if m.group(1) == "alta" else -PASSO_VOZ_DB
        atual = float(aj.get("voz_ganho_db", marca_video["voz_ganho_db"])) + delta
        aj["voz_ganho_db"] = round(min(14.0, max(0.0, atual)), 1)
        return f"voz com ganho de {aj['voz_ganho_db']} dB"
    m = re.match(r"(?:musica|trilha)\s+(?:um\s+pouco\s+)?mais\s+(alta|baixa)$", p)
    if m:
        delta = PASSO_MUSICA if m.group(1) == "alta" else -PASSO_MUSICA
        atual = float(aj.get("musica_volume", marca_video["musica_volume"])) + delta
        limitado = round(min(0.15, max(0.10, atual)), 3)  # regra da casa: 10–15%
        aj["musica_volume"] = limitado
        aviso = " (limite da faixa 10–15%)" if abs(limitado - atual) > 1e-6 else ""
        return f"música a {limitado:.0%}{aviso}"

    m = re.match(r"(?:troca|trocar|muda|mudar)\s+o\s+clip\s+do\s+bloco\s+(\d+)\s+(?:por|para)\s+(.+)$", p)
    if m:
        n = int(m.group(1))
        resto = _depois_de(original, ("por", "para"))
        nome, _, ponto = resto.partition("@")
        _bloco(aj, n)["clip"] = nome.strip()
        if ponto.strip():
            _bloco(aj, n)["clip_inicio"] = segundos(ponto)
        else:
            _bloco(aj, n).pop("clip_inicio", None)
        return f"bloco {n} com o clip {nome.strip()}"

    m = re.match(r"(?:texto|titulo|tela)\s+do\s+bloco\s+(\d+)\s*(?::|para|=)\s*(.+)$", p)
    if m:
        n = int(m.group(1))
        texto = re.split(r"\s*(?::|=|\bpara\b)\s*", original, maxsplit=1)[1].strip().strip('"“”')
        _bloco(aj, n)["tela"] = texto
        return f"bloco {n} com o texto \"{texto}\""

    m = re.match(r"bloco\s+(\d+)\s+(desfocado|fundo desfocado|centro|centralizado|foco\s+[\d.,]+)$", p)
    if m:
        n = int(m.group(1))
        _bloco(aj, n)["enquadramento"] = m.group(2)
        return f"bloco {n} com enquadramento {m.group(2)}"

    if p in ("com fade", "com transicao", "transicao fade"):
        aj["transicao"] = "fade"
        return "transições em fade"
    if p in ("sem transicao", "corte seco", "sem fade"):
        aj["transicao"] = "corte"
        return "corte seco entre blocos"
    if p in ("com legenda", "com legendas", "liga legendas", "legendas"):
        aj["legendas"] = True
        return "legendas ligadas"
    if p in ("sem legenda", "sem legendas", "desliga legendas"):
        aj["legendas"] = False
        return "legendas desligadas"
    if p in ("com selo", "poe o selo", "coloca o selo"):
        aj["selo"] = True
        return "selo Xpert Xcaret ligado"
    if p in ("sem selo", "tira o selo"):
        aj["selo"] = False
        return "selo Xpert Xcaret desligado"

    raise ErroFacilita(f"Não entendi o pedido \"{original}\". Pedidos que eu entendo:\n{EXEMPLOS}")


def _depois_de(texto: str, palavras: tuple[str, ...]) -> str:
    m = re.search(r"\b(?:" + "|".join(palavras) + r")\b\s+(.+)$", texto, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def aplicar(rot: Roteiro, aj: dict, params: dict) -> list[str]:
    """Aplica os ajustes ao roteiro já lido (em memória) e aos parâmetros de vídeo.

    Devolve a lista de blocos removidos. Remoção de bloco é tratada na montagem,
    porque também corta a narração daquele trecho.
    """
    numeros = {b.numero for b in rot.blocos}
    for n in list(aj.get("remover", [])) + list((aj.get("blocos") or {}).keys()):
        if int(n) not in numeros:
            raise ErroFacilita(f"Ajuste cita o bloco {n}, que não existe no roteiro.")
    for n, mudancas in (aj.get("blocos") or {}).items():
        b = next(b for b in rot.blocos if b.numero == int(n))
        for chave, valor in mudancas.items():
            if chave == "enquadramento":
                _enquadramento(b, str(valor))
            elif chave == "clip_inicio":
                b.clip_inicio = segundos(valor)
            elif chave in ("clip", "tela"):
                setattr(b, chave, valor)
            else:
                raise ErroFacilita(f"Ajuste desconhecido no bloco {n}: {chave}")
    if "voz_ganho_db" in aj:
        params["voz_ganho_db"] = float(aj["voz_ganho_db"])
    if "musica_volume" in aj:
        params["musica_volume"] = float(aj["musica_volume"])
    if "transicao" in aj:
        rot.meta["transicao"] = aj["transicao"]
        for b in rot.blocos:
            b.transicao = None
    for chave in ("legendas", "selo"):
        if chave in aj:
            rot.meta[chave] = bool(aj[chave])
    remover = set(int(n) for n in aj.get("remover", []))
    if remover and remover >= numeros:
        raise ErroFacilita("Os ajustes removem todos os blocos.")
    return sorted(remover)
