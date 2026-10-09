"""Critérios de aceite do gerador de imagens (Chromium via Playwright)."""

import datetime as dt
import shutil

import pytest
from PIL import Image

from facilita_studio.imagens.gerador import gerar, validar
from facilita_studio.imagens.render import navegador
from facilita_studio.marca import erros
from facilita_studio.util import ErroFacilita

HOJE = dt.date(2026, 10, 9)


def _chromium_ok() -> bool:
    try:
        with navegador():
            return True
    except Exception:  # noqa: BLE001
        return False


precisa_chromium = pytest.mark.skipif(not _chromium_ok(), reason="Chromium indisponível")


def _peca(tmp_path, texto_oferta: str = "", modelo: str = "carrossel") -> "Path":
    Image.new("RGB", (1200, 900), (40, 120, 180)).save(tmp_path / "foto.jpg")
    oferta = texto_oferta or """oferta:
  aeroporto_saida: GRU
  all_inclusive: true
  bagagem: mão
  valor_total_casal: 25980
  parcelas: 10
  validade: 2026-12-15
  pagamento: 10x sem juros no cartão
"""
    telas = """telas:
  - modelo: capa
    campos: {titulo: Hotel Xcaret Arte}
  - modelo: miolo
    campos: {titulo: Valores}
""" if modelo == "carrossel" else ""
    arq = tmp_path / "peca.yaml"
    arq.write_text(f"""peca: Teste carrossel
modelo: {modelo}
campos: {{titulo: Hotel Xcaret Arte, cta: Comente ARTE}}
fotos:
  - arquivo: foto.jpg
    origem: Drive oficial Xcaret
{oferta}{telas}""", encoding="utf-8")
    return arq


def test_validacao_recusa_sem_aeroporto(tmp_path, marca):
    arq = _peca(tmp_path, "oferta:\n  valor_total_casal: 1000\n  validade: 2026-12-15\n  pagamento: à vista\n")
    problemas, _ = validar(arq, marca, HOJE)
    assert any("aeroporto" in p.mensagem for p in erros(problemas))
    with pytest.raises(ErroFacilita):
        gerar(arq, marca, tmp_path / "saida", permitir_fonte_substituta=True, hoje=HOJE)


def test_validacao_recusa_sem_validade(tmp_path, marca):
    arq = _peca(tmp_path, "oferta:\n  aeroporto_saida: GRU\n  valor_total_casal: 1000\n  pagamento: à vista\n")
    assert any("validade" in p.mensagem for p in erros(validar(arq, marca, HOJE)[0]))


@precisa_chromium
def test_carrossel_feed_1080x1350_com_marca(tmp_path, marca):
    arq = _peca(tmp_path)
    r = gerar(arq, marca, tmp_path / "saida", permitir_fonte_substituta=True, hoje=HOJE)
    pngs = [s["png"] for s in r["saidas"]]
    assert len(pngs) == 3  # capa, miolo e CTA acrescentado no fim
    for png in pngs:
        with Image.open(png) as im:
            assert im.size == (1080, 1350)
            cores = im.convert("RGB").getcolors(1080 * 1350)
        marinho = sum(n for n, c in cores if c == (13, 45, 94))
        assert marinho > 10000  # fundo/véu na cor da marca
    assert pngs[-1].endswith("_carrossel_03_1080x1350.png")
    # refazer trocando só o texto gera nova versão, sem apagar a anterior
    arq.write_text(arq.read_text(encoding="utf-8").replace("Valores", "Preços"), encoding="utf-8")
    r2 = gerar(arq, marca, tmp_path / "saida", permitir_fonte_substituta=True, hoje=HOJE)
    assert r2["pasta"].endswith("v02") and all(Path(p).exists() for p in pngs)


@precisa_chromium
def test_oferta_story_e_whatsapp(tmp_path, marca):
    arq = _peca(tmp_path, modelo="oferta")
    r = gerar(arq, marca, tmp_path / "saida", formatos=["feed", "story", "whatsapp"],
              permitir_fonte_substituta=True, hoje=HOJE)
    tamanhos = [Image.open(s["png"]).size for s in r["saidas"]]
    assert tamanhos == [(1080, 1350), (1080, 1920), (1080, 1920)]


@precisa_chromium
def test_poppins_carregada_quando_instalada(tmp_path, marca):
    """Com arquivos de fonte na pasta da marca, o Chromium carrega a família 'Poppins'."""
    fontes = marca.pasta / "fontes"
    fontes.mkdir()
    for peso, arq in marca.dados["fonte"]["arquivos"].items():
        shutil.copy("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", marca.pasta / arq)
    r = gerar(_peca(tmp_path, modelo="oferta"), marca, tmp_path / "saida", hoje=HOJE)
    assert r["saidas"][0]["poppins_carregada"]


@precisa_chromium
def test_variacoes_e_selo(tmp_path, marca):
    arq = _peca(tmp_path, modelo="oferta")
    arq.write_text("selo: true\n" + arq.read_text(encoding="utf-8"), encoding="utf-8")
    r = gerar(arq, marca, tmp_path / "saida", variacoes=3, permitir_fonte_substituta=True, hoje=HOJE)
    pngs = [s["png"] for s in r["saidas"]]
    assert [p[-8:] for p in pngs] == ["var1.png", "var2.png", "var3.png"]
    with Image.open(pngs[2]) as im:
        cores = im.convert("RGB").getcolors(1080 * 1350)
    assert sum(n for n, c in cores if c == (232, 87, 42)) > 50000  # variação 3: fundo laranja
    with pytest.raises(ErroFacilita):
        gerar(_peca(tmp_path), marca, tmp_path / "saida", variacoes=2, permitir_fonte_substituta=True, hoje=HOJE)


@precisa_chromium
def test_capa_do_reels(tmp_path, midia, marca):
    from facilita_studio.imagens.capa import gerar_capa

    from conftest import criar_roteiro

    roteiro, clips = criar_roteiro(tmp_path, midia)
    r = gerar_capa(roteiro, clips, marca, tmp_path / "saida", bloco=2, permitir_fonte_substituta=True)
    assert r["bloco"] == 2 and r["clip"] == "piscina_vertical.mp4"
    with Image.open(r["png"]) as im:
        assert im.size == (1080, 1920)


from pathlib import Path  # noqa: E402
