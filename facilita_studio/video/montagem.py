"""Montagem do Reels: reenquadramento, corte por bloco, títulos, áudio, CTA e exportação."""

from __future__ import annotations

import math
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..marca import Marca, Problema, exigir_sem_erros
from ..util import (
    ErroFacilita,
    ffmpeg,
    garantir_saida_segura,
    impressao_arquivo,
    proxima_versao,
    salvar_manifesto,
)
from . import roteiro as mod_roteiro
from .analise import detectar_silencios, medir_volume
from .cobertura import Biblioteca, Escolha, carregar_biblioteca, mapear, salvar_relatorio
from .importacao import InfoMidia, sondar
from .sobreposicoes import cta_png, titulo_png


# ---------------------------------------------------------------- reenquadramento
def filtro_reenquadrar(largura: int, altura: int, modo: str = "centro", foco: float | None = None,
                       W: int = 1080, H: int = 1920) -> str:
    """Filtro ffmpeg que leva um clip de qualquer proporção a W×H (9:16).

    centro    : preenche a tela e corta as sobras pelo centro
    foco      : preenche e corta, com o ponto horizontal `foco` (0 = esquerda, 1 = direita)
    desfocado : clip inteiro no meio, sobre uma cópia ampliada e desfocada dele mesmo
    """
    if largura <= 0 or altura <= 0:
        raise ErroFacilita("Clip sem resolução conhecida.")

    def par(x: float) -> int:
        return max(2, int(math.ceil(x / 2.0) * 2))

    s_fill = max(W / largura, H / altura)
    fw, fh = par(largura * s_fill), par(altura * s_fill)
    fx = 0.5 if foco is None else min(1.0, max(0.0, float(foco)))
    cx, cy = int((fw - W) * fx), (fh - H) // 2
    preencher = f"scale={fw}:{fh}:flags=lanczos,crop={W}:{H}:{cx}:{cy}"
    if modo in ("centro", "foco"):
        return preencher
    if modo == "desfocado":
        s_fit = min(W / largura, H / altura)
        gw, gh = par(largura * s_fit), par(altura * s_fit)
        return (
            f"split=2[fundo][frente];[fundo]{preencher},boxblur=luma_radius=40:luma_power=2,eq=brightness=-0.06[f];"
            f"[frente]scale={gw}:{gh}:flags=lanczos[g];[f][g]overlay=(W-w)/2:(H-h)/2"
        )
    raise ErroFacilita(f"Enquadramento '{modo}' desconhecido.")


# ---------------------------------------------------------------- plano
@dataclass
class Segmento:
    bloco: int
    duracao: float           # tempo do bloco na linha do tempo final
    entrada: float           # antecipação para a transição de entrada (0 em corte seco)
    escolha: Escolha
    tela: str = ""
    modo: str = "centro"
    foco: float | None = None
    arquivo: Path | None = None
    titulo_png: Path | None = None

    @property
    def comprimento(self) -> float:
        return self.duracao + self.entrada


@dataclass
class Resultado:
    mp4: Path
    manifesto: Path
    cobertura: Path
    duracao: float
    avisos: list[str] = field(default_factory=list)
    medidas: dict = field(default_factory=dict)


def _modo(bloco, escolha: Escolha, biblioteca: Biblioteca, marca: Marca) -> tuple[str, float | None]:
    clip = biblioteca.achar(escolha.clip) if escolha.clip else None
    modo = bloco.enquadramento or (clip.enquadramento if clip else None) or marca.video["enquadramento_padrao"]
    foco = bloco.foco if bloco.foco is not None else (clip.foco if clip else None)
    if foco is not None and modo == "centro":
        modo = "foco"
    return modo, foco


def verificar_textos(rot: mod_roteiro.Roteiro, marca: Marca) -> list[Problema]:
    problemas = []
    for b in rot.blocos:
        problemas += marca.verificar_texto(b.tela, f"bloco {b.numero} (tela)")
        problemas += marca.verificar_texto(b.narracao_limpa, f"bloco {b.numero} (narração)")
    problemas += marca.verificar_texto(rot.cta, "CTA")
    problemas += marca.verificar_texto(str(rot.meta.get("cta_subtitulo", "")), "CTA (subtítulo)")
    return problemas


# ---------------------------------------------------------------- render
def _render_segmento(seg: Segmento, info: InfoMidia | None, marca: Marca, destino: Path, previa: bool) -> Path:
    v = marca.video
    W, H, fps = v["largura"], v["altura"], v["fps"]
    L = seg.comprimento
    args: list[str] = []
    if seg.escolha.clip and info:
        inicio = max(0.0, seg.escolha.clip_inicio - seg.entrada)
        args += ["-ss", f"{inicio:.3f}", "-t", f"{L + 0.5:.3f}", "-i", seg.escolha.clip]
        base = f"[0:v]{filtro_reenquadrar(info.largura_efetiva, info.altura_efetiva, seg.modo, seg.foco, W, H)}"
    else:
        args += ["-f", "lavfi", "-t", f"{L:.3f}", "-i", f"color=c={marca.cores['marinho'].replace('#', '0x')}:s={W}x{H}:r={fps}"]
        base = "[0:v]null"
    grafo = (
        f"{base},fps={fps},setsar=1,tpad=stop_mode=clone:stop_duration={L:.3f},"
        f"trim=duration={L:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]"
    )
    saida = "[v]"
    if seg.titulo_png:
        args += ["-loop", "1", "-t", f"{L:.3f}", "-i", seg.titulo_png]
        ini = seg.entrada + 0.15
        fim = max(ini + 0.4, L - 0.45)
        grafo += (
            f";[1:v]format=rgba,fade=in:st={ini:.3f}:d=0.3:alpha=1,fade=out:st={fim:.3f}:d=0.3:alpha=1[t];"
            f"[v][t]overlay=0:0:format=auto,format=yuv420p[o]"
        )
        saida = "[o]"
    ffmpeg(
        [*args, "-filter_complex", grafo, "-map", saida, "-an", "-c:v", "libx264",
         "-preset", "ultrafast" if previa else "veryfast", "-crf", "24" if previa else "12",
         "-r", str(fps), "-pix_fmt", "yuv420p", "-fflags", "+bitexact", "-flags:v", "+bitexact", destino],
        f"montar o bloco {seg.bloco}",
    )
    return destino


def _filtros_audio(total: float, tem_voz: bool, tem_musica: bool, marca: Marca, idx_voz: int, idx_mus: int) -> tuple[list[str], str | None]:
    v = marca.video
    partes, saidas = [], []
    if tem_voz:
        ruido = "afftdn=nf=-25," if v.get("reducao_ruido", True) else ""
        partes.append(
            f"[{idx_voz}:a]aresample=48000,aformat=channel_layouts=stereo,{ruido}"
            f"volume={v['voz_ganho_db']}dB,apad,atrim=0:{total:.3f},asetpts=PTS-STARTPTS[voz]"
        )
        saidas.append("[voz]")
    if tem_musica:
        v0, v1, d = v["musica_volume"], v["musica_volume_final"], v["musica_subida_segundos"]
        t0 = max(0.0, total - d)
        partes.append(
            f"[{idx_mus}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
            f"volume='if(lt(t,{t0:.3f}),{v0},{v0}+({v1}-{v0})*(t-{t0:.3f})/{d})':eval=frame,"
            f"afade=t=out:st={max(0.0, total - 0.4):.3f}:d=0.4[mus]"
        )
        saidas.append("[mus]")
    if not saidas:
        return partes, None
    if len(saidas) == 2:
        partes.append("[voz][mus]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95:level=disabled[a]")
    else:
        partes.append(f"{saidas[0]}alimiter=limit=0.95:level=disabled[a]")
    return partes, "[a]"


def _medir_mix(narracao: Path | None, musica: Path | None, total: float, fala_ate: float, marca: Marca, pasta: Path) -> dict:
    """Mede voz e música já processadas, no trecho em que há fala."""
    medidas: dict = {}
    for nome, arq, tem_voz, tem_mus in (("voz", narracao, True, False), ("musica", musica, False, True)):
        if not arq:
            continue
        args = ["-i", arq] if tem_voz else ["-stream_loop", "-1", "-i", arq]
        partes, _ = _filtros_audio(total, tem_voz, tem_mus, marca, 0, 0)
        grafo = partes[0]
        wav = pasta / f"_medida_{nome}.wav"
        ffmpeg([*args, "-filter_complex", grafo, "-map", f"[{'voz' if tem_voz else 'mus'}]", "-t", f"{total:.3f}", wav], f"medir {nome}")
        medidas[nome] = medir_volume(wav, 0.0, fala_ate)
    if "voz" in medidas and "musica" in medidas:
        medidas["voz_acima_da_musica_db"] = round(medidas["voz"]["media_db"] - medidas["musica"]["media_db"], 1)
    return medidas


def montar(
    caminho_roteiro: Path | str,
    caminho_clips: Path | str,
    marca: Marca,
    pasta_saida: Path | str = "saida",
    previa: bool = False,
    manter_trabalho: bool = False,
    permitir_fonte_substituta: bool = False,
) -> Resultado:
    caminho_roteiro, caminho_clips, pasta_saida = Path(caminho_roteiro), Path(caminho_clips), Path(pasta_saida)
    rot = mod_roteiro.ler(caminho_roteiro)
    biblioteca, problemas = carregar_biblioteca(caminho_clips, marca)
    v = marca.video

    narracao = rot.arquivo("narracao")
    musica = rot.arquivo("musica")
    if narracao and not narracao.exists():
        raise ErroFacilita(f"Narração não encontrada: {narracao}")
    if musica:
        if not musica.exists():
            raise ErroFacilita(f"Música não encontrada: {musica}")
        problemas += marca.verificar_origem(rot.meta.get("musica_origem"), musica.name, "musica")
    problemas += verificar_textos(rot, marca)
    problemas += marca.verificar_ativos(permitir_fonte_substituta)
    exigir_sem_erros(problemas, "Reels")

    info_narr = sondar(narracao) if narracao else None
    silencios = detectar_silencios(narracao) if narracao and not all(b.duracao for b in rot.blocos) else []
    mod_roteiro.resolver_tempos(rot, info_narr.duracao if info_narr else None, silencios)

    escolhas = mapear(rot, biblioteca)
    pasta_rel = pasta_saida / "reels" / rot.slug
    cobertura_md, _ = salvar_relatorio(rot, escolhas, pasta_rel)

    fala_ate = rot.blocos[-1].fim or 0.0
    respiro = float(rot.meta.get("respiro_final", v["respiro_final"]))
    total = round(fala_ate + respiro, 3)
    if total > v["duracao_maxima"] + 1e-6:
        raise ErroFacilita(
            f"O Reels teria {total:.1f}s (fala até {fala_ate:.1f}s + {respiro:.1f}s de respiro); o máximo é {v['duracao_maxima']}s."
        )

    logo = marca.exigir_logo()
    trabalho = pasta_rel / "_trabalho"
    if trabalho.exists():
        shutil.rmtree(trabalho)
    trabalho.mkdir(parents=True)

    transicao_padrao = rot.meta.get("transicao", v["transicao"])
    T = float(v["transicao_duracao"])
    segmentos: list[Segmento] = []
    for i, (b, e) in enumerate(zip(rot.blocos, escolhas)):
        trans = (b.transicao or transicao_padrao).lower()
        entrada = T if (i > 0 and trans.startswith("fade")) else 0.0
        duracao = e.duracao + (respiro if i == len(rot.blocos) - 1 else 0.0)
        modo, foco = _modo(b, e, biblioteca, marca)
        seg = Segmento(b.numero, duracao, entrada, e, b.tela, modo, foco)
        if b.tela:
            seg.titulo_png = titulo_png(b.tela, trabalho / f"titulo_{b.numero:02d}.png", marca,
                                        str(rot.meta.get("posicao_titulo", "topo")))
        segmentos.append(seg)

    for seg in segmentos:
        info = biblioteca.achar(seg.escolha.clip).info if seg.escolha.clip else None
        seg.arquivo = _render_segmento(seg, info, marca, trabalho / f"bloco_{seg.bloco:02d}.mp4", previa)

    cta_ini = max(0.0, total - float(v["cta_duracao"]))
    cta_arquivo = cta_png(rot.cta or "Fale com a Facilita Pass", trabalho / "cta.png", marca, logo,
                          str(rot.meta.get("cta_subtitulo", "")))

    # ---- passo final: emenda, CTA + logo até o último quadro, áudio
    destino = proxima_versao(pasta_rel, f"{rot.slug}_reels_{'previa' if previa else '1080x1920'}", "mp4")
    origens = [c.arquivo for c in biblioteca.clips] + [narracao, musica, caminho_roteiro, caminho_clips]
    garantir_saida_segura(destino, origens)

    args: list[str] = []
    for seg in segmentos:
        args += ["-i", seg.arquivo]
    n = len(segmentos)
    args += ["-loop", "1", "-t", f"{total:.3f}", "-i", cta_arquivo]
    idx_voz = n + 1
    if narracao:
        args += ["-i", narracao]
    idx_mus = n + 1 + (1 if narracao else 0)
    if musica:
        args += ["-stream_loop", "-1", "-i", musica]

    grafo: list[str] = []
    atual, acumulado = "[0:v]", segmentos[0].comprimento
    for k in range(1, n):
        seg = segmentos[k]
        rotulo = f"[x{k}]"
        if seg.entrada > 0:
            grafo.append(f"{atual}[{k}:v]xfade=transition=fade:duration={seg.entrada:.3f}:offset={acumulado - seg.entrada:.3f}{rotulo}")
            acumulado += seg.comprimento - seg.entrada
        else:
            grafo.append(f"{atual}[{k}:v]concat=n=2:v=1:a=0{rotulo}")
            acumulado += seg.comprimento
        atual = rotulo
    grafo.append(
        f"[{n}:v]format=rgba,fade=in:st={cta_ini:.3f}:d=0.4:alpha=1[cta];"
        f"{atual}[cta]overlay=0:0:enable='gte(t,{cta_ini:.3f})':format=auto,trim=duration={total:.3f},format=yuv420p"
        + (",scale=540:960" if previa else "") + "[vf]"
    )
    partes_audio, rotulo_audio = _filtros_audio(total, bool(narracao), bool(musica), marca, idx_voz, idx_mus)
    grafo += partes_audio
    mapas = ["-map", "[vf]"] + (["-map", rotulo_audio] if rotulo_audio else [])
    ffmpeg(
        [*args, "-filter_complex", ";".join(grafo), *mapas,
         "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(v["fps"]),
         "-preset", "ultrafast" if previa else "medium", "-crf", "28" if previa else str(v["crf"]),
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.3f}",
         "-movflags", "+faststart", "-map_metadata", "-1", "-fflags", "+bitexact",
         "-flags:v", "+bitexact", "-flags:a", "+bitexact", destino],
        "exportar o Reels",
    )

    final = sondar(destino)
    medidas = {
        "duracao": round(final.duracao, 2),
        "resolucao": f"{final.largura}x{final.altura}",
        "cta_inicio": cta_ini,
        "fala_ate": fala_ate,
    }
    medidas.update(_medir_mix(narracao, musica, total, max(0.5, fala_ate), marca, trabalho))

    avisos = list(marca.avisos)
    avisos += [f"Bloco {e.bloco} sem imagem: {e.motivo}" for e in escolhas if not e.coberto]
    avisos += [f"Bloco {e.bloco}: {e.motivo}" for e in escolhas if e.situacao == "curto"]
    if "voz_acima_da_musica_db" in medidas and medidas["voz_acima_da_musica_db"] < 6:
        avisos.append(f"Voz só {medidas['voz_acima_da_musica_db']} dB acima da música; considere baixar a trilha.")

    manifesto = salvar_manifesto(
        destino.with_suffix(".json"),
        {
            "tipo": "reels",
            "saida": str(destino),
            "previa": previa,
            "roteiro": {"arquivo": str(caminho_roteiro), "sha256": rot.hash, "titulo": rot.titulo},
            "biblioteca": str(caminho_clips),
            "narracao": impressao_arquivo(narracao) if narracao else None,
            "musica": {**impressao_arquivo(musica), "origem": rot.meta.get("musica_origem")} if musica else None,
            "blocos": [
                {"bloco": s.bloco, "tela": s.tela, "duracao": s.duracao, "entrada": s.entrada, "enquadramento": s.modo,
                 "foco": s.foco, **asdict(s.escolha),
                 "clip_origem": (biblioteca.achar(s.escolha.clip).origem if s.escolha.clip else None)}
                for s in segmentos
            ],
            "clips_usados": [impressao_arquivo(Path(c)) for c in sorted({s.escolha.clip for s in segmentos if s.escolha.clip})],
            "parametros": v,
            "medidas": medidas,
            "avisos": avisos,
        },
    )
    if not manter_trabalho:
        shutil.rmtree(trabalho, ignore_errors=True)
    return Resultado(destino, manifesto, cobertura_md, final.duracao, avisos, medidas)
