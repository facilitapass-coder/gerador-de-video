"""Biblioteca de clips e mapa de cobertura: qual clip cobre cada bloco e o que falta gravar.

A biblioteca é um `clips.yaml` com a descrição de cada clip (feita olhando a folha de
contato gerada por `facilita analisar`) e a origem obrigatória:

    clips:
      - arquivo: clips/fachada.mp4
        origem: Gravação do Richard
        descricao: fachada do hotel vista de drone
        tags: [fachada, drone, aérea]
        foco: 0.4                       # opcional, ponto de foco horizontal (0 a 1)
        trechos:                        # opcional, partes do clip com descrição própria
          - {inicio: 0:02, fim: 0:09, descricao: drone se aproxima da entrada}
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from ..marca import Marca, Problema
from ..util import ErroFacilita, formatar_tempo, segundos, sem_acentos
from .importacao import InfoMidia, sondar
from .roteiro import Bloco, Roteiro

STOPWORDS = set(
    "a o as os um uma uns umas de da do das dos e em no na nos nas por para com sem que se ao aos à às "
    "ou mais muito pelo pela pelos pelas seu sua seus suas este esta isso isto ele ela eles elas "
    "the of and in on with vista plano imagem cena take".split()
)


def tokens(texto: str) -> set[str]:
    palavras = re.findall(r"[a-z0-9]+", sem_acentos(texto or "").lower())
    saida = set()
    for p in palavras:
        if p in STOPWORDS or len(p) < 3:
            continue
        saida.add(p[:-1] if p.endswith("s") and len(p) > 4 else p)  # plural simples
    return saida


@dataclass
class Trecho:
    inicio: float
    fim: float
    descricao: str = ""


@dataclass
class Clip:
    arquivo: Path
    origem: str
    descricao: str = ""
    tags: list[str] = field(default_factory=list)
    foco: float | None = None
    enquadramento: str | None = None
    trechos: list[Trecho] = field(default_factory=list)
    info: InfoMidia | None = None

    @property
    def nome(self) -> str:
        return self.arquivo.name

    def tokens(self) -> set[str]:
        return tokens(" ".join([self.descricao, " ".join(self.tags), self.arquivo.stem.replace("_", " ").replace("-", " ")]))


@dataclass
class Biblioteca:
    caminho: Path
    clips: list[Clip]

    def achar(self, nome: str) -> Clip | None:
        alvo = Path(nome).name.lower()
        return next((c for c in self.clips if c.nome.lower() == alvo or str(c.arquivo).lower().endswith(nome.lower())), None)


def carregar_biblioteca(caminho: Path | str, marca: Marca, sondar_arquivos: bool = True) -> tuple[Biblioteca, list[Problema]]:
    caminho = Path(caminho)
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    base = caminho.parent / dados.get("pasta", ".")
    clips, problemas = [], []
    for item in dados.get("clips", []):
        if "arquivo" not in item:
            raise ErroFacilita(f"{caminho.name}: todo clip precisa de 'arquivo'.")
        arquivo = Path(item["arquivo"])
        arquivo = arquivo if arquivo.is_absolute() else base / arquivo
        problemas += marca.verificar_origem(item.get("origem"), arquivo.name, "vídeo")
        trechos = [
            Trecho(segundos(t["inicio"]), segundos(t["fim"]), str(t.get("descricao", ""))) for t in item.get("trechos", []) or []
        ]
        clip = Clip(
            arquivo=arquivo,
            origem=str(item.get("origem") or ""),
            descricao=str(item.get("descricao", "")),
            tags=[str(t) for t in item.get("tags", []) or []],
            foco=item.get("foco"),
            enquadramento=item.get("enquadramento"),
            trechos=trechos,
        )
        if sondar_arquivos:
            if not arquivo.exists():
                problemas.append(Problema("erro", "arquivo não encontrado", str(arquivo)))
            else:
                clip.info = sondar(arquivo)
        clips.append(clip)
    return Biblioteca(caminho=caminho, clips=clips), problemas


@dataclass
class Escolha:
    bloco: int
    nome_bloco: str
    inicio_bloco: float
    duracao: float
    imagem: str
    clip: str | None = None
    clip_inicio: float = 0.0
    disponivel: float = 0.0
    pontuacao: float = 0.0
    situacao: str = "sem imagem"  # coberto | forçado | curto | sem imagem
    motivo: str = ""

    @property
    def coberto(self) -> bool:
        return self.clip is not None


def _candidatos(clip: Clip) -> list[tuple[float, float, set[str]]]:
    """(início, fim, tokens) de cada trecho, ou do clip inteiro."""
    dur = clip.info.duracao if clip.info else 0.0
    base = clip.tokens()
    if clip.trechos:
        return [(t.inicio, min(t.fim, dur) if dur else t.fim, base | tokens(t.descricao)) for t in clip.trechos]
    return [(0.0, dur, base)]


def mapear(roteiro: Roteiro, biblioteca: Biblioteca) -> list[Escolha]:
    escolhas: list[Escolha] = []
    usos: dict[str, int] = {}
    for b in roteiro.blocos:
        if b.duracao is None:
            raise ErroFacilita(f"Bloco {b.numero} sem tempo; rode resolver_tempos antes.")
        e = Escolha(b.numero, b.nome, b.inicio or 0.0, b.duracao, b.imagem)
        if b.clip:
            e = _forcado(b, biblioteca, e)
        else:
            e = _melhor(b, biblioteca, e, usos)
        if e.clip:
            usos[e.clip] = usos.get(e.clip, 0) + 1
            if e.situacao != "forçado" and e.disponivel + 0.05 < e.duracao:
                e.situacao = "curto"
                e.motivo = f"trecho tem {e.disponivel:.1f}s e o bloco pede {e.duracao:.1f}s; o último quadro será congelado"
        escolhas.append(e)
    return escolhas


def _forcado(b: Bloco, biblioteca: Biblioteca, e: Escolha) -> Escolha:
    clip = biblioteca.achar(b.clip or "")
    if not clip:
        raise ErroFacilita(f"Bloco {b.numero}: clip '{b.clip}' não está em {biblioteca.caminho.name}.")
    dur = clip.info.duracao if clip.info else 0.0
    inicio = b.clip_inicio or 0.0
    e.clip, e.clip_inicio, e.disponivel = str(clip.arquivo), inicio, max(0.0, dur - inicio)
    e.situacao, e.pontuacao, e.motivo = "forçado", 1.0, "indicado no roteiro"
    return e


def _melhor(b: Bloco, biblioteca: Biblioteca, e: Escolha, usos: dict[str, int]) -> Escolha:
    pedido = tokens(b.imagem) or tokens(b.nome + " " + b.tela)
    if not pedido:
        e.motivo = "bloco sem 'imagem' descrita no roteiro"
        return e
    melhor = None
    for clip in biblioteca.clips:
        if clip.info is None or clip.info.tipo != "video":
            continue
        for inicio, fim, tk in _candidatos(clip):
            comum = pedido & tk
            if not comum:
                continue
            nota = len(comum) / len(pedido)
            nota -= 0.25 * usos.get(str(clip.arquivo), 0)  # evita repetir imagem
            nota += 0.05 if (fim - inicio) >= e.duracao else 0.0
            if melhor is None or nota > melhor[0]:
                melhor = (nota, clip, inicio, fim, comum)
    if melhor is None or melhor[0] <= 0:
        e.motivo = "nenhum clip descrito com: " + ", ".join(sorted(pedido))
        return e
    nota, clip, inicio, fim, comum = melhor
    # o trecho marca o ponto de entrada; o clip pode seguir depois do fim descrito
    restante = (clip.info.duracao if clip.info else fim) - inicio
    e.clip, e.clip_inicio, e.disponivel = str(clip.arquivo), inicio, max(0.0, restante)
    e.pontuacao, e.situacao, e.motivo = round(nota, 2), "coberto", "casou: " + ", ".join(sorted(comum))
    return e


def relatorio_markdown(roteiro: Roteiro, escolhas: list[Escolha]) -> str:
    linhas = [
        f"# Mapa de cobertura · {roteiro.titulo}",
        "",
        "| Bloco | Tempo | Imagem pretendida | Clip | Trecho | Situação |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for e in escolhas:
        tempo = f"{formatar_tempo(e.inicio_bloco)}–{formatar_tempo(e.inicio_bloco + e.duracao)}"
        clip = Path(e.clip).name if e.clip else "—"
        trecho = f"{formatar_tempo(e.clip_inicio)} (+{min(e.disponivel, e.duracao):.1f}s)" if e.clip else "—"
        linhas.append(f"| {e.bloco} · {e.nome_bloco} | {tempo} | {e.imagem or '—'} | {clip} | {trecho} | {e.situacao} |")
    faltas = [e for e in escolhas if not e.coberto]
    curtos = [e for e in escolhas if e.situacao == "curto"]
    linhas += ["", "## O que falta gravar", ""]
    if not faltas and not curtos:
        linhas.append("Nada: todos os blocos têm imagem.")
    for e in faltas:
        linhas.append(f"- **Bloco {e.bloco} ({e.nome_bloco})**: {e.imagem or 'imagem não descrita'} · {e.duracao:.1f}s · {e.motivo}")
    for e in curtos:
        linhas.append(f"- Bloco {e.bloco} ({e.nome_bloco}): mais {e.duracao - e.disponivel:.1f}s de \"{e.imagem}\" ({e.motivo})")
    return "\n".join(linhas) + "\n"


def salvar_relatorio(roteiro: Roteiro, escolhas: list[Escolha], pasta: Path) -> tuple[Path, Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    md = pasta / f"{roteiro.slug}_cobertura.md"
    js = pasta / f"{roteiro.slug}_cobertura.json"
    md.write_text(relatorio_markdown(roteiro, escolhas), encoding="utf-8")
    js.write_text(json.dumps([asdict(e) for e in escolhas], ensure_ascii=False, indent=2), encoding="utf-8")
    return md, js
