import datetime as dt

from facilita_studio.imagens import ofertas
from facilita_studio.marca import erros

HOJE = dt.date(2026, 10, 9)
BASE = {
    "aeroporto_saida": "GRU",
    "all_inclusive": True,
    "bagagem": "mão",
    "valor_total_casal": 25980,
    "parcelas": 10,
    "validade": "2026-12-15",
    "pagamento": "10x sem juros",
}


def test_oferta_valida_monta_textos():
    problemas, t = ofertas.validar(BASE, HOJE)
    assert not erros(problemas)
    assert t["preco_linha"] == "10x de R$ 2.598 por casal"
    assert t["total_linha"] == "Total R$ 25.980 para 2 pessoas"
    assert t["saida"] == "Saindo de GRU" and t["bagagem"] == "Bagagem de mão"
    assert t["validade"] == "Válido até 15/12/2026"


def test_recusa_sem_aeroporto_ou_validade():
    for chave in ("aeroporto_saida", "validade", "pagamento"):
        o = {k: v for k, v in BASE.items() if k != chave}
        assert erros(ofertas.validar(o, HOJE)[0]), chave


def test_all_inclusive_so_bagagem_de_mao():
    assert erros(ofertas.validar({**BASE, "bagagem": "despachada 23kg"}, HOJE)[0])


def test_parcela_sobre_total_do_casal():
    assert erros(ofertas.validar({**BASE, "valor_parcela": 1299}, HOJE)[0])  # parcela por pessoa
    assert not erros(ofertas.validar({**BASE, "valor_parcela": 2598}, HOJE)[0])
    assert erros(ofertas.validar({**BASE, "valor_por_pessoa": 10000}, HOJE)[0])


def test_oferta_vencida():
    assert erros(ofertas.validar({**BASE, "validade": "2026-10-01"}, HOJE)[0])


def test_texto_livre_por_pessoa():
    assert ofertas.verificar_textos_livres({"subtitulo": "10x de R$ 1.299 por pessoa"})


def test_formato_reais():
    assert ofertas.reais(1234567.5) == "R$ 1.234.567,50"
