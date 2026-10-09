"""Linha de comando: `facilita <comando>`. Use `facilita --help` para a lista."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .marca import Marca, erros
from .util import ErroFacilita


def _imprimir_problemas(problemas) -> None:
    for p in problemas:
        print(f"  {p}")


def cmd_importar(a, marca: Marca) -> int:
    from .video.importacao import listar_midias, sondar, tabela

    infos = [sondar(p) for p in listar_midias(a.entradas)]
    print(tabela(infos))
    if a.json:
        Path(a.json).write_text(json.dumps([i.resumo() for i in infos], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nDados em {a.json}")
    return 0


def cmd_analisar(a, marca: Marca) -> int:
    from .video.analise import analisar
    from .video.importacao import listar_midias

    pasta = Path(a.saida) / "analise"
    resultados = analisar(listar_midias(a.entradas), pasta, marca, a.intervalo)
    for r in resultados:
        linha = f"{Path(r['arquivo']).name}: {r['duracao']:.1f}s"
        if "folha_de_contato" in r:
            linha += f" · {r['quadros']} quadros · folha: {r['folha_de_contato']}"
        if "volume" in r:
            linha += f" · volume médio {r['volume']['media_db']} dB (pico {r['volume']['pico_db']} dB)"
        print(linha)
    (pasta / "analise.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def _carregar_para_mapa(a, marca: Marca):
    from .video import roteiro as mod_roteiro
    from .video.analise import detectar_silencios
    from .video.cobertura import carregar_biblioteca
    from .video.importacao import sondar

    rot = mod_roteiro.ler(a.roteiro)
    biblioteca, problemas = carregar_biblioteca(a.clips, marca)
    narr = rot.arquivo("narracao")
    if not all(b.duracao for b in rot.blocos):
        dur = sondar(narr).duracao if narr and narr.exists() else None
        mod_roteiro.resolver_tempos(rot, dur, detectar_silencios(narr) if dur else [])
    return rot, biblioteca, problemas


def cmd_cobertura(a, marca: Marca) -> int:
    from .video.cobertura import mapear, relatorio_markdown, salvar_relatorio

    rot, biblioteca, problemas = _carregar_para_mapa(a, marca)
    _imprimir_problemas(problemas)
    escolhas = mapear(rot, biblioteca)
    print(relatorio_markdown(rot, escolhas))
    md, js = salvar_relatorio(rot, escolhas, Path(a.saida) / "reels" / rot.slug)
    print(f"Mapa salvo em {md} e {js}")
    return 1 if erros(problemas) else 0


def cmd_montar(a, marca: Marca) -> int:
    from .video.montagem import montar

    r = montar(a.roteiro, a.clips, marca, a.saida, previa=a.previa, manter_trabalho=a.manter_trabalho,
               permitir_fonte_substituta=a.permitir_fonte_substituta)
    print(f"Reels pronto: {r.mp4} ({r.duracao:.1f}s, {r.medidas.get('resolucao')})")
    if "voz_acima_da_musica_db" in r.medidas:
        print(f"Voz {r.medidas['voz_acima_da_musica_db']} dB acima da música.")
    print(f"Mapa de cobertura: {r.cobertura}\nManifesto: {r.manifesto}")
    for av in r.avisos:
        print(f"  [aviso] {av}")
    return 0


def cmd_ajustar(a, marca: Marca) -> int:
    from .video import ajustes as mod_ajustes

    roteiro = Path(a.roteiro)
    aj = {} if a.limpar else mod_ajustes.carregar(roteiro)
    for pedido in a.pedidos:
        print(f"- {pedido}: {mod_ajustes.interpretar(pedido, aj, marca.video)}")
    destino = mod_ajustes.salvar(roteiro, aj)
    print(f"Ajustes em {destino}. Rode 'facilita montar' para gerar a nova versão.")
    return 0


def cmd_legenda(a, marca: Marca) -> int:
    from .video import roteiro as mod_roteiro
    from .video.legenda import salvar_legenda

    destino, problemas = salvar_legenda(mod_roteiro.ler(a.roteiro), marca, Path(a.saida))
    print(destino.read_text(encoding="utf-8"))
    _imprimir_problemas(problemas)
    print(f"Legenda salva em {destino}")
    return 1 if erros(problemas) else 0


def cmd_imagem(a, marca: Marca) -> int:
    from .imagens.gerador import gerar

    r = gerar(a.peca, marca, a.saida, a.formato or None, a.permitir_fonte_substituta, a.manter_2x, variacoes=a.variacoes)
    for s in r["saidas"]:
        print(f"PNG: {s['png']}")
    for av in r["avisos"]:
        print(f"  {av}" if av.startswith("[") else f"  [aviso] {av}")
    print(f"Manifesto: {r['manifesto']}")
    return 0


def cmd_capa(a, marca: Marca) -> int:
    from .imagens.capa import gerar_capa

    r = gerar_capa(a.roteiro, a.clips, marca, a.saida, a.bloco, a.quadro, a.titulo, a.permitir_fonte_substituta)
    print(f"Capa: {r['png']} (bloco {r['bloco']}, {r['clip']} em {r['tempo']:.1f}s)")
    for av in r["avisos"]:
        print(f"  [aviso] {av}")
    return 0


def cmd_comparar(a, marca: Marca) -> int:
    from .versoes import comparar

    for linha in comparar(a.antes, a.depois):
        print(f"- {linha}")
    return 0


def cmd_validar(a, marca: Marca) -> int:
    alvo = Path(a.arquivo)
    if alvo.suffix.lower() in (".md", ".markdown"):
        from .video import roteiro as mod_roteiro
        from .video.montagem import verificar_textos

        problemas = verificar_textos(mod_roteiro.ler(alvo), marca)
    else:
        from .imagens.gerador import validar

        problemas, _ = validar(alvo, marca)
    if not problemas:
        print(f"{alvo.name}: tudo certo.")
    _imprimir_problemas(problemas)
    return 1 if erros(problemas) else 0


def cmd_logo(a, marca: Marca) -> int:
    from .imagens.fotos import corrigir_alfa_logo

    origem = Path(a.logo) if a.logo else marca.pasta / marca.dados["logo"]["arquivo"]
    destino = marca.pasta / "derivados" / (origem.stem + "-alfa.png")
    r = corrigir_alfa_logo(origem, destino, a.limiar)
    print(f"Logo corrigido: {r['destino']} ({r['pixels_removidos']} pixels quase pretos removidos). Original intocado.")
    return 0


def cmd_marca(a, marca: Marca) -> int:
    problemas = marca.verificar_ativos()
    print(f"Marca: {marca.dados['nome']} · pasta {marca.pasta}")
    print("Cores: " + ", ".join(f"{k} {v}" for k, v in marca.cores.items()))
    print(f"Fonte Poppins completa: {'sim' if marca.fonte_completa() else 'não'}")
    print(f"Logo: {marca.caminho_logo() or 'AUSENTE'}")
    _imprimir_problemas(problemas)
    return 1 if erros(problemas) else 0


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="facilita", description="Editor de Reels e gerador de imagens da Facilita Pass.")
    p.add_argument("--marca", help="pasta da marca (padrão: marca/)")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("importar", help="lê resolução, duração e orientação de clips e áudios")
    s.add_argument("entradas", nargs="+")
    s.add_argument("--json", help="grava os dados em JSON")
    s.set_defaults(func=cmd_importar)

    s = sub.add_parser("analisar", help="quadros a cada 2 s, folha de contato e volume da voz")
    s.add_argument("entradas", nargs="+")
    s.add_argument("--intervalo", type=float, default=2.0)
    s.add_argument("--saida", default="saida")
    s.set_defaults(func=cmd_analisar)

    for nome, func, ajuda in (("cobertura", cmd_cobertura, "mapa de cobertura: clip de cada bloco e o que falta gravar"),
                              ("montar", cmd_montar, "monta o Reels MP4 1080×1920")):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("roteiro")
        s.add_argument("--clips", required=True, help="biblioteca clips.yaml")
        s.add_argument("--saida", default="saida")
        if nome == "montar":
            s.add_argument("--previa", action="store_true", help="prévia rápida em 540×960")
            s.add_argument("--manter-trabalho", action="store_true", help="guarda os arquivos intermediários")
            s.add_argument("--permitir-fonte-substituta", action="store_true", help="monta mesmo sem a Poppins instalada")
        s.set_defaults(func=func)

    s = sub.add_parser("ajustar", help='pedidos como "tira o bloco 5" ou "voz mais alta" para a próxima montagem')
    s.add_argument("roteiro")
    s.add_argument("pedidos", nargs="*")
    s.add_argument("--limpar", action="store_true", help="descarta os ajustes anteriores")
    s.set_defaults(func=cmd_ajustar)

    s = sub.add_parser("legenda", help="legenda do post com CTA e lembrete da e-Visa")
    s.add_argument("roteiro")
    s.add_argument("--saida", default="saida")
    s.set_defaults(func=cmd_legenda)

    s = sub.add_parser("imagem", help="gera PNG de post, carrossel, story ou arte de WhatsApp")
    s.add_argument("peca", help="arquivo .yaml da peça")
    s.add_argument("--formato", action="append", choices=["feed", "story", "whatsapp"])
    s.add_argument("--saida", default="saida")
    s.add_argument("--permitir-fonte-substituta", action="store_true", help="gera mesmo sem a Poppins instalada")
    s.add_argument("--manter-2x", action="store_true", help="guarda o PNG em 2× em vez de reduzir")
    s.add_argument("--variacoes", type=int, default=1, help="gera 2 ou 3 opções de layout para escolha")
    s.set_defaults(func=cmd_imagem)

    s = sub.add_parser("capa", help="capa do Reels: quadro do vídeo com o título")
    s.add_argument("roteiro")
    s.add_argument("--clips", required=True)
    s.add_argument("--bloco", type=int, help="bloco de onde sai o quadro (padrão: o 1º com imagem)")
    s.add_argument("--quadro", help="tempo dentro do bloco, ex.: 0:02")
    s.add_argument("--titulo", help="título da capa (padrão: capa_titulo ou título do roteiro)")
    s.add_argument("--saida", default="saida")
    s.add_argument("--permitir-fonte-substituta", action="store_true")
    s.set_defaults(func=cmd_capa)

    s = sub.add_parser("comparar", help="diferenças entre duas versões (manifestos .json ou pastas vNN)")
    s.add_argument("antes")
    s.add_argument("depois")
    s.set_defaults(func=cmd_comparar)

    s = sub.add_parser("validar", help="confere marca, regras de oferta e fotos sem gerar nada")
    s.add_argument("arquivo", help="roteiro .md ou peça .yaml")
    s.set_defaults(func=cmd_validar)

    s = sub.add_parser("logo-corrigir", help="corrige o canal alfa do logo (remove pixels quase pretos)")
    s.add_argument("logo", nargs="?")
    s.add_argument("--limiar", type=int, default=40)
    s.set_defaults(func=cmd_logo)

    s = sub.add_parser("marca", help="confere fonte, logo e cores da marca")
    s.set_defaults(func=cmd_marca)
    return p


def main(argv: list[str] | None = None) -> int:
    a = construir_parser().parse_args(argv)
    try:
        marca = Marca.carregar(a.marca)
        return a.func(a, marca)
    except ErroFacilita as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
