import datetime as dt

import pytest
from PIL import Image

from facilita_studio.fila import Item, _horario, _numero, agendar, ler_planilha, linha_para_peca, processar
from facilita_studio.util import ErroFacilita

from test_imagens import precisa_chromium

HOJE = dt.date(2026, 10, 9)
HORARIOS = ["09:00", "12:30", "18:30"]
CABECALHO = ("peca;modelo;formatos;titulo;cta;foto;foto_origem;aeroporto_saida;all_inclusive;bagagem;"
             "valor_total_casal;parcelas;validade;pagamento;destino;data_publicacao;horario")


def _planilha(tmp_path, linhas: list[str]):
    Image.new("RGB", (800, 600), (40, 120, 180)).save(tmp_path / "foto.jpg")
    arq = tmp_path / "pautas.csv"
    arq.write_text("\n".join([CABECALHO, *linhas]) + "\n", encoding="utf-8")
    return arq


def test_conversoes():
    assert _numero("25.980,00") == 25980 and _numero("R$ 1299,5") == 1299.5 and _numero("10") == 10
    assert _horario("9h") == "09:00" and _horario("12h30") == "12:30" and _horario("18:30") == "18:30"
    with pytest.raises(ErroFacilita):
        _horario("meio-dia")


def test_coluna_desconhecida(tmp_path):
    arq = tmp_path / "p.csv"
    arq.write_text("Título;Preço do pacote\nx;1\n", encoding="utf-8")
    with pytest.raises(ErroFacilita, match="preco_pacote"):
        ler_planilha(arq)


def test_linha_vira_peca(tmp_path):
    arq = _planilha(tmp_path, ["Xcaret;oferta;feed, story;Hotel Xcaret Arte;Comente ARTE;foto.jpg;Canva Pro;GRU;sim;mão;"
                               "25.980,00;10;15/12/2026;10x sem juros;México;;"])
    linha = ler_planilha(arq)[0]
    dados = linha_para_peca(linha, tmp_path)
    assert dados["formatos"] == ["feed", "story"]
    assert dados["oferta"]["all_inclusive"] is True and dados["oferta"]["valor_total_casal"] == 25980
    assert dados["fotos"][0]["arquivo"] == str((tmp_path / "foto.jpg").resolve())
    assert dados["fotos"][0]["origem"] == "Canva Pro"


def test_agenda_respeita_fixos_e_preenche_horarios():
    def item(n, data=None, horario=None):
        return Item(n, f"p{n}", {"modelo": "oferta"}, "", data, horario)

    seg = dt.date(2026, 10, 12)
    itens = [item(2), item(3, seg, "09:00"), item(4), item(5, None, "18:30"), item(6), item(7)]
    avisos = agendar(itens, HORARIOS, seg)
    slots = {i.linha: (i.data, i.horario) for i in itens}
    ter = seg + dt.timedelta(days=1)
    assert slots[3] == (seg, "09:00")                    # fixo mantido
    assert slots[5] == (seg, "18:30")                    # horário pedido vem antes das peças livres
    assert slots[2] == (seg, "12:30") and slots[4] == (ter, "09:00")
    assert slots[6] == (ter, "12:30") and slots[7] == (ter, "18:30")
    assert len(set(slots.values())) == 6                  # nenhum horário repetido
    assert all(h in HORARIOS for _, h in slots.values())
    assert not avisos


def test_dia_cheio_vai_para_o_seguinte():
    seg = dt.date(2026, 10, 12)
    itens = [Item(n, f"p{n}", {}, "", seg) for n in range(2, 6)]
    avisos = agendar(itens, HORARIOS, seg)
    assert itens[-1].data == seg + dt.timedelta(days=1)
    assert any("cheio" in a for a in avisos)


def test_lote_recusa_linhas_ruins_e_segue(tmp_path, marca):
    arq = _planilha(tmp_path, [
        "Boa;oferta;feed;Hotel Xcaret Arte;Comente ARTE;foto.jpg;Canva Pro;GRU;sim;mão;25980;10;15/12/2026;10x;México;12/10/2026;09h",
        "Sem aeroporto;oferta;feed;Oferta;;foto.jpg;Canva Pro;;;;9990;5;15/12/2026;5x;;;",
        "Sem origem;hotel;feed;Suítes;;foto.jpg;;;;;;;;;;;",
        "Embaixador;hotel;feed;Fale com o embaixador;;foto.jpg;Canva Pro;;;;;;;;;;",
    ])
    r = processar(arq, marca, tmp_path / "saida", gerar_pngs=False, hoje=HOJE)
    assert [i.linha for i in r["itens"]] == [2]
    assert sorted(i.linha for i in r["itens_recusados"]) == [3, 4, 5]
    item = r["itens"][0]
    assert (item.data, item.horario) == (dt.date(2026, 10, 12), "09:00")
    assert "e-Visa" in item.legenda
    csv = (tmp_path / "saida" / "fila" / "pautas" / "agenda.csv").read_text(encoding="utf-8-sig")
    assert "12/10/2026;09:00;Boa;oferta" in csv
    ics = (tmp_path / "saida" / "fila" / "pautas" / "agenda.ics").read_text(encoding="utf-8")
    assert "DTSTART;TZID=America/Sao_Paulo:20261012T090000" in ics and "BEGIN:VTIMEZONE" in ics
    assert item.yaml.exists()  # peça editável sozinha depois


@precisa_chromium
def test_lote_gera_pngs(tmp_path, marca):
    arq = _planilha(tmp_path, [
        "A;oferta;feed, story;Hotel Xcaret Arte;Comente ARTE;foto.jpg;Canva Pro;GRU;sim;mão;25980;10;15/12/2026;10x;;;",
        "B;hotel;feed;Suítes;;foto.jpg;Canva Pro;;;;;;;;;;",
    ])
    r = processar(arq, marca, tmp_path / "saida", hoje=HOJE, permitir_fonte_substituta=True)
    tamanhos = [Image.open(p).size for it in r["itens"] for p in it.pngs]
    assert tamanhos == [(1080, 1350), (1080, 1920), (1080, 1350)]


def test_le_xlsx(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Peça", "Título", "Data de publicação", "Horário", "Valor total casal"])
    ws.append(["X", "Hotel", dt.datetime(2026, 10, 12), dt.time(12, 30), 25980.0])
    ws.append([None, None, None, None, None])
    wb.save(tmp_path / "p.xlsx")
    linhas = ler_planilha(tmp_path / "p.xlsx")
    assert linhas == [{"peca": "X", "titulo": "Hotel", "data_publicacao": "2026-10-12", "horario": "12:30",
                       "valor_total_casal": "25980"}]
