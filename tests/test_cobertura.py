from facilita_studio.video import roteiro as r
from facilita_studio.video.cobertura import carregar_biblioteca, mapear, relatorio_markdown

from conftest import criar_roteiro


def test_mapa_aponta_clip_e_falta(tmp_path, midia, marca):
    blocos = """## Bloco 1 · Praia
- tempo: 0:00–0:02
- imagem: praia com mar

## Bloco 2 · Spa
- tempo: 0:02–0:03
- imagem: spa e jardim

## Bloco 3 · Piscina longa
- tempo: 0:03–0:09
- imagem: piscina
"""
    roteiro, clips = criar_roteiro(tmp_path, midia, blocos=blocos)
    bib, problemas = carregar_biblioteca(clips, marca)
    assert not problemas
    escolhas = mapear(r.ler(roteiro), bib)
    assert escolhas[0].clip.endswith("praia_horizontal.mp4") and escolhas[0].situacao == "coberto"
    assert escolhas[1].clip is None and escolhas[1].situacao == "sem imagem"
    assert escolhas[2].situacao == "curto"
    md = relatorio_markdown(r.ler(roteiro), escolhas)
    assert "O que falta gravar" in md and "spa e jardim" in md


def test_clip_sem_origem_e_recusado(tmp_path, midia, marca):
    clips = tmp_path / "clips.yaml"
    clips.write_text(f"clips:\n  - arquivo: {midia / 'praia_horizontal.mp4'}\n    descricao: praia\n", encoding="utf-8")
    _, problemas = carregar_biblioteca(clips, marca)
    assert problemas and problemas[0].nivel == "erro"
