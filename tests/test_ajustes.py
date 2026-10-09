import pytest

from facilita_studio.util import ErroFacilita
from facilita_studio.video import ajustes as aj
from facilita_studio.video import roteiro as r

VIDEO = {"voz_ganho_db": 7, "musica_volume": 0.12}


def test_interpreta_pedidos():
    a: dict = {}
    assert "removido" in aj.interpretar("Tira o bloco 5", a, VIDEO)
    aj.interpretar("voz mais alta", a, VIDEO)
    aj.interpretar("música mais alta", a, VIDEO)
    aj.interpretar("troca o clip do bloco 3 por quarto.mp4 @ 0:02", a, VIDEO)
    aj.interpretar("texto do bloco 2: Piscinas com vista", a, VIDEO)
    aj.interpretar("bloco 1 foco 0.3", a, VIDEO)
    aj.interpretar("com legendas", a, VIDEO)
    aj.interpretar("com selo", a, VIDEO)
    assert a["remover"] == [5]
    assert a["voz_ganho_db"] == 9.0 and a["musica_volume"] == 0.14
    assert a["blocos"][3] == {"clip": "quarto.mp4", "clip_inicio": 2.0}
    assert a["blocos"][2]["tela"] == "Piscinas com vista"
    assert a["blocos"][1]["enquadramento"] == "foco 0.3"
    assert a["legendas"] is True and a["selo"] is True
    aj.interpretar("volta o bloco 5", a, VIDEO)
    assert a["remover"] == []


def test_musica_fica_entre_10_e_15_por_cento():
    a: dict = {}
    for _ in range(5):
        aj.interpretar("música mais alta", a, VIDEO)
    assert a["musica_volume"] == 0.15
    for _ in range(5):
        aj.interpretar("musica mais baixa", a, VIDEO)
    assert a["musica_volume"] == 0.10


def test_pedido_desconhecido():
    with pytest.raises(ErroFacilita, match="Não entendi"):
        aj.interpretar("faz um café", {}, VIDEO)


def test_salva_ao_lado_sem_tocar_roteiro(tmp_path):
    rot = tmp_path / "roteiro.md"
    rot.write_text("## Bloco 1\n- tempo: 0:00–0:02\n\n## Bloco 2\n- tempo: 0:02–0:04\n", encoding="utf-8")
    antes = rot.read_text(encoding="utf-8")
    a: dict = {}
    aj.interpretar("tira o bloco 2", a, VIDEO)
    aj.interpretar("texto do bloco 1: Novo", a, VIDEO)
    destino = aj.salvar(rot, a)
    assert destino.name == "roteiro.ajustes.yaml" and rot.read_text(encoding="utf-8") == antes
    roteiro = r.ler(rot)
    params = dict(VIDEO)
    assert aj.aplicar(roteiro, aj.carregar(rot), params) == [2]
    assert roteiro.blocos[0].tela == "Novo"


def test_bloco_inexistente(tmp_path):
    rot = tmp_path / "roteiro.md"
    rot.write_text("## Bloco 1\n- tempo: 0:00–0:02\n", encoding="utf-8")
    with pytest.raises(ErroFacilita, match="não existe"):
        aj.aplicar(r.ler(rot), {"remover": [9]}, dict(VIDEO))
    with pytest.raises(ErroFacilita, match="todos"):
        aj.aplicar(r.ler(rot), {"remover": [1]}, dict(VIDEO))
