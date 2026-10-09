"""Fila e agenda: gera um lote de peças a partir de uma planilha de pautas e monta a agenda de publicação.

Cada linha da planilha (CSV ou XLSX) vira um arquivo de peça (.yaml) em
`saida/fila/<planilha>/pecas/`, que pode ser editado e refeito sozinho depois com
`facilita imagem`. Linhas com problema não são geradas e aparecem no relatório; as
demais seguem. A agenda distribui as peças nos horários da casa (marca.yaml > agenda)
e sai em CSV (abre no Excel), Markdown e .ics (calendário).

Colunas reconhecidas (maiúsculas, acentos e espaços não importam):

    peca, modelo, formatos, variacoes, etiqueta, titulo, subtitulo, cta, texto,
    foto, foto_origem, destaques (itens separados por "|", fonte depois de "::"),
    aeroporto_saida, all_inclusive, bagagem, noites, valor_total_casal, valor_por_pessoa,
    parcelas, validade, pagamento, datas, condicoes, selo, aviso_evisa, destino,
    data_publicacao, horario, legenda, arquivo_peca (usa um .yaml pronto, ex.: carrossel)
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .imagens import gerador
from .imagens.render import navegador
from .marca import Marca, Problema, erros
from .util import ErroFacilita, salvar_manifesto, sem_acentos, slug
from .video.legenda import DESTINOS_MEXICO

CAMPOS_TEXTO = ("etiqueta", "titulo", "subtitulo", "cta", "texto")
CAMPOS_OFERTA = ("aeroporto_saida", "all_inclusive", "bagagem", "noites", "valor_total_casal", "valor_por_pessoa",
                 "parcelas", "validade", "pagamento", "datas", "condicoes")
CAMPOS_CONHECIDOS = set(CAMPOS_TEXTO + CAMPOS_OFERTA) | {
    "peca", "modelo", "formatos", "variacoes", "foto", "foto_origem", "destaques", "selo", "aviso_evisa", "destino",
    "data_publicacao", "horario", "legenda", "arquivo_peca",
}


# ---------------------------------------------------------------- leitura
def _coluna(nome: str) -> str:
    """'Data de publicação' -> data_publicacao; 'Aeroporto de saída' -> aeroporto_saida."""
    partes = re.split(r"[^a-z0-9]+", sem_acentos(str(nome or "")).lower())
    return "_".join(p for p in partes if p and p not in ("de", "do", "da", "dos", "das"))


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if isinstance(valor, dt.datetime):
        valor = valor.date()
    if isinstance(valor, dt.time):
        return valor.strftime("%H:%M")
    return str(valor).strip()


def ler_planilha(caminho: Path | str) -> list[dict]:
    """Linhas como dicionários {coluna_normalizada: texto}; linhas vazias são ignoradas."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroFacilita(f"Planilha não encontrada: {caminho}")
    if caminho.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError as e:  # pragma: no cover
            raise ErroFacilita("Para ler .xlsx instale o openpyxl (pip install openpyxl) ou salve como CSV.") from e
        planilha = openpyxl.load_workbook(caminho, read_only=True, data_only=True).worksheets[0]
        linhas = [[_texto(c) for c in linha] for linha in planilha.iter_rows(values_only=True)]
    elif caminho.suffix.lower() in (".csv", ".txt"):
        conteudo = caminho.read_text(encoding="utf-8-sig")
        try:
            dialeto = csv.Sniffer().sniff(conteudo.splitlines()[0], delimiters=";,\t")
        except csv.Error:
            dialeto = csv.excel
        linhas = [[c.strip() for c in linha] for linha in csv.reader(conteudo.splitlines(), dialeto)]
    else:
        raise ErroFacilita("Planilha precisa ser .csv ou .xlsx.")
    if not linhas:
        raise ErroFacilita(f"{caminho.name} está vazia.")
    cabecalho = [_coluna(c) for c in linhas[0]]
    desconhecidas = [c for c in cabecalho if c and c not in CAMPOS_CONHECIDOS]
    if desconhecidas:
        raise ErroFacilita(f"Colunas não reconhecidas em {caminho.name}: {', '.join(desconhecidas)}.")
    saida = []
    for linha in linhas[1:]:
        item = {c: v for c, v in zip(cabecalho, linha) if c and v not in ("", None)}
        if item:
            saida.append(item)
    return saida


def _sim(valor) -> bool:
    return sem_acentos(str(valor or "")).lower().strip() in {"sim", "s", "x", "true", "1", "yes"}


def _numero(valor: str):
    texto = str(valor).replace("R$", "").strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", texto):  # 25.980,00
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")
    n = float(texto)
    return int(n) if n.is_integer() else n


def _data(valor: str) -> dt.date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(valor.strip()[:10], fmt).date()
        except ValueError:
            pass
    raise ErroFacilita(f"data '{valor}' não entendida (use DD/MM/AAAA).")


def _horario(valor: str) -> str:
    m = re.fullmatch(r"(\d{1,2})\s*(?:h|:)\s*(\d{2})?\s*(?:h|min)?", sem_acentos(valor).lower().strip())
    if not m:
        raise ErroFacilita(f"horário '{valor}' não entendido (use 09h, 12h30 ou 18:30).")
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if h > 23 or mi > 59:
        raise ErroFacilita(f"horário '{valor}' inválido.")
    return f"{h:02d}:{mi:02d}"


# ---------------------------------------------------------------- linha -> peça
def linha_para_peca(linha: dict, base: Path) -> dict:
    """Monta o conteúdo de um arquivo de peça a partir de uma linha da planilha."""
    if linha.get("arquivo_peca"):
        arq = Path(linha["arquivo_peca"])
        arq = arq if arq.is_absolute() else base / arq
        if not arq.exists():
            raise ErroFacilita(f"arquivo_peca não encontrado: {arq}")
        dados = yaml.safe_load(arq.read_text(encoding="utf-8")) or {}
        _absolutizar_fotos(dados, arq.parent)
        return dados
    oferta: dict = {}
    for chave in CAMPOS_OFERTA:
        if chave not in linha:
            continue
        valor = linha[chave]
        if chave == "all_inclusive":
            oferta[chave] = _sim(valor)
        elif chave in ("noites", "valor_total_casal", "valor_por_pessoa", "parcelas"):
            try:
                oferta[chave] = _numero(valor)
            except ValueError as e:
                raise ErroFacilita(f"{chave} '{valor}' não é número.") from e
        else:
            oferta[chave] = valor
    modelo = sem_acentos(linha.get("modelo", "")).lower() or ("oferta" if oferta else "hotel")
    if modelo == "carrossel":
        raise ErroFacilita("carrossel precisa de várias telas: aponte um .yaml pronto na coluna arquivo_peca.")
    dados: dict = {"peca": linha.get("peca") or linha.get("titulo") or "peca", "modelo": modelo,
                   "campos": {c: linha[c] for c in CAMPOS_TEXTO if c in linha}}
    if linha.get("formatos"):
        dados["formatos"] = [f.strip().lower() for f in re.split(r"[;,/+ ]+", linha["formatos"]) if f.strip()]
    if linha.get("foto"):
        foto = Path(linha["foto"])
        dados["fotos"] = [{"arquivo": str(foto if foto.is_absolute() else (base / foto).resolve()),
                           "origem": linha.get("foto_origem", "")}]
    if linha.get("destaques"):
        itens = []
        for item in linha["destaques"].split("|"):
            texto, _, fonte = item.partition("::")
            if texto.strip():
                itens.append({"texto": texto.strip(), "fonte": fonte.strip()})
        dados["destaques"] = itens
    if oferta:
        dados["oferta"] = oferta
    for chave in ("selo", "aviso_evisa"):
        if chave in linha:
            dados[chave] = _sim(linha[chave])
    if linha.get("variacoes"):
        dados["variacoes"] = int(_numero(linha["variacoes"]))
    return dados


def _absolutizar_fotos(dados: dict, base: Path) -> None:
    for lista in [dados.get("fotos")] + [t.get("fotos") for t in dados.get("telas") or []]:
        for f in lista or []:
            if isinstance(f, dict) and f.get("arquivo") and not Path(f["arquivo"]).is_absolute():
                f["arquivo"] = str((base / f["arquivo"]).resolve())


def montar_legenda(linha: dict, dados: dict, marca: Marca) -> str:
    campos = dados.get("campos") or {}
    partes = [linha.get("legenda") or " · ".join(x for x in (campos.get("titulo"), campos.get("subtitulo")) if x)]
    if campos.get("cta"):
        partes.append(campos["cta"])
    destino = sem_acentos(" ".join([linha.get("destino", ""), str(campos.get("titulo", ""))])).lower()
    if dados.get("aviso_evisa") or any(d in destino for d in DESTINOS_MEXICO):
        partes.append(marca.dados["avisos"]["evisa_mexico"].strip())
    return "\n\n".join(p for p in partes if p)


# ---------------------------------------------------------------- agenda
@dataclass
class Item:
    linha: int
    nome: str
    dados: dict
    legenda: str
    data: dt.date | None = None
    horario: str | None = None
    yaml: Path | None = None
    pngs: list[str] = field(default_factory=list)
    problemas: list[Problema] = field(default_factory=list)


def agendar(itens: list[Item], horarios: list[str], inicio: dt.date) -> list[str]:
    """Preenche data e horário; peças com data e horário fixos mantêm o que foi pedido."""
    avisos: list[str] = []
    ocupados: set[tuple[dt.date, str]] = set()
    # 1º: data e horário fixos
    for it in itens:
        if it.data and it.horario:
            if (it.data, it.horario) in ocupados:
                avisos.append(f"linha {it.linha}: {it.data:%d/%m} às {it.horario} já tem outra peça.")
            if it.horario not in horarios:
                avisos.append(f"linha {it.linha}: {it.horario} fora dos horários da casa ({', '.join(horarios)}).")
            ocupados.add((it.data, it.horario))

    def proximo(dia: dt.date) -> tuple[dt.date, str]:
        while True:
            for h in horarios:
                if (dia, h) not in ocupados:
                    return dia, h
            dia += dt.timedelta(days=1)

    # 2º: só horário pedido -> primeiro dia livre naquele horário (antes das peças livres)
    for it in itens:
        if it.horario and not it.data:
            dia = inicio
            while (dia, it.horario) in ocupados:
                dia += dt.timedelta(days=1)
            it.data = dia
            ocupados.add((dia, it.horario))
            if it.horario not in horarios:
                avisos.append(f"linha {it.linha}: {it.horario} fora dos horários da casa ({', '.join(horarios)}).")
    # 3º: o resto, na ordem da planilha, no próximo horário livre (a partir da data pedida, se houver)
    for it in itens:
        if it.data and it.horario:
            continue
        pedido = it.data
        it.data, it.horario = proximo(it.data or inicio)
        if pedido and it.data != pedido:
            avisos.append(f"linha {it.linha}: {pedido:%d/%m} já estava cheio; foi para {it.data:%d/%m} às {it.horario}.")
        ocupados.add((it.data, it.horario))
    itens.sort(key=lambda x: (x.data, x.horario, x.linha))
    return avisos


def _ics_texto(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ics_dobrar(linha: str) -> str:
    """Quebra linhas acima de 75 octetos, como pede o padrão iCalendar."""
    dados, partes, atual = linha.encode("utf-8"), [], b""
    for ch in linha:
        b = ch.encode("utf-8")
        if len(atual) + len(b) > (75 if not partes else 74):
            partes.append(atual.decode("utf-8"))
            atual = b""
        atual += b
    partes.append(atual.decode("utf-8"))
    return "\r\n ".join(partes) if len(dados) > 75 else linha


def salvar_agenda(itens: list[Item], pasta: Path, fuso: str) -> dict[str, Path]:
    csv_p, md_p, ics_p = pasta / "agenda.csv", pasta / "agenda.md", pasta / "agenda.ics"
    with open(csv_p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["data", "horario", "peca", "modelo", "arquivos", "legenda"])
        for it in itens:
            w.writerow([f"{it.data:%d/%m/%Y}", it.horario, it.nome, it.dados.get("modelo"),
                        " | ".join(Path(p).name for p in it.pngs), it.legenda])
    linhas = ["# Agenda de publicação", "", "| Data | Horário | Peça | Modelo | Arquivos |", "| --- | --- | --- | --- | --- |"]
    for it in itens:
        linhas.append(f"| {it.data:%d/%m/%Y} ({_DIAS[it.data.weekday()]}) | {it.horario} | {it.nome} | "
                      f"{it.dados.get('modelo')} | {', '.join(Path(p).name for p in it.pngs) or '—'} |")
    md_p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    ev = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Facilita Pass//Facilita Studio//PT", "CALSCALE:GREGORIAN"]
    if fuso == "America/Sao_Paulo":  # sem horário de verão desde 2019: UTC−3 o ano todo
        ev += ["BEGIN:VTIMEZONE", f"TZID:{fuso}", "BEGIN:STANDARD", "DTSTART:19700101T000000",
               "TZOFFSETFROM:-0300", "TZOFFSETTO:-0300", "TZNAME:-03", "END:STANDARD", "END:VTIMEZONE"]
    for it in itens:
        inicio = dt.datetime.combine(it.data, dt.time.fromisoformat(it.horario))
        uid = hashlib.sha256(f"{it.nome}|{inicio.isoformat()}".encode()).hexdigest()[:24]
        descricao = it.legenda + ("\n\nArquivos: " + ", ".join(Path(p).name for p in it.pngs) if it.pngs else "")
        ev += ["BEGIN:VEVENT", f"UID:{uid}@facilita-studio", "DTSTAMP:20260101T000000Z",
               f"DTSTART;TZID={fuso}:{inicio:%Y%m%dT%H%M%S}", "DURATION:PT15M",
               _ics_dobrar(f"SUMMARY:{_ics_texto('Publicar: ' + it.nome)}"),
               _ics_dobrar(f"DESCRIPTION:{_ics_texto(descricao)}"), "END:VEVENT"]
    ev.append("END:VCALENDAR")
    ics_p.write_text("\r\n".join(ev) + "\r\n", encoding="utf-8")
    return {"csv": csv_p, "md": md_p, "ics": ics_p}


_DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


# ---------------------------------------------------------------- execução
def processar(planilha: Path | str, marca: Marca, pasta_saida: Path | str = "saida", gerar_pngs: bool = True,
              inicio: dt.date | None = None, permitir_fonte_substituta: bool = False,
              hoje: dt.date | None = None) -> dict:
    planilha = Path(planilha)
    hoje = hoje or dt.date.today()
    inicio = inicio or hoje + dt.timedelta(days=1)
    pasta = Path(pasta_saida) / "fila" / slug(planilha.stem)
    pasta_pecas = pasta / "pecas"
    pasta_pecas.mkdir(parents=True, exist_ok=True)

    itens: list[Item] = []
    recusadas: list[Item] = []
    for n, linha in enumerate(ler_planilha(planilha), start=2):  # linha 1 é o cabeçalho
        try:
            dados = linha_para_peca(linha, planilha.parent)
            nome = str(dados.get("peca") or f"linha {n}")
            it = Item(n, nome, dados, montar_legenda(linha, dados, marca))
            if linha.get("data_publicacao"):
                it.data = _data(linha["data_publicacao"])
                if it.data < hoje:
                    it.problemas.append(Problema("erro", f"data de publicação {it.data:%d/%m/%Y} já passou.", f"linha {n}"))
            if linha.get("horario"):
                it.horario = _horario(linha["horario"])
        except ErroFacilita as e:
            recusadas.append(Item(n, linha.get("peca") or linha.get("titulo") or f"linha {n}", {}, "",
                                  problemas=[Problema("erro", str(e), f"linha {n}")]))
            continue
        it.yaml = pasta_pecas / f"{n:03d}-{slug(nome)}.yaml"
        it.yaml.write_text(yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8")
        problemas, _ = gerador.validar(it.yaml, marca, hoje)
        problemas += marca.verificar_texto(it.legenda, "legenda")
        it.problemas += [Problema(p.nivel, p.mensagem, f"linha {n} · {p.onde}") for p in problemas]
        (recusadas if erros(it.problemas) else itens).append(it)

    avisos = agendar(itens, list(marca.dados.get("agenda", {}).get("horarios", ["09:00", "12:30", "18:30"])), inicio)

    if gerar_pngs and itens:
        problemas_marca = marca.verificar_ativos(permitir_fonte_substituta)
        if erros(problemas_marca):
            raise ErroFacilita("Lote recusado:\n" + "\n".join(f"  {p}" for p in erros(problemas_marca)))
        with navegador() as browser:
            for it in itens:
                variacoes = int(it.dados.get("variacoes") or 1)
                r = gerador.gerar(it.yaml, marca, pasta, permitir_fonte_substituta=permitir_fonte_substituta,
                                  hoje=hoje, variacoes=variacoes, browser=browser)
                it.pngs = [s["png"] for s in r["saidas"]]

    arquivos = salvar_agenda(itens, pasta, marca.dados.get("agenda", {}).get("fuso", "America/Sao_Paulo"))
    relatorio = {
        "planilha": str(planilha),
        "geradas": [{"linha": i.linha, "peca": i.nome, "data": str(i.data), "horario": i.horario, "pngs": i.pngs,
                     "avisos": [str(p) for p in i.problemas]} for i in itens],
        "recusadas": [{"linha": i.linha, "peca": i.nome, "problemas": [str(p) for p in erros(i.problemas)]} for i in recusadas],
        "avisos_agenda": avisos,
        "agenda": {k: str(v) for k, v in arquivos.items()},
    }
    salvar_manifesto(pasta / "relatorio.json", relatorio)
    return {**relatorio, "pasta": str(pasta), "itens": itens, "itens_recusados": recusadas}
