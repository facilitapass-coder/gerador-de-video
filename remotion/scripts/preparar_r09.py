"""Prepara o Reels 09 (sala de hospitalidade): corta os trechos de fala e de apoio em H.264 30 fps,
monta a trilha de voz tratada e gera as legendas palavra a palavra.
Uso (na raiz do repositório): .venv/bin/python remotion/scripts/preparar_r09.py"""
import json, re, subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ORIG = RAIZ / "projetos" / "_do-app-fotos"
SAIDA = RAIZ / "remotion" / "public" / "r09"
FPS = 30
idx = {r["n"]: r for r in json.load(open(RAIZ / "trabalho" / "fotos-app-videos.json"))}
caminho = lambda n: ORIG / idx[n]["pasta"] / idx[n]["arquivo"]

# Trechos de fala, na ordem do vídeo: (nome, nº do clip, início, fim) em segundos do clip original
FALAS = [("a", 190, 9.64, 13.74), ("b", 190, 15.20, 21.63), ("c", 190, 21.65, 28.40), ("d", 344, 2.30, 9.42),
         ("e1", 191, 21.94, 25.28), ("e2", 191, 26.84, 28.02), ("e3", 191, 34.74, 37.92)]
# Imagens de apoio: (nome, nº do clip, início, duração)
APOIO = [("piscina", 74, 0.5, 3.4), ("buffet", 347, 2.0, 3.4), ("caminho", 88, 0.3, 4.6), ("fundo", 73, 1.0, 3.0)]
CORRIGE = {"bobo": "voo", "continue": "continua", "ou": "", "fluido": "", "usar": "usufruir", "as": "às", "o": "o"}

def ff(*a): subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a], check=True)
VF = f"fps={FPS},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p"

def palavras(n):
    wav = SAIDA / "tmp.wav"
    ff("-i", str(caminho(n)), "-vn", "-ar", "16000", "-ac", "1", str(wav))
    out = subprocess.run(["whisper-cli", "-m", str(RAIZ / "trabalho/modelos/ggml-small.bin"), "-l", "pt", "-ml", "1", "-sow", "-np", str(wav)],
                         capture_output=True, text=True).stdout
    wav.unlink()
    r = []
    for m in re.finditer(r"\[00:(\d\d):([\d.]+) --> 00:(\d\d):([\d.]+)\]\s+(\S.*)", out):
        r.append((int(m.group(1)) * 60 + float(m.group(2)), m.group(5).strip()))
    return r

SAIDA.mkdir(parents=True, exist_ok=True)
linha, legendas, quadro, cache, partes_audio = [], [], 0, {}, []
for nome, n, a, b in FALAS:
    q = round((b - a) * FPS); dur = q / FPS
    ff("-ss", f"{a}", "-i", str(caminho(n)), "-t", f"{dur}", "-an", "-vf", VF, "-frames:v", str(q), "-c:v", "libx264", "-preset", "fast", "-crf", "16", str(SAIDA / f"fala_{nome}.mp4"))
    ff("-ss", f"{a}", "-i", str(caminho(n)), "-t", f"{dur}", "-vn", "-ar", "48000", "-ac", "2",
       "-af", f"afade=t=in:d=0.012,afade=t=out:st={dur - 0.012:.3f}:d=0.012", str(SAIDA / f"voz_{nome}.wav"))
    partes_audio.append(SAIDA / f"voz_{nome}.wav")
    if n not in cache: cache[n] = palavras(n)
    for t, p in cache[n]:
        if a - 0.03 <= t < b - 0.05:
            limpa = p.strip()
            chave = limpa.lower().strip(",.?!")
            if chave == "fluido" or chave == "ou": continue
            if nome == "e3" and chave == "o" and t < 36: continue  # "usar o fluido da" -> "usufruir da"
            if chave == "dia" and legendas and legendas[-1]["texto"] == "meio":
                legendas[-1]["texto"] = "meio-dia" + ("," if limpa.endswith(",") else ""); continue
            if chave in ("bobo", "continue", "usar"): limpa = CORRIGE[chave] + ("," if limpa.endswith(",") else "")
            if nome == "d" and chave == "aqui" and legendas and legendas[-1]["texto"].startswith("desfrutando"): limpa = "de"
            if nome.startswith("e") and chave == "as": limpa = "às"
            legendas.append({"quadro": quadro + max(0, round((t - a) * FPS)), "texto": limpa})
    linha.append({"nome": nome, "quadros": q, "inicio": quadro}); quadro += q
for nome, n, a, d in APOIO:
    ff("-ss", f"{a}", "-i", str(caminho(n)), "-t", f"{d}", "-an", "-vf", VF, "-c:v", "libx264", "-preset", "fast", "-crf", "16", str(SAIDA / f"apoio_{nome}.mp4"))
lista = SAIDA / "voz.txt"; lista.write_text("".join(f"file '{p.name}'\n" for p in partes_audio))
ff("-f", "concat", "-safe", "0", "-i", str(lista), "-af",
   "highpass=f=90,afftdn=nr=12,acompressor=threshold=-21dB:ratio=3.5:attack=6:release=120:makeup=4,loudnorm=I=-15:TP=-1.5:LRA=7",
   "-ar", "48000", str(SAIDA / "voz.wav"))
for p in partes_audio: p.unlink()
lista.unlink()
# Agrupa as legendas em blocos curtos (até 3 palavras ou 18 letras; quebra em vírgula e na troca de trecho)
grupos, atual = [], []
cortes = {l["inicio"] for l in linha}
for w in legendas:
    troca = atual and any(atual[-1]["quadro"] < c <= w["quadro"] for c in cortes)
    if atual and (troca or len(atual) >= 3 or sum(len(x["texto"]) for x in atual) + len(w["texto"]) > 18 or atual[-1]["texto"].endswith((",", "."))):
        grupos.append(atual); atual = []
    atual.append(w)
if atual: grupos.append(atual)
for g in grupos:
    for w in g: w["texto"] = w["texto"].rstrip(",.")
dados = {"total": quadro, "linha": linha, "grupos": grupos}
(RAIZ / "remotion" / "src" / "r09-dados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))
print("quadros de fala:", quadro, f"({quadro / FPS:.1f}s)")
for g in grupos: print(g[0]["quadro"], " ".join(w["texto"] for w in g))
