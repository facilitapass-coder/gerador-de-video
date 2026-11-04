"""Monta a sequência de Stories de uma semana. Uso (na raiz):
  .venv/bin/python remotion/scripts/montar_stories.py <plano.json> [opções] [id ...]
Opções:
  --so-preparar    só corta os trechos e gera legendas (não exporta)
  --so-renderizar  exporta sem refazer cortes nem trilha
  --so-musica      refaz a trilha e exporta apenas os Stories sem fala
  --so-fala        exporta apenas os Stories com fala que ainda não existem"""
import json, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]
ids = [a for a in sys.argv[2:] if not a.startswith("--")]
so_preparar, so_renderizar = "--so-preparar" in sys.argv, "--so-renderizar" in sys.argv
so_musica, so_fala = "--so-musica" in sys.argv, "--so-fala" in sys.argv
faltando = "--faltando" in sys.argv  # exporta só o que ainda não tem arquivo, sem refazer cortes
plano = json.loads(Path(sys.argv[1]).read_text())
tmp = RAIZ / "trabalho" / "story-cfg.json"
MUSICAS = RAIZ / "trabalho" / "musica"
BANCO = MUSICAS / "banco"   # faixas do Pixabay Music (Pixabay Content License: uso comercial, sem crédito obrigatório)
# Por ambiente: (faixa, segundo em que o trecho começa). As cantadas vêm primeiro.
TRECHOS = {
    "fiesta": [("el-contrario", 37), ("rumba-urbana", 61), ("salsa-caliente", 55), ("fuego-que-nunca", 79), ("cumbia-banda", 30), ("el-contrario", 77)],
    "mariachi": [("fiesta-guadalajara", 20), ("corridos-tumbados", 50), ("huapango-banda", 15), ("tampico-cumbia", 20), ("fiesta-guadalajara", 75)],
    "lounge": [("donde-tu-estas", 41), ("your-best-summer", 58), ("donde-tu-estas", 0), ("spanish-reggaeton", 30), ("donde-tu-estas", 101), ("latin-party-pop", 20)],
    "aventura": [("spanish-reggaeton", 60), ("rumba-urbana", 30), ("corridos-tumbados", 110), ("latin-party-pop", 45)],
    "tropical": [("tampico-cumbia", 45), ("your-best-summer", 20), ("el-contrario", 16), ("cumbia-banda", 60), ("latin-party-pop", 8), ("salsa-caliente", 15), ("huapango-banda", 45)],
}
REGRAS = [("aventura", ["xplor", "tunel", "toboagua", "atalho", "maquina-de-soco", "veiculos", "dentro-da-caverna", "parque-noturno"]),
          ("fiesta", ["bar", "noite", "mercado-do-hotel", "tochas", "jantar", "almoco", "carrinhos", "onibus", "chegada-ao-hotel", "danca", "sala-de-jogos"]),
          ("mariachi", ["abertura", "partiu", "chegamos", "cafe-no-mercado", "ate-a-proxima", "tem-novidade", "hora-de-voltar", "bom-dia", "caminho-do-cafe", "flamingos", "araras"]),
          ("lounge", ["nascer-do-sol", "suite-com-piscina", "rede-na-varanda", "fim-de-tarde", "vista-da-varanda"])]
usos = {}
ultima = [None]

def trilha_do(st):
    if st.get("trilha"): return st["trilha"]
    chave = (st["nome"] + " " + st["etiqueta"]).lower()
    for nome, palavras in REGRAS:
        if any(p in chave for p in palavras): return nome
    return "lounge" if "la casa de la playa" in chave else "tropical"

for dia in plano["dias"]:
    destino = RAIZ / "projetos" / "stories" / dia["pasta"]; destino.mkdir(parents=True, exist_ok=True)
    for st in dia["stories"]:
        if ids and st["id"] not in ids: continue
        pasta = RAIZ / "remotion" / "public" / st["id"]; saida = destino / f"{st['nome']}.mp4"
        if faltando and saida.exists(): continue
        if not (so_renderizar or so_musica or so_fala or faltando):
            cfg = {"id": st["id"], "story": True, "etiqueta": st["etiqueta"], "titulo": st["titulo"], "falas": st["falas"],
                   "troca": {**plano.get("troca", {}), **st.get("troca", {})}, "remove": st.get("remove", []),
                   "frases": {**plano.get("frases", {}), **st.get("frases", {})}}
            tmp.write_text(json.dumps(cfg, ensure_ascii=False))
            print(f"\n##### {st['id']} · {st['nome']}", flush=True)
            subprocess.run([str(RAIZ / ".venv/bin/python"), str(RAIZ / "remotion/scripts/preparar_fala.py"), str(tmp)], check=True)
        dados = json.loads((pasta / "dados.json").read_text())
        sem_fala = not dados["grupos"]
        if (so_musica and not sem_fala) or (so_fala and (sem_fala or saida.exists())): continue
        if sem_fala and not so_renderizar:
            # Story sem fala: trilha instrumental do ambiente, começando num compasso diferente a cada uso
            nome = trilha_do(st); k = usos.get(nome, 0); opcoes = TRECHOS[nome]
            faixa, inicio = opcoes[k % len(opcoes)]
            if st.get("faixa"): faixa, inicio = st["faixa"]   # faixa escolhida a dedo para este Story
            if faixa == ultima[0]: k += 1; faixa, inicio = opcoes[k % len(opcoes)]   # nunca a mesma faixa em dois Stories seguidos
            usos[nome] = k + 1; ultima[0] = faixa
            dur = dados["total"] / 30
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{inicio}", "-i", str(BANCO / f"{faixa}.mp3"), "-t", f"{dur:.3f}",
                            "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.25,afade=t=out:st={max(0, dur - 1.2):.3f}:d=1.2", "-ar", "48000", "-ac", "2", str(pasta / "voz.wav")], check=True)
            nome = f"{nome} · {faixa}"
            print(f"   {st['id']} trilha: {nome}", flush=True)
        if so_preparar: continue
        cmd = ["npx", "remotion", "render", "Story", str(saida), f"--props=public/{st['id']}/dados.json", "--codec=h264", "--crf=18", "--log=error"]
        for tentativa in (1, 2, 3):   # uma exportação que trava é interrompida em 8 min e refeita
            try:
                subprocess.run(cmd, cwd=RAIZ / "remotion", check=True, timeout=480)
                print("->", saida.relative_to(RAIZ), flush=True); break
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                subprocess.run(["pkill", "-f", f"--props=public/{st['id']}/dados.json"]); saida.unlink(missing_ok=True)
                print(f"   {st['id']} tentativa {tentativa} falhou: {type(e).__name__}", flush=True)
        else:
            print(f"FALHOU {st['id']}", flush=True)
