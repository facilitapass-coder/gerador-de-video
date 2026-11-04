"""Prepara um Reels de fala real: corta trechos de fala e de apoio em H.264 30 fps, monta a voz tratada
e gera legendas palavra a palavra. Uso (na raiz): .venv/bin/python remotion/scripts/preparar_fala.py remotion/scripts/r03.json

Config: {"id": "r03", "falas": [[nome, origem, inicio, fim]], "apoio": [[nome, origem, inicio, duracao]],
         "troca": {"palavra errada": "certa"}, "remove": ["palavra"]}
`origem` é o nº do vídeo no indice.csv ou um caminho relativo a projetos/_do-app-fotos."""
import json, re, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ORIG = RAIZ / "projetos" / "_do-app-fotos"
cfg = json.loads(Path(sys.argv[1]).read_text())
SAIDA = RAIZ / "remotion" / "public" / cfg["id"]
FPS = 30
idx = {r["n"]: r for r in json.load(open(RAIZ / "trabalho" / "fotos-app-videos.json"))}
caminho = lambda o: ORIG / idx[o]["pasta"] / idx[o]["arquivo"] if isinstance(o, int) else ORIG / o
VF = f"fps={FPS},scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,format=yuv420p"

def ff(*a): subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a], check=True)

def palavras(o):
    wav = SAIDA / "tmp.wav"
    ff("-i", str(caminho(o)), "-vn", "-ar", "16000", "-ac", "1", str(wav))
    out = subprocess.run(["whisper-cli", "-m", str(RAIZ / "trabalho/modelos/ggml-small.bin"), "-l", "pt", "-ml", "1", "-sow", "-np", str(wav)],
                         capture_output=True, text=True).stdout
    wav.unlink()
    return [(int(m.group(1)) * 60 + float(m.group(2)), m.group(3).strip())
            for m in re.finditer(r"\[00:(\d\d):([\d.]+) --> [\d:.]+\][ \t]+(\S[^\n]*)", out)]

SAIDA.mkdir(parents=True, exist_ok=True)
troca = {k.lower(): v for k, v in cfg.get("troca", {}).items()}
remove = {k.lower() for k in cfg.get("remove", [])}
linha, legendas, quadro, cache, vozes = [], [], 0, {}, []
def silencios(o):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(caminho(o)), "-vn", "-af", "silencedetect=noise=-32dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]; fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(ini, fim + [9e9] * (len(ini) - len(fim))))
def encaixa(o, a, b):
    """Ajusta o trecho para não cortar palavra nem pegar palavra vizinha:
    o fim vai até o silêncio seguinte, mas para antes da próxima palavra; o início recua um pouco, sem invadir a anterior."""
    chave = str(o)
    if chave not in cache: cache[chave] = palavras(o)
    ws = [t for t, _ in cache[chave]]
    sil = silencios(o)
    prox = [t for t in ws if t >= b - 0.05]; ant = [t for t in ws if t < a - 0.05]
    limite_fim = (prox[0] - 0.04) if prox else 9e9
    dep = [i for i, f in sil if i >= b - 0.35 and i - b <= 1.0]
    fim = (min(dep) + 0.15) if dep else b + 0.2
    fim = min(fim, limite_fim) if limite_fim > b - 0.3 else fim
    limite_ini = (ant[-1] + 0.3) if ant else 0.0
    antes = [f for i, f in sil if f <= a + 0.05 and a - f <= 0.5]
    ini = (max(antes) - 0.05) if antes else a - 0.1
    ini = max(ini, min(limite_ini, a - 0.08), 0.0) if ini < a else a
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(caminho(o))], capture_output=True, text=True).stdout)
    return round(ini, 2), round(min(max(fim, ini + 0.5), dur - 0.05), 2)
for nome, o, a, b, *resto in cfg["falas"]:
    mudo = bool(resto and resto[0])
    if not mudo: a, b = encaixa(o, a, b)
    q = round((b - a) * FPS); dur = q / FPS
    ff("-ss", f"{a}", "-i", str(caminho(o)), "-t", f"{dur}", "-an", "-vf", VF, "-frames:v", str(q), "-c:v", "libx264", "-preset", "fast", "-crf", "16", str(SAIDA / f"fala_{nome}.mp4"))
    tem_audio = "audio" in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(caminho(o))],
                                          capture_output=True, text=True).stdout
    if mudo and not tem_audio:
        ff("-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=stereo", str(SAIDA / f"voz_{nome}.wav"))
    elif mudo:
        # Trecho sem fala: mantém o som ambiente do lugar, mais baixo que a voz
        ff("-ss", f"{a}", "-i", str(caminho(o)), "-t", f"{dur}", "-vn", "-ar", "48000", "-ac", "2",
           "-af", f"volume=0.35,afade=t=in:d=0.25,afade=t=out:st={max(0, dur - 0.3):.3f}:d=0.3", str(SAIDA / f"voz_{nome}.wav"))
    else:
        ff("-ss", f"{a}", "-i", str(caminho(o)), "-t", f"{dur}", "-vn", "-ar", "48000", "-ac", "2",
           "-af", f"afade=t=in:d=0.012,afade=t=out:st={dur - 0.012:.3f}:d=0.012", str(SAIDA / f"voz_{nome}.wav"))
    vozes.append(SAIDA / f"voz_{nome}.wav")
    chave_o = str(o)
    if not mudo and chave_o not in cache: cache[chave_o] = palavras(o)
    for t, p in ([] if mudo else cache[chave_o]):
        if a - 0.03 <= t < b - 0.05:
            base = p.lower().strip(",.?!"); pont = "," if p.endswith(",") else "." if p.endswith((".", "!", "?")) else ""
            if base in remove or not base or base.startswith(("[", "(")): continue
            texto = (troca[base] + pont) if base in troca else p
            legendas.append({"quadro": quadro + max(0, round((t - a) * FPS)), "texto": texto})
    linha.append({"nome": nome, "quadros": q, "inicio": quadro, "mudo": mudo}); quadro += q
# Frases que a transcrição erra em mais de uma palavra: {"tobo a água": "toboágua"}
limpo = lambda x: x.lower().strip(",.?!")
for errada, certa in cfg.get("frases", {}).items():
    alvo = errada.lower().split(); i = 0
    while i <= len(legendas) - len(alvo):
        if [limpo(w["texto"]) for w in legendas[i:i + len(alvo)]] == alvo:
            fim = legendas[i + len(alvo) - 1]["texto"]
            pont = "," if fim.endswith(",") else "." if fim.endswith((".", "!", "?")) else ""
            legendas[i:i + len(alvo)] = [{"quadro": legendas[i]["quadro"], "texto": certa + pont}]
        i += 1
for nome, o, a, d in cfg.get("apoio", []):
    ff("-ss", f"{a}", "-i", str(caminho(o)), "-t", f"{d}", "-an", "-vf", VF, "-c:v", "libx264", "-preset", "fast", "-crf", "16", str(SAIDA / f"apoio_{nome}.mp4"))
lista = SAIDA / "voz.txt"; lista.write_text("".join(f"file '{p.name}'\n" for p in vozes))
so_ambiente = all(l["mudo"] for l in linha)
filtro = ("highpass=f=70,loudnorm=I=-23:TP=-2:LRA=11" if so_ambiente else
          "highpass=f=90,afftdn=nr=12,acompressor=threshold=-21dB:ratio=3.5:attack=6:release=120:makeup=4,loudnorm=I=-15:TP=-1.5:LRA=7")
ff("-f", "concat", "-safe", "0", "-i", str(lista), "-af", filtro, "-ar", "48000", str(SAIDA / "voz.wav"))
for p in vozes: p.unlink()
lista.unlink()
grupos, atual = [], []
cortes = {l["inicio"] for l in linha}
for w in legendas:
    virou = atual and any(atual[-1]["quadro"] < c <= w["quadro"] for c in cortes)
    if atual and (virou or len(atual) >= 3 or sum(len(x["texto"]) for x in atual) + len(w["texto"]) > 18 or atual[-1]["texto"].endswith((",", "."))):
        grupos.append(atual); atual = []
    atual.append(w)
if atual: grupos.append(atual)
for g in grupos:
    for w in g: w["texto"] = w["texto"].rstrip(",.")
dados = {"total": quadro, "linha": linha, "grupos": grupos}
if cfg.get("reel"):
    dados.update({"id": cfg["id"], **cfg["reel"]})
    (SAIDA / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))
elif cfg.get("story"):
    dados.update({"id": cfg["id"], "etiqueta": cfg.get("etiqueta", ""), "titulo": cfg.get("titulo", "")})
    (SAIDA / "dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))
else:
    (RAIZ / "remotion" / "src" / f"{cfg['id']}-dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))
print("quadros de fala:", quadro, f"({quadro / FPS:.1f}s)", [(l["nome"], l["quadros"]) for l in linha])
for g in grupos: print(g[0]["quadro"], " ".join(w["texto"] for w in g))
