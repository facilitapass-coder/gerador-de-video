"""Leitura do roteiro em Markdown.

Formato (ver exemplos/xcaret-arte/roteiro.md):

    ---
    titulo: Hotel Xcaret Arte
    narracao: narracao.wav
    cta: Comente ARTE
    ---

    ## Bloco 1 · Abertura
    - tempo: 0:00–0:06
    - imagem: fachada do hotel, vista aérea
    - tela: Hotel Xcaret Arte
    - clip: fachada.mp4 @ 0:03        (opcional: força o clip e o ponto de entrada)
    - enquadramento: desfocado        (centro | foco 0.3 | desfocado)

    Texto da narração, com [pausa 0.5s] quando houver pausa.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..util import ErroFacilita, hash_texto, segundos, slug

_PAUSA = re.compile(r"\[\s*pausa(?:\s+([\d.,]+)\s*s?)?\s*\]", re.IGNORECASE)
_CABECALHO = re.compile(r"^##\s+(?:bloco\s*)?(\d+)?\s*[·:\-—–.]*\s*(.*)$", re.IGNORECASE)
_ITEM = re.compile(r"^[-*]\s*([\wçãõáéíóúâêô ]+?)\s*:\s*(.*)$", re.IGNORECASE)
_TEMPO = re.compile(r"([\d:.,]+)\s*(?:s\s*)?(?:–|—|-|a|até)\s*([\d:.,]+)")
_CHAVES = {
    "tempo": "tempo",
    "tempos": "tempo",
    "imagem": "imagem",
    "imagem pretendida": "imagem",
    "tela": "tela",
    "texto na tela": "tela",
    "clip": "clip",
    "enquadramento": "enquadramento",
    "transicao": "transicao",
    "transição": "transicao",
    "narracao": "narracao",
    "narração": "narracao",
}
PAUSA_PADRAO = 0.5


@dataclass
class Bloco:
    numero: int
    nome: str
    inicio: float | None = None
    fim: float | None = None
    imagem: str = ""
    tela: str = ""
    narracao: str = ""
    clip: str | None = None
    clip_inicio: float | None = None
    enquadramento: str | None = None
    foco: float | None = None
    transicao: str | None = None

    @property
    def duracao(self) -> float | None:
        if self.inicio is None or self.fim is None:
            return None
        return self.fim - self.inicio

    @property
    def narracao_limpa(self) -> str:
        return re.sub(r"\s+", " ", _PAUSA.sub(" ", self.narracao)).strip()

    def pausas(self) -> float:
        total = 0.0
        for m in _PAUSA.finditer(self.narracao):
            total += float(m.group(1).replace(",", ".")) if m.group(1) else PAUSA_PADRAO
        return total


@dataclass
class Roteiro:
    caminho: Path
    meta: dict
    blocos: list[Bloco] = field(default_factory=list)
    texto: str = ""

    @property
    def pasta(self) -> Path:
        return self.caminho.parent

    @property
    def titulo(self) -> str:
        return str(self.meta.get("titulo") or self.caminho.stem)

    @property
    def slug(self) -> str:
        return slug(str(self.meta.get("slug") or self.titulo))

    @property
    def cta(self) -> str:
        return str(self.meta.get("cta") or "")

    @property
    def hash(self) -> str:
        return hash_texto(self.texto)

    def arquivo(self, chave: str) -> Path | None:
        valor = self.meta.get(chave)
        if not valor:
            return None
        p = Path(valor)
        return p if p.is_absolute() else (self.pasta / p)


def _enquadramento(bloco: Bloco, valor: str) -> None:
    v = valor.strip().lower()
    m = re.match(r"foco\s*([\d.,]+)", v)
    if m:
        bloco.enquadramento, bloco.foco = "foco", float(m.group(1).replace(",", "."))
    elif v.startswith("desfoc") or v.startswith("fundo"):
        bloco.enquadramento = "desfocado"
    elif v.startswith("centr"):
        bloco.enquadramento = "centro"
    else:
        raise ErroFacilita(f"Bloco {bloco.numero}: enquadramento '{valor}' não reconhecido (centro | foco 0.3 | desfocado).")


def _aplicar(bloco: Bloco, chave: str, valor: str) -> None:
    valor = valor.strip()
    if chave == "tempo":
        m = _TEMPO.search(valor)
        if not m:
            raise ErroFacilita(f"Bloco {bloco.numero}: tempo '{valor}' não entendido (use 0:00–0:06).")
        bloco.inicio, bloco.fim = segundos(m.group(1)), segundos(m.group(2))
        if bloco.fim <= bloco.inicio:
            raise ErroFacilita(f"Bloco {bloco.numero}: o fim ({m.group(2)}) precisa ser depois do início ({m.group(1)}).")
    elif chave == "clip":
        nome, _, ponto = valor.partition("@")
        bloco.clip = nome.strip() or None
        bloco.clip_inicio = segundos(ponto) if ponto.strip() else None
    elif chave == "enquadramento":
        _enquadramento(bloco, valor)
    elif chave == "narracao":
        bloco.narracao = (bloco.narracao + " " + valor).strip()
    else:
        setattr(bloco, chave, valor.strip('"“”'))


def ler(caminho: Path | str) -> Roteiro:
    caminho = Path(caminho)
    texto = caminho.read_text(encoding="utf-8")
    meta: dict = {}
    corpo = texto
    if texto.startswith("---"):
        _, fm, corpo = texto.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    roteiro = Roteiro(caminho=caminho, meta=meta, texto=texto)
    atual: Bloco | None = None
    for linha in corpo.splitlines():
        s = linha.strip()
        m = _CABECALHO.match(s)
        if m and not s.startswith("###"):
            numero = int(m.group(1)) if m.group(1) else len(roteiro.blocos) + 1
            atual = Bloco(numero=numero, nome=m.group(2).strip() or f"Bloco {numero}")
            roteiro.blocos.append(atual)
            continue
        if atual is None or not s or s.startswith("<!--") or s.startswith("#"):
            continue
        item = _ITEM.match(s)
        if item and item.group(1).strip().lower() in _CHAVES:
            _aplicar(atual, _CHAVES[item.group(1).strip().lower()], item.group(2))
            continue
        atual.narracao = (atual.narracao + " " + s.lstrip("> ").strip()).strip()
    if not roteiro.blocos:
        raise ErroFacilita(f"{caminho.name}: nenhum bloco encontrado (cada bloco começa com '## Bloco N').")
    return roteiro


def palavras(texto: str) -> int:
    return len(re.findall(r"\w+", texto))


def resolver_tempos(roteiro: Roteiro, duracao_narracao: float | None, silencios: list[tuple[float, float]] | None = None) -> None:
    """Blocos sem tempo recebem tempo estimado pela narração.

    Com tempos explícitos no roteiro, nada muda. Sem tempos, a duração da narração é
    repartida pelo número de palavras (mais as pausas marcadas) e cada corte é puxado
    para o meio da pausa real mais próxima (até 0,8 s de distância).
    """
    if all(b.duracao for b in roteiro.blocos):
        return
    if any(b.duracao for b in roteiro.blocos):
        raise ErroFacilita("Ou todos os blocos têm tempo, ou nenhum tem (para estimar pela narração).")
    if not duracao_narracao:
        raise ErroFacilita("Os blocos não têm tempo e não há narração para medir. Informe 'tempo:' em cada bloco.")
    pesos = [max(1, palavras(b.narracao_limpa)) + b.pausas() * 2.5 for b in roteiro.blocos]
    total = sum(pesos)
    meios = [(a + b) / 2 for a, b in (silencios or [])]
    t = 0.0
    for i, (bloco, peso) in enumerate(zip(roteiro.blocos, pesos)):
        bloco.inicio = t
        fim = t + duracao_narracao * peso / total
        if i < len(roteiro.blocos) - 1 and meios:
            perto = min(meios, key=lambda m: abs(m - fim))
            if abs(perto - fim) <= 0.8 and perto > t + 0.5:
                fim = perto
        else:
            fim = fim if i < len(roteiro.blocos) - 1 else duracao_narracao
        bloco.fim = round(fim, 3)
        t = bloco.fim
