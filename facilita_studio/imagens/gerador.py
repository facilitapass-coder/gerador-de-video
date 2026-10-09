"""Gera as peças de imagem a partir de um arquivo de peça (YAML).

Exemplo mínimo (ver exemplos/oferta-xcaret.yaml):

    peca: Xcaret Arte novembro
    modelo: oferta              # oferta | hotel | story | whatsapp | carrossel
    formatos: [feed, story]     # opcional
    campos: {titulo: ..., subtitulo: ..., cta: ...}
    fotos: [{arquivo: fotos/piscina.jpg, origem: Drive oficial Xcaret}]
    oferta: {aeroporto_saida: GRU, validade: 2026-11-30, ...}
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from ..marca import Marca, Problema, erros, exigir_sem_erros
from ..util import ErroFacilita, garantir_saida_segura, impressao_arquivo, salvar_manifesto, slug
from . import ofertas
from .fotos import verificar_fotos
from .render import _ComDefault, fontes_css, html, navegador, renderizar

VARIANTES = ["", "v2", "v3"]  # 1 = padrão; 2 = cartão branco; 3 = fundo laranja
MODELOS = {"oferta", "hotel", "story", "whatsapp", "carrossel"}
FORMATO_PADRAO = {"oferta": ["feed"], "hotel": ["feed"], "story": ["story"], "whatsapp": ["whatsapp"], "carrossel": ["feed"]}
TELAS_CARROSSEL = {"capa", "miolo", "cta"}


def _modelo_html(modelo: str, formato: str) -> str:
    if formato == "story":
        return "story"
    if formato == "whatsapp":
        return "whatsapp"
    if modelo in ("story", "whatsapp"):
        raise ErroFacilita(f"O modelo '{modelo}' é vertical; use formato story ou whatsapp.")
    return modelo


def _destaques(lista) -> list:
    saida = []
    for d in lista or []:
        saida.append(_ComDefault({"texto": d, "fonte": ""} if isinstance(d, str) else d))
    return saida


def carregar(caminho: Path | str) -> dict:
    caminho = Path(caminho)
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    modelo = dados.get("modelo")
    if modelo not in MODELOS:
        raise ErroFacilita(f"{caminho.name}: modelo '{modelo}' desconhecido ({', '.join(sorted(MODELOS))}).")
    return dados


def _telas(dados: dict) -> list[dict]:
    if dados["modelo"] != "carrossel":
        return [dados]
    telas = [dict(t) for t in dados.get("telas") or []]
    if not telas:
        raise ErroFacilita("Carrossel sem 'telas'.")
    for t in telas:
        if t.get("modelo") not in TELAS_CARROSSEL:
            raise ErroFacilita(f"Tela de carrossel com modelo '{t.get('modelo')}' (use capa, miolo ou cta).")
        t.setdefault("oferta", dados.get("oferta") if t["modelo"] != "capa" else None)
    if telas[-1]["modelo"] != "cta":
        telas.append({"modelo": "cta", "campos": {"titulo": dados.get("campos", {}).get("titulo", ""),
                                                  "cta": dados.get("campos", {}).get("cta", "Fale com a Facilita Pass")},
                      "oferta": dados.get("oferta")})
    return telas


def validar(caminho: Path | str, marca: Marca, hoje: dt.date | None = None) -> tuple[list[Problema], dict]:
    """Valida textos, fotos e regras de oferta. Não gera nada."""
    caminho = Path(caminho)
    dados = carregar(caminho)
    problemas: list[Problema] = []
    preparadas = []
    for i, tela in enumerate(_telas(dados)):
        onde = f"tela {i + 1}" if dados["modelo"] == "carrossel" else "peça"
        campos = {**(dados.get("campos") or {}), **(tela.get("campos") or {})} if tela is not dados else (dados.get("campos") or {})
        for chave, valor in campos.items():
            problemas += marca.verificar_texto(str(valor), f"{onde} · {chave}")
        for d in tela.get("destaques") or []:
            texto = d if isinstance(d, str) else d.get("texto", "")
            problemas += marca.verificar_texto(texto, f"{onde} · destaque")
            if isinstance(d, str) or not d.get("fonte"):
                problemas.append(Problema("aviso", f"destaque sem fonte marcado como 'a confirmar': {texto}", onde))
        problemas += ofertas.verificar_textos_livres(campos)
        fotos, p_fotos = verificar_fotos(tela.get("fotos") or (dados.get("fotos") if tela.get("modelo") == "capa" else []) or [],
                                         caminho.parent, marca)
        problemas += [Problema(x.nivel, x.mensagem, f"{onde} · {x.onde}") for x in p_fotos]
        p_oferta, textos_oferta = ofertas.validar(tela.get("oferta"), hoje)
        problemas += p_oferta
        preparadas.append({"tela": tela, "campos": campos, "fotos": fotos, "oferta": textos_oferta})
    # Problemas de oferta repetidos em cada tela aparecem uma vez só.
    vistos, unicos = set(), []
    for p in problemas:
        if str(p) not in vistos:
            vistos.add(str(p))
            unicos.append(p)
    return unicos, {"dados": dados, "telas": preparadas}


def gerar(caminho: Path | str, marca: Marca, pasta_saida: Path | str = "saida", formatos: list[str] | None = None,
          permitir_fonte_substituta: bool = False, manter_2x: bool = False, hoje: dt.date | None = None,
          variacoes: int = 1) -> dict:
    caminho = Path(caminho)
    problemas, prep = validar(caminho, marca, hoje)
    problemas += marca.verificar_ativos(permitir_fonte_substituta)
    exigir_sem_erros(problemas, f"Peça {caminho.name}")
    dados = prep["dados"]
    modelo = dados["modelo"]
    formatos = formatos or dados.get("formatos") or FORMATO_PADRAO[modelo]
    if modelo == "carrossel" and formatos != ["feed"]:
        raise ErroFacilita("Carrossel sai só no formato feed (1080×1350).")
    if not 1 <= variacoes <= len(VARIANTES):
        raise ErroFacilita(f"Variações vão de 1 a {len(VARIANTES)}.")
    if modelo == "carrossel" and variacoes > 1:
        raise ErroFacilita("Variações de layout valem para peças avulsas, não para carrossel.")

    nome = slug(str(dados.get("peca") or caminho.stem))
    base = Path(pasta_saida) / "imagens" / nome
    n = 1
    while (base / f"v{n:02d}").exists():
        n += 1
    pasta = base / f"v{n:02d}"
    pasta.mkdir(parents=True)

    logo = marca.exigir_logo()
    aviso = marca.dados["avisos"]["evisa_mexico"] if dados.get("aviso_evisa") else None
    selo = marca.exigir_selo() if dados.get("selo") else None
    origens = [caminho, logo, selo] + [f for t in prep["telas"] for f in t["fotos"]]
    contexto_base = {
        "fontes_css": fontes_css(marca),
        "cores": marca.cores,
        "logo_uri": logo.resolve().as_uri(),
        "aviso": aviso,
        "selo_uri": selo.resolve().as_uri() if selo else None,
        "selo_largura": (marca.dados.get("selo") or {}).get("largura_imagem", 180),
    }
    saidas = []
    total_telas = len(prep["telas"])
    with navegador() as browser:
        for formato in formatos:
            if formato not in marca.imagens["formatos"]:
                raise ErroFacilita(f"Formato '{formato}' desconhecido ({', '.join(marca.imagens['formatos'])}).")
            largura, altura = marca.imagens["formatos"][formato]
            trabalhos = [(i, t, k) for i, t in enumerate(prep["telas"]) for k in range(variacoes)]
            for i, t, k in trabalhos:
                sufixo = f"_var{k + 1}" if variacoes > 1 else ""
                if modelo == "carrossel":
                    mod_html = f"carrossel_{t['tela']['modelo']}"
                    arquivo = pasta / f"{nome}_carrossel_{i + 1:02d}_{largura}x{altura}.png"
                else:
                    mod_html = _modelo_html(modelo, formato)
                    arquivo = pasta / f"{nome}_{modelo}_{formato}_{largura}x{altura}{sufixo}.png"
                garantir_saida_segura(arquivo, origens)
                ctx = {
                    **contexto_base,
                    "largura": largura,
                    "altura": altura,
                    "seguro_story": formato == "story",
                    "c": t["campos"],
                    "o": t["oferta"] or None,
                    "fotos": [f.resolve().as_uri() for f in t["fotos"]],
                    "destaques": _destaques(t["tela"].get("destaques")),
                    "numero": f"{i + 1}/{total_telas}" if modelo == "carrossel" else None,
                    "variante": VARIANTES[k],
                }
                if not (modelo == "carrossel" and t["tela"]["modelo"] == "cta"):
                    ctx["aviso"] = None
                info = renderizar(browser, html(mod_html, ctx), arquivo, largura, altura,
                                  marca.imagens.get("escala_render", 2), manter_2x)
                if not info["imagens_ok"]:
                    raise ErroFacilita(f"{arquivo.name}: alguma imagem (foto ou logo) não carregou.")
                if not info["poppins_carregada"] and not permitir_fonte_substituta:
                    raise ErroFacilita(f"{arquivo.name}: a fonte Poppins não carregou no Chromium.")
                saidas.append({"formato": formato, "modelo_html": mod_html, "variacao": k + 1, **info})

    manifesto = salvar_manifesto(pasta / "manifesto.json", {
        "tipo": "imagem",
        "peca": str(caminho),
        "peca_conteudo": dados,
        "logo": impressao_arquivo(logo),
        "fotos": [{**impressao_arquivo(f), "origem": o.get("origem") if isinstance(o, dict) else None}
                  for t in prep["telas"] for f, o in zip(t["fotos"], t["tela"].get("fotos") or dados.get("fotos") or [])],
        "saidas": saidas,
        "avisos": [str(p) for p in problemas if p.nivel == "aviso"] + marca.avisos,
    })
    return {"pasta": str(pasta), "saidas": saidas, "manifesto": str(manifesto),
            "avisos": [str(p) for p in problemas if p not in erros(problemas)] + marca.avisos}
