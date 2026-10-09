"""`facilita novo`: cria a pasta de trabalho de uma peça, com modelos de roteiro, biblioteca e post.

    projetos/<nome>/
      clips/      vídeos brutos (MP4, MOV), nunca alterados
      audio/      narração (WAV, M4A, MP3) e trilha licenciada
      fotos/      fotos licenciadas para posts e carrosséis
      roteiro.md  roteiro por blocos
      clips.yaml  descrição e origem de cada clip
      post.yaml   peça de imagem (oferta)
      saida/      tudo o que a ferramenta gera
"""

from __future__ import annotations

from pathlib import Path

from .util import ErroFacilita, slug

ROTEIRO = """---
titulo: {titulo}
narracao: audio/narracao.wav
# musica: audio/trilha.mp3
# musica_origem: Artlist           # obrigatório com música (lista em marca/marca.yaml)
cta: Comente {palavra}
destino: México
transicao: fade
legendas: false
---

## Bloco 1 · Abertura
- tempo: 0:00–0:06
- imagem: descreva o que deve aparecer
- tela: {titulo}

Texto aprovado da narração do bloco 1.

## Bloco 2 · Destaque
- tempo: 0:06–0:14
- imagem: descreva o que deve aparecer
- tela: Texto curto na tela

Texto aprovado da narração do bloco 2.

## Bloco 3 · Convite
- tempo: 0:14–0:20
- imagem: descreva o que deve aparecer
- tela: Quer conhecer?

Texto aprovado da narração, com o convite para comentar {palavra}.
"""

CLIPS = """# Um item por clip em clips/. Descreva olhando a folha de contato (facilita analisar clips/*).
# 'origem' é obrigatória: Gravação do Richard, Drive oficial Xcaret, Canva Pro, e-agências...
pasta: clips
clips: []
#  - arquivo: fachada.mp4
#    origem: Gravação do Richard
#    descricao: fachada do hotel vista de drone
#    tags: [fachada, drone]
"""

POST = """# Peça de imagem. Gere com: facilita imagem post.yaml --formato feed --formato story
peca: {titulo}
modelo: oferta
campos:
  etiqueta: Oferta
  titulo: {titulo}
  subtitulo: ""
  cta: Comente {palavra}
fotos: []
#  - arquivo: fotos/foto.jpg
#    origem: Drive oficial Xcaret
oferta:
  aeroporto_saida: GRU
  all_inclusive: true
  bagagem: mão
  valor_total_casal: 0          # total das 2 pessoas
  parcelas: 10
  validade: ""                  # AAAA-MM-DD
  pagamento: ""
"""

LEIA_ME = """# {titulo}

1. Coloque os vídeos em `clips/`, a narração em `audio/` e as fotos em `fotos/`.
2. `facilita analisar clips/* audio/* --saida saida` e descreva cada clip em `clips.yaml`.
3. Escreva o roteiro em `roteiro.md`.
4. `facilita cobertura roteiro.md --clips clips.yaml --saida saida`
5. `facilita montar roteiro.md --clips clips.yaml --saida saida --previa`, depois sem `--previa`.
6. Post: preencha `post.yaml` e rode `facilita imagem post.yaml --saida saida`.
"""


def criar(nome: str, raiz: Path | str = "projetos") -> Path:
    pasta = Path(raiz) / slug(nome)
    if pasta.exists():
        raise ErroFacilita(f"A pasta {pasta} já existe; escolha outro nome.")
    for sub in ("clips", "audio", "fotos", "saida"):
        (pasta / sub).mkdir(parents=True)
    palavra = slug(nome).split("-")[-1].upper() or "QUERO"
    valores = {"titulo": nome.strip(), "palavra": palavra}
    (pasta / "roteiro.md").write_text(ROTEIRO.format(**valores), encoding="utf-8")
    (pasta / "clips.yaml").write_text(CLIPS, encoding="utf-8")
    (pasta / "post.yaml").write_text(POST.format(**valores), encoding="utf-8")
    (pasta / "LEIA-ME.md").write_text(LEIA_ME.format(**valores), encoding="utf-8")
    return pasta
