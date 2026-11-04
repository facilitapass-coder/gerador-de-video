"""Reels 02 (La Casa de la Playa, narrado): corta os planos no tempo da narração `audio/02.m4a`.
Uso (na raiz): .venv/bin/python remotion/scripts/preparar_r02.py"""
import json, subprocess
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; ORIG = RAIZ / "projetos" / "_do-app-fotos"; SAIDA = RAIZ / "remotion" / "public" / "r02"
idx = {r["n"]: r for r in json.load(open(RAIZ / "trabalho" / "fotos-app-videos.json"))}
def origem(o):
    if isinstance(o, int): return ORIG / idx[o]["pasta"] / idx[o]["arquivo"]
    return (RAIZ / "remotion" / "public" / o) if o.startswith("clips/") else ORIG / o
CORTE = 1.1   # silêncio no começo da gravação
# (origem, início no clip, fim do trecho na narração original em s, texto na tela, destaque)
PLANOS = [
 ("reels/DJI_0587.MP4", 12.0, 3.6, "", ""), (109, 51.5, 6.0, "", ""), (122, 0.5, 9.7, "De verdade.", ""),
 (117, 1.0, 14.4, "Piscina privativa", "aquecida"), (109, 75.5, 17.0, "Jacuzzi de", "pedra vulcânica"), (109, 13.0, 21.2, "Mordomo", "24 horas"),
 ("reels/DJI_0576.MP4", 3.0, 24.9, "La Casa de la Playa", "Riviera Maya"), ("reels/DJI_0593.MP4", 13.0, 27.8, "Só", "63 suítes"), (128, 1.0, 30.1, "Todas de frente", "pro mar"),
 (148, 3.0, 34.0, "Piscina", "infinita"), (160, 2.5, 38.1, "com bar", "dentro d'água"),
 (145, 1.0, 39.55, "", "Chocolateria"), ("../_material-xcaret/Redes Sociais/La Casa de La Playa/VÍDEOS/La Casa de la Playa_Cava (Adega).MP4", 2.0, 40.4, "", "Adega"), (136, 5.0, 41.6, "", "Biblioteca"), (117, 28.0, 43.9, "Praia só dos", "hóspedes"),
 ("clips/xplor2.mp4", 0.4, 46.3, "E os parques do", "Grupo Xcaret"), ("clips/xelha7.mp4", 2.0, 48.75, "E os parques do", "Grupo Xcaret"),
 (162, 0.0, 50.75, "Eu não queria", "mais sair"), (160, 5.0, 54.4, "", ""),
]
VF = "fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1,format=yuv420p"
def ff(*a): subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *a], check=True)
linha, ini = [], CORTE
for i, (o, a, fim, t1, t2) in enumerate(PLANOS):
    q = round((fim - CORTE) * 30) - round((ini - CORTE) * 30)
    ff("-ss", f"{a}", "-i", str(origem(o)), "-an", "-vf", VF + f",tpad=stop_mode=clone:stop_duration=3", "-frames:v", str(q), "-c:v", "libx264", "-preset", "fast", "-crf", "16", str(SAIDA / f"p{i:02d}.mp4"))
    linha.append({"arquivo": f"p{i:02d}.mp4", "quadros": q, "t1": t1, "t2": t2}); ini = fim
voz = RAIZ / "projetos" / "all-fun-inclusive" / "audio" / "02.m4a"
ff("-ss", f"{CORTE}", "-i", str(voz), "-af", "highpass=f=85,afftdn=nr=10,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3,loudnorm=I=-15:TP=-1.5:LRA=7,afade=t=in:d=0.04",
   "-ar", "48000", "-ac", "2", str(SAIDA / "voz.wav"))
total = sum(l["quadros"] for l in linha); dur = total / 30
ff("-ss", "20", "-i", str(RAIZ / "trabalho/musica/banco/latin-party-pop.mp3"), "-t", f"{dur}", "-af",
   f"loudnorm=I=-16:TP=-1.5,volume=0.13,afade=t=in:d=0.5,afade=t=out:st={dur - 1.5:.2f}:d=1.5", "-ar", "48000", "-ac", "2", str(SAIDA / "musica.wav"))
(RAIZ / "remotion" / "src" / "r02-dados.json").write_text(json.dumps({"total": total, "linha": linha}, ensure_ascii=False, indent=1))
print(total, f"{dur:.1f}s", [l["quadros"] for l in linha])
