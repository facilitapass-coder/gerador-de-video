import json

from facilita_studio.versoes import comparar
from facilita_studio.video.legendas import frases_do_bloco, montar_frases, salvar_srt
from facilita_studio.video.roteiro import Bloco


def test_grafia_da_marca(marca):
    assert marca.corrigir_grafia("no xcaret com o cadillac em cancun") == "no Xcaret com o Cadillac em Cancún"


def test_frases_respeitam_pontuacao_e_pausas():
    b = Bloco(1, "x", 0, 6, narracao="Bem-vindo ao Xcaret Arte. [pausa 0.5s] Um hotel feito para quem gosta de arte e boa comida.")
    frases = frases_do_bloco(b, 32)
    assert frases[0] == "Bem-vindo ao Xcaret Arte."
    assert all(len(linha) <= 32 for f in frases for linha in f.split("\n"))
    assert all(f.count("\n") <= 1 for f in frases)


def test_tempos_dentro_do_bloco_e_corte_no_cta(marca, tmp_path):
    blocos = [Bloco(1, "a", 0, 4, narracao="Primeira frase. Segunda frase."), Bloco(2, "b", 4, 8, narracao="no xcaret.")]
    frases = montar_frases(blocos, marca, ate=6.0)
    assert frases[0].inicio == 0 and frases[-1].fim <= 6.0
    assert frases[-1].texto == "no Xcaret."
    srt = salvar_srt(frases, tmp_path / "x.srt").read_text(encoding="utf-8")
    assert "00:00:00,000 -->" in srt


def test_comparar_manifestos(tmp_path):
    base = {"tipo": "reels", "roteiro": {"sha256": "a"}, "parametros": {"voz_ganho_db": 7}, "medidas": {"duracao": 10},
            "blocos": [{"bloco": 1, "tela": "A", "clip": "/x/c.mp4"}, {"bloco": 2, "tela": "B", "clip": "/x/d.mp4"}]}
    novo = {**base, "parametros": {"voz_ganho_db": 9}, "medidas": {"duracao": 6},
            "blocos": [{"bloco": 1, "tela": "A2", "clip": "/y/c.mp4"}]}
    (tmp_path / "a.json").write_text(json.dumps(base))
    (tmp_path / "b.json").write_text(json.dumps(novo))
    linhas = comparar(tmp_path / "a.json", tmp_path / "b.json")
    assert "Bloco 1 · tela: A → A2" in linhas
    assert "Bloco 2: removido" in linhas
    assert "Parâmetro voz_ganho_db: 7 → 9" in linhas
    assert not any("clip" in l for l in linhas)  # mesmo arquivo em outra pasta
