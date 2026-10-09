import pytest

from facilita_studio.util import ErroFacilita
from facilita_studio.video import roteiro as r

ROTEIRO = """---
titulo: Hotel Xcaret Arte
cta: Comente ARTE
---

## Bloco 1 · Abertura
- tempo: 0:00–0:06
- imagem: fachada do hotel
- tela: Hotel Xcaret Arte
- clip: fachada.mp4 @ 0:03
- enquadramento: foco 0.3

Olá, [pausa 0.5s] este é o Xcaret Arte.

## Bloco 2 · Piscina
- tempo: 0:06 - 0:12.5
- imagem: piscina
- enquadramento: desfocado

Texto do bloco dois.
"""


def test_le_blocos(tmp_path):
    arq = tmp_path / "r.md"
    arq.write_text(ROTEIRO, encoding="utf-8")
    rot = r.ler(arq)
    assert rot.titulo == "Hotel Xcaret Arte" and rot.slug == "hotel-xcaret-arte" and rot.cta == "Comente ARTE"
    b1, b2 = rot.blocos
    assert (b1.numero, b1.nome, b1.inicio, b1.fim) == (1, "Abertura", 0, 6)
    assert b1.clip == "fachada.mp4" and b1.clip_inicio == 3
    assert b1.enquadramento == "foco" and b1.foco == 0.3
    assert b1.narracao_limpa == "Olá, este é o Xcaret Arte."
    assert b1.pausas() == 0.5
    assert b2.duracao == 6.5 and b2.enquadramento == "desfocado"


def test_estima_tempos_pela_narracao(tmp_path):
    arq = tmp_path / "r.md"
    arq.write_text("## Um\num dois três quatro\n\n## Dois\num dois três quatro\n", encoding="utf-8")
    rot = r.ler(arq)
    r.resolver_tempos(rot, 10.0, silencios=[(5.2, 5.6)])
    assert rot.blocos[0].fim == pytest.approx(5.4)
    assert rot.blocos[1].fim == 10.0


def test_tempo_invalido(tmp_path):
    arq = tmp_path / "r.md"
    arq.write_text("## Bloco 1\n- tempo: 0:06–0:02\n", encoding="utf-8")
    with pytest.raises(ErroFacilita):
        r.ler(arq)
