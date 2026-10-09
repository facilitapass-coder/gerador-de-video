"""Capa do Reels: um quadro do vídeo reenquadrado em 9:16 com o título, no mesmo motor das imagens."""

from __future__ import annotations

from pathlib import Path

from ..marca import Marca, exigir_sem_erros
from ..util import ErroFacilita, ffmpeg, garantir_saida_segura, proxima_versao, salvar_manifesto, segundos
from ..video import ajustes as mod_ajustes
from ..video import roteiro as mod_roteiro
from ..video.analise import detectar_silencios
from ..video.cobertura import carregar_biblioteca, mapear
from ..video.importacao import sondar
from ..video.montagem import filtro_reenquadrar
from .render import fontes_css, html, navegador, renderizar


def gerar_capa(caminho_roteiro: Path | str, caminho_clips: Path | str, marca: Marca, pasta_saida: Path | str = "saida",
               bloco: int | None = None, quadro: str | float | None = None, titulo: str | None = None,
               permitir_fonte_substituta: bool = False) -> dict:
    """Usa o clip escolhido pelo mapa de cobertura para o bloco (padrão: o 1º bloco com imagem).

    `quadro` é o tempo dentro do bloco (padrão: meio do bloco). Título padrão: `capa_titulo`
    do roteiro, ou o título do roteiro.
    """
    caminho_roteiro = Path(caminho_roteiro)
    rot = mod_roteiro.ler(caminho_roteiro)
    mod_ajustes.aplicar(rot, mod_ajustes.carregar(caminho_roteiro), dict(marca.video))
    biblioteca, problemas = carregar_biblioteca(caminho_clips, marca)
    titulo = titulo or str(rot.meta.get("capa_titulo") or rot.titulo)
    problemas += marca.verificar_texto(titulo, "capa")
    problemas += marca.verificar_ativos(permitir_fonte_substituta)
    exigir_sem_erros(problemas, "Capa")

    narr = rot.arquivo("narracao")
    if not all(b.duracao for b in rot.blocos):
        dur = sondar(narr).duracao if narr and narr.exists() else None
        mod_roteiro.resolver_tempos(rot, dur, detectar_silencios(narr) if dur else [])
    escolhas = mapear(rot, biblioteca)
    if bloco is not None:
        escolha = next((e for e in escolhas if e.bloco == bloco), None)
        if escolha is None:
            raise ErroFacilita(f"Bloco {bloco} não existe no roteiro.")
    else:
        escolha = next((e for e in escolhas if e.coberto), None)
    if escolha is None or not escolha.clip:
        raise ErroFacilita("Nenhum bloco com imagem para tirar a capa. Indique outro bloco com --bloco.")
    clip = biblioteca.achar(escolha.clip)
    deslocamento = segundos(quadro) if quadro is not None else min(escolha.duracao, escolha.disponivel) / 2
    t = escolha.clip_inicio + min(deslocamento, max(0.0, escolha.disponivel - 0.05))

    pasta = Path(pasta_saida) / "reels" / rot.slug
    destino = proxima_versao(pasta, f"{rot.slug}_capa_1080x1920", "png")
    garantir_saida_segura(destino, [clip.arquivo, caminho_roteiro, Path(caminho_clips)])
    fundo = destino.with_name(destino.stem + "_quadro.jpg")
    filtro = filtro_reenquadrar(clip.info.largura_efetiva, clip.info.altura_efetiva,
                                (clip.enquadramento or marca.video["enquadramento_padrao"]) if clip.foco is None else "foco",
                                clip.foco)
    ffmpeg(["-ss", f"{t:.3f}", "-i", clip.arquivo, "-frames:v", "1", "-filter_complex", f"[0:v]{filtro}[v]",
            "-map", "[v]", "-q:v", "2", fundo], "extrair o quadro da capa")

    logo = marca.exigir_logo()
    ctx = {
        "fontes_css": fontes_css(marca), "cores": marca.cores, "logo_uri": logo.resolve().as_uri(),
        "largura": 1080, "altura": 1920, "seguro_story": True,
        "c": {"titulo": titulo, "subtitulo": rot.meta.get("capa_subtitulo", ""), "etiqueta": rot.meta.get("capa_etiqueta", "")},
        "fotos": [fundo.resolve().as_uri()],
    }
    with navegador() as browser:
        info = renderizar(browser, html("capa_reels", ctx), destino, 1080, 1920, marca.imagens.get("escala_render", 2))
    if not info["poppins_carregada"] and not permitir_fonte_substituta:
        raise ErroFacilita("A fonte Poppins não carregou no Chromium.")
    manifesto = salvar_manifesto(destino.with_suffix(".json"), {
        "tipo": "capa_reels", "roteiro": str(caminho_roteiro), "titulo": titulo, "bloco": escolha.bloco,
        "clip": str(clip.arquivo), "clip_origem": clip.origem, "tempo_no_clip": round(t, 3), **info,
    })
    return {"png": str(destino), "manifesto": str(manifesto), "bloco": escolha.bloco, "clip": clip.nome, "tempo": t,
            "avisos": list(marca.avisos)}
