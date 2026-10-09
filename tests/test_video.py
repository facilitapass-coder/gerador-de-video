"""Critérios de aceite do editor de vídeo, com mídia sintética curta."""

import hashlib
import subprocess

import pytest
from PIL import Image

from facilita_studio.util import ErroFacilita
from facilita_studio.video.importacao import sondar
from facilita_studio.video.montagem import filtro_reenquadrar, montar
from facilita_studio.video.sobreposicoes import cta_png, dentro_da_zona_segura, titulo_png

from conftest import criar_roteiro, ff


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_sondar(midia):
    h = sondar(midia / "praia_horizontal.mp4")
    v = sondar(midia / "piscina_vertical.mp4")
    a = sondar(midia / "narracao.wav")
    assert (h.orientacao, v.orientacao, a.tipo) == ("horizontal", "vertical", "audio")
    assert h.duracao == pytest.approx(4, abs=0.1)


@pytest.mark.parametrize("modo", ["centro", "foco", "desfocado"])
def test_reenquadrar_para_9x16(tmp_path, midia, modo):
    saida = tmp_path / f"{modo}.mp4"
    filtro = filtro_reenquadrar(640, 360, modo, 0.2 if modo == "foco" else None)
    ff("-i", midia / "praia_horizontal.mp4", "-t", "0.5", "-filter_complex", f"[0:v]{filtro}[v]", "-map", "[v]",
       "-c:v", "libx264", "-preset", "ultrafast", saida)
    info = sondar(saida)
    assert (info.largura, info.altura) == (1080, 1920)


def test_titulos_e_cta_dentro_da_zona_segura(tmp_path, marca):
    longo = "Um título bem comprido para testar a quebra de linhas dentro da área segura do Reels"
    for pos in ("topo", "centro", "baixo"):
        assert dentro_da_zona_segura(titulo_png(longo, tmp_path / f"t_{pos}.png", marca, pos), marca)
    cta = cta_png("Comente ARTE", tmp_path / "cta.png", marca, marca.exigir_logo(), "Saída de GRU")
    assert dentro_da_zona_segura(cta, marca, ignorar_veu=True)


def test_reels_completo(tmp_path, midia, marca):
    roteiro, clips = criar_roteiro(tmp_path, midia)
    originais = {p: _sha(p) for p in midia.iterdir()}
    r = montar(roteiro, clips, marca, tmp_path / "saida", permitir_fonte_substituta=True)

    info = sondar(r.mp4)
    assert (info.largura, info.altura) == (1080, 1920)
    assert info.duracao == pytest.approx(4 + 1.5, abs=0.15)  # fala + respiro
    assert info.duracao <= 60
    assert r.mp4.name == "teste-praia_reels_1080x1920_v01.mp4"
    codec = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name",
                            "-of", "csv=p=0", str(r.mp4)], capture_output=True, text=True).stdout.strip()
    assert codec == "h264"

    # voz mais alta que a música; música na faixa de 10–15%
    assert r.medidas["voz_acima_da_musica_db"] > 6
    assert 0.10 <= marca.video["musica_volume"] <= 0.15

    # logo até o último quadro: o cartão branco do CTA aparece no último quadro
    ultimo = tmp_path / "ultimo.png"
    ff("-sseof", "-0.1", "-i", r.mp4, "-frames:v", "1", "-update", "1", ultimo)
    with Image.open(ultimo) as im:
        cores = im.convert("RGB").getcolors(1080 * 1920)
    laranja = sum(n for n, (rr, g, b) in cores if rr > 200 and 60 < g < 120 and b < 80)
    assert laranja > 5000  # logo/botão laranja visível

    # originais intocados; manifesto e mapa gravados
    assert all(_sha(p) == h for p, h in originais.items())
    assert r.manifesto.exists() and r.cobertura.exists()

    # nova montagem vira v02, sem sobrescrever
    r2 = montar(roteiro, clips, marca, tmp_path / "saida", previa=True, permitir_fonte_substituta=True)
    assert r2.mp4.name == "teste-praia_reels_previa_v01.mp4"
    assert (sondar(r2.mp4).largura, sondar(r2.mp4).altura) == (540, 960)


def test_reels_acima_de_60s_recusado(tmp_path, midia, marca):
    blocos = "## Bloco 1\n- tempo: 0:00–0:59.5\n- imagem: praia\n"
    roteiro, clips = criar_roteiro(tmp_path, midia, blocos=blocos)
    with pytest.raises(ErroFacilita, match="máximo"):
        montar(roteiro, clips, marca, tmp_path / "saida", permitir_fonte_substituta=True)


def test_reels_com_termo_proibido_recusado(tmp_path, midia, marca):
    blocos = "## Bloco 1\n- tempo: 0:00–0:02\n- imagem: praia\n- tela: Fale com o embaixador\n"
    roteiro, clips = criar_roteiro(tmp_path, midia, blocos=blocos)
    with pytest.raises(ErroFacilita, match="Xpert Xcaret"):
        montar(roteiro, clips, marca, tmp_path / "saida", permitir_fonte_substituta=True)


def test_reels_sem_poppins_recusado_por_padrao(tmp_path, midia, marca):
    roteiro, clips = criar_roteiro(tmp_path, midia)
    with pytest.raises(ErroFacilita, match="Poppins"):
        montar(roteiro, clips, marca, tmp_path / "saida")
