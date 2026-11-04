"""Anúncio 02 · variação "seu filho vai pedir pra morar nesse hotel" (Reels para ADS). Corta os planos em H.264 30 fps.
Uso (na raiz): .venv/bin/python remotion/scripts/preparar_ad02.py"""
import json, subprocess
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; ORIG = RAIZ / "projetos" / "_do-app-fotos"; SAIDA = RAIZ / "remotion" / "public" / "ad02"
idx = {r["n"]: r for r in json.load(open(RAIZ / "trabalho" / "fotos-app-videos.json"))}
OF = RAIZ / "projetos/all-fun-inclusive/clips/All-Fun Inclusive_"
def origem(o):
    if isinstance(o, int): return ORIG / idx[o]["pasta"] / idx[o]["arquivo"]
    return Path(str(OF) + o) if o.endswith(".mp4") and "/" not in o else ORIG / o
# (origem, início no clip, quadros, texto)
PLANOS = [
 (442, 2.0, 96, ""),                                         # gancho: casinhas das crianças
 (409, 1.0, 45, "Cinema com piscina de bolinhas"),
 (413, 3.0, 45, "Toboágua saindo do terraço"),
 (456, 3.2, 45, "Clube só para adolescentes"),
 ("reels/DJI_0659.MP4", 3.0, 84, ""),                        # revela o hotel: 4 noites
 (357, 1.0, 42, "Rio dentro do hotel"),
 ("Xel-Há7.mp4", 2.0, 42, "Parques Xcaret inclusos"),
 (509, 3.2, 42, "Alimentação inclusa"),
 ("reels/DJI_0646.MP4", 5.0, 330, ""),                       # fundo da oferta + CTA
]
VF = "fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=12"
linha = []
for i, (o, a, q, t) in enumerate(PLANOS):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a}", "-i", str(origem(o)), "-an", "-vf", VF, "-frames:v", str(q),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "16", str(SAIDA / f"p{i:02d}.mp4")], check=True)
    linha.append({"arquivo": f"p{i:02d}.mp4", "quadros": q, "texto": t})
total = sum(l["quadros"] for l in linha)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "20", "-i", str(RAIZ / "trabalho/musica/banco/fiesta-guadalajara.mp3"), "-t", f"{total / 30}",
                "-af", f"loudnorm=I=-15:TP=-1.5,afade=t=in:d=0.3,afade=t=out:st={total / 30 - 1.5:.2f}:d=1.5", "-ar", "48000", "-ac", "2", str(SAIDA / "musica.wav")], check=True)
(RAIZ / "remotion/src/ad02-dados.json").write_text(json.dumps({"total": total, "linha": linha}, ensure_ascii=False, indent=1))
print(total, f"{total / 30:.1f}s")
