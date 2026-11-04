#!/usr/bin/env python3
"""Facilita Studio · ferramentas de mídia (só biblioteca padrão + ffmpeg + whisper-cli).

Uso: python3 estudio.py <comando> [opções]   (python3 estudio.py <comando> -h para ajuda)

  info        resolução, duração, fps, rotação e volume de cada arquivo
  folha       folha de contato com o tempo escrito em cada quadro
  silencios   pausas da fala (JSON) para decidir onde cortar
  cortar      mantém só os trechos pedidos (vídeo + áudio), já em H.264
  vertical    converte vídeo do celular (HEVC/4K) em 1080×1920 H.264 sem áudio
  voz         limpa e nivela a voz (perfil normal, abafado ou baixo)
  juntar      junta áudios com durações exatas (evita perder o sincronismo)
  transcrever palavras com tempo (JSON) + correção pelo dicionário da marca
  trilha      trilha sintetizada sem direitos autorais (suspense, animada, calma)
  master      nivela o áudio do vídeo final em -14 LUFS sem recodificar a imagem
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MODELO_PADRAO = Path(os.environ.get("FACILITA_WHISPER_MODELO", Path.home() / ".facilita-studio" / "modelos" / "ggml-small.bin"))

PERFIS_VOZ = {
    # gravação comum de celular
    "normal": "highpass=f=80,afftdn=nr=8:nf=-35,acompressor=threshold=-24dB:ratio=3:attack=5:release=80:makeup=2",
    # voz abafada (microfone tampado, ambiente fechado): tira graves embolados e devolve brilho
    "abafado": (
        "highpass=f=100,afftdn=nr=10:nf=-28:tn=1,equalizer=f=180:t=q:w=1:g=-3,equalizer=f=320:t=q:w=1.1:g=-6,"
        "equalizer=f=550:t=q:w=1.2:g=-2,equalizer=f=2800:t=q:w=1.3:g=6,equalizer=f=4800:t=q:w=1.4:g=6,"
        "highshelf=f=8000:g=6,aexciter=amount=1.5:drive=6:freq=3500:blend=0,deesser=i=0.45:f=0.6,"
        "acompressor=threshold=-22dB:ratio=3:attack=4:release=70:makeup=2"
    ),
    # gravação de tela com voz muito baixa
    "baixo": "highpass=f=80,afftdn=nr=8:nf=-40,acompressor=threshold=-30dB:ratio=4:attack=5:release=80:makeup=6",
}


def rodar(cmd: list[str], capturar: bool = False) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Falhou: {' '.join(cmd[:3])}…\n{r.stderr[-1500:]}")
    return (r.stdout + r.stderr) if capturar else r.stdout


def exigir(binario: str, dica: str) -> None:
    if not shutil.which(binario):
        sys.exit(f"Não encontrei '{binario}'. {dica}")


def sondar(arq: str) -> dict:
    out = rodar(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", arq])
    return json.loads(out)


def duracao(arq: str) -> float:
    return float(sondar(arq)["format"]["duration"])


# ---------------------------------------------------------------- info
def cmd_info(a):
    exigir("ffprobe", "Instale o ffmpeg.")
    for arq in a.arquivos:
        d = sondar(arq)
        v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
        tem_audio = any(s["codec_type"] == "audio" for s in d["streams"])
        linha = {"arquivo": arq, "duracao": round(float(d["format"]["duration"]), 2)}
        if v:
            rot = 0
            for sd in v.get("side_data_list", []):
                if "rotation" in sd:
                    rot = int(sd["rotation"])
            w, h = v["width"], v["height"]
            if abs(rot) in (90, 270):
                w, h = h, w
            num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
            linha.update({"largura": w, "altura": h, "fps": round(int(num) / max(int(den), 1), 2), "codec": v["codec_name"], "rotacao": rot})
        if tem_audio:
            vol = rodar(["ffmpeg", "-hide_banner", "-i", arq, "-af", "volumedetect", "-vn", "-f", "null", "-"], capturar=True)
            m = re.search(r"mean_volume: ([-\d.]+)", vol)
            linha["volume_medio_db"] = float(m.group(1)) if m else None
        print(json.dumps(linha, ensure_ascii=False))


# ---------------------------------------------------------------- folha
def fonte_sistema() -> str | None:
    for f in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if Path(f).exists():
            return f
    return None


def cmd_folha(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    total = duracao(a.video)
    n = max(1, int(total / a.a_cada) + 1)
    colunas = a.colunas
    linhas = (n + colunas - 1) // colunas
    fonte = fonte_sistema()
    texto = f",drawtext=fontfile={fonte}:text='%{{pts\\:hms}}':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6" if fonte else ""
    vf = f"fps=1/{a.a_cada},scale={a.largura}:-2{texto},tile={colunas}x{linhas}"
    rodar(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", vf, "-frames:v", "1", a.saida])
    print(f"Folha salva em {a.saida} ({n} quadros, um a cada {a.a_cada}s)")


# ---------------------------------------------------------------- silencios
def cmd_silencios(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    out = rodar(["ffmpeg", "-hide_banner", "-i", a.arquivo, "-af", f"silencedetect=n={a.limite}dB:d={a.minimo}", "-vn", "-f", "null", "-"], capturar=True)
    inicios = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    fins = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    total = duracao(a.arquivo)
    pausas = [{"de": round(i, 2), "ate": round(f, 2), "dur": round(f - i, 2)} for i, f in zip(inicios, fins + [total] * (len(inicios) - len(fins)))]
    # sugestão de trechos a manter: corta pausas longas deixando respiro dos dois lados
    manter, cursor = [], 0.0
    for p in pausas:
        if p["dur"] >= a.cortar_acima:
            fim = p["de"] + a.respiro
            if fim - cursor > 0.3:
                manter.append([round(cursor, 2), round(fim, 2)])
            cursor = p["ate"] - a.respiro
    if total - cursor > 0.3:
        manter.append([round(max(cursor, 0), 2), round(total, 2)])
    print(json.dumps({"duracao": round(total, 2), "pausas": pausas, "manter_sugerido": manter}, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- cortar
def cmd_cortar(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    trechos = [tuple(float(x) for x in t.split(":")) for t in a.manter.split(",")]
    tem_audio = any(s["codec_type"] == "audio" for s in sondar(a.video)["streams"])
    fc, rot = "", ""
    for n, (i, f) in enumerate(trechos):
        fc += f"[0:v]trim={i}:{f},setpts=PTS-STARTPTS,fps={a.fps}[v{n}];"
        if tem_audio:
            fc += f"[0:a]atrim={i}:{f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,areverse,afade=t=in:d=0.02,areverse[a{n}];"
            rot += f"[v{n}][a{n}]"
        else:
            rot += f"[v{n}]"
    fc += f"{rot}concat=n={len(trechos)}:v=1:a={1 if tem_audio else 0}[v]" + ("[a]" if tem_audio else "")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.video, "-filter_complex", fc, "-map", "[v]"]
    if tem_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "256k"]
    cmd += ["-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium", "-pix_fmt", "yuv420p", a.saida]
    rodar(cmd)
    print(json.dumps({"saida": a.saida, "duracao": round(duracao(a.saida), 3), "trechos": trechos}, ensure_ascii=False))


# ---------------------------------------------------------------- vertical
def cmd_vertical(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    vf = f"scale={a.largura}:{a.altura}:force_original_aspect_ratio=increase,crop={a.largura}:{a.altura},fps={a.fps}"
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if a.inicio:
        cmd += ["-ss", str(a.inicio)]
    cmd += ["-i", a.video]
    if a.duracao:
        cmd += ["-t", str(a.duracao)]
    cmd += ["-vf", vf, "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", a.saida]
    rodar(cmd)
    print(json.dumps({"saida": a.saida, "duracao": round(duracao(a.saida), 3)}))


# ---------------------------------------------------------------- voz
def cmd_voz(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    cadeia = PERFIS_VOZ[a.perfil] + f",loudnorm=I={a.lufs}:TP=-1.5:LRA=7"
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if a.inicio:
        cmd += ["-ss", str(a.inicio)]
    if a.duracao:
        cmd += ["-t", str(a.duracao)]
    cmd += ["-i", a.entrada]
    alvo = a.duracao or (duracao(a.entrada) - (a.inicio or 0))
    # loudnorm encurta alguns milissegundos: completa até a duração exata para não perder o sincronismo
    cadeia += f",apad,atrim=0:{alvo:.3f}"
    cmd += ["-vn", "-af", cadeia, "-ar", "48000", "-ac", "1", a.saida]
    rodar(cmd)
    print(json.dumps({"saida": a.saida, "duracao": round(duracao(a.saida), 3), "perfil": a.perfil}))


# ---------------------------------------------------------------- juntar
def cmd_juntar(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    pares = [p.rsplit("@", 1) if "@" in p else [p, None] for p in a.partes]
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for arq, _ in pares:
        cmd += ["-i", arq]
    fc = ""
    for n, (_, dur) in enumerate(pares):
        fc += f"[{n}]apad,atrim=0:{dur}[p{n}];" if dur else f"[{n}]anull[p{n}];"
    fc += "".join(f"[p{n}]" for n in range(len(pares))) + f"concat=n={len(pares)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=7,alimiter=limit=0.88"
    cmd += ["-filter_complex", fc, "-ar", "48000", a.saida]
    rodar(cmd)
    print(json.dumps({"saida": a.saida, "duracao": round(duracao(a.saida), 3)}))


# ---------------------------------------------------------------- transcrever
def carregar_dicionario(marca: str | None) -> list[str]:
    if not marca or not Path(marca).exists():
        return []
    try:
        return json.loads(Path(marca).read_text(encoding="utf-8")).get("dicionario", [])
    except json.JSONDecodeError:
        return []


def corrigir(palavra: str, dicionario: list[str]) -> str:
    nucleo = re.sub(r"[.,!?;:\"]+$", "", palavra).strip('"')
    sufixo = palavra[len(palavra.rstrip('.,!?;:"')):].replace('"', "")
    base = re.sub(r"[^\wà-ú.]", "", nucleo.lower())
    for certo in dicionario:
        alvo = re.sub(r"[^\wà-ú.]", "", certo.lower())
        if base == alvo or (len(alvo) > 4 and _parecido(base, alvo)):
            return certo + sufixo
    return nucleo + sufixo


def _parecido(a: str, b: str) -> bool:
    # distância de edição <= 2 (pega "ventuski" -> "ventusky", "simipar" -> "simepar")
    if abs(len(a) - len(b)) > 2:
        return False
    ant = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(ant[j] + 1, atual[j - 1] + 1, ant[j - 1] + (ca != cb)))
        ant = atual
    return ant[-1] <= 2


def cmd_transcrever(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    exigir("whisper-cli", "Instale o whisper.cpp (Mac: brew install whisper-cpp).")
    modelo = Path(a.modelo)
    if not modelo.exists():
        sys.exit(f"Modelo do whisper não encontrado em {modelo}. Rode scripts/checar-ambiente.sh para ver como baixar.")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        rodar(["ffmpeg", "-v", "error", "-y", "-i", a.audio, "-ar", "16000", "-ac", "1", str(wav)])
        base = Path(tmp) / "w"
        rodar(["whisper-cli", "-m", str(modelo), "-l", a.idioma, "-f", str(wav), "-ml", "1", "-sow", "-ojf", "-of", str(base)])
        dados = json.loads((base.with_suffix(".json")).read_text(encoding="utf-8"))
    dic = carregar_dicionario(a.marca) + (a.dicionario.split(",") if a.dicionario else [])
    palavras = []
    for s in dados["transcription"]:
        t = s["text"].strip()
        if not t or t.startswith("[") or t.startswith("("):
            continue
        palavras.append({"w": corrigir(t, dic), "i": round(s["offsets"]["from"] / 1000 + a.deslocar, 2), "f": round(s["offsets"]["to"] / 1000 + a.deslocar, 2)})
    Path(a.saida).write_text(json.dumps(palavras, ensure_ascii=False), encoding="utf-8")
    print(f"{len(palavras)} palavras em {a.saida}\n" + " ".join(p["w"] for p in palavras))


# ---------------------------------------------------------------- trilha
TRILHAS = {
    "suspense": (
        "(0.22*sin(2*PI*55*t)+0.16*sin(2*PI*82.41*t)+0.08*sin(2*PI*110.7*t)+0.06*sin(2*PI*130.81*t))*(0.7+0.3*sin(2*PI*0.18*t))"
        "+0.55*sin(2*PI*48*t)*exp(-9*mod(t,0.85))+0.3*sin(2*PI*48*t)*exp(-12*mod(t+0.6,0.85))"
        "+0.035*sin(2*PI*659.25*t+2.5*sin(2*PI*0.21*t))*(0.5+0.5*sin(2*PI*0.06*t))"
    ),
    "animada": (
        "0.5*sin(2*PI*55*t)*exp(-7*mod(t,0.5))+0.18*sin(2*PI*220*t)*exp(-14*mod(t+0.25,0.5))"
        "+0.06*(sin(2*PI*261.6*t)+sin(2*PI*329.6*t)+sin(2*PI*392*t))*(0.6+0.4*sin(2*PI*0.5*t))"
        "+0.05*sin(2*PI*523.3*t)*exp(-10*mod(t,0.25))"
    ),
    "calma": (
        "0.08*(sin(2*PI*196*t)+sin(2*PI*246.9*t)+sin(2*PI*293.7*t))*(0.6+0.4*sin(2*PI*0.08*t))"
        "+0.04*sin(2*PI*587.3*t+1.5*sin(2*PI*0.15*t))*(0.5+0.5*sin(2*PI*0.05*t))"
    ),
}


def cmd_trilha(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    d = a.duracao
    expr = TRILHAS[a.clima]
    fc = "[0]lowpass=f=2500,aecho=0.8:0.7:180|320:0.35|0.25[m];"
    entradas = ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}"]
    if a.clima == "suspense":
        entradas += ["-f", "lavfi", "-i", f"anoisesrc=c=brown:a=0.35:d={d}:r=48000"]
        fc += "[1]bandpass=f=500:width_type=o:w=1.5,volume='0.5+0.5*sin(2*PI*0.11*t)':eval=frame,lowpass=f=1200[w];[m][w]amix=inputs=2:weights=1 0.6,"
    else:
        fc += "[m]anull,"
    fc += f"pan=stereo|c0=c0|c1=c0,afade=t=in:d=1.5,afade=t=out:st={max(d - 2.5, 0)}:d=2.5,loudnorm=I=-18:TP=-2"
    rodar(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", fc, "-ar", "48000", a.saida])
    print(json.dumps({"saida": a.saida, "duracao": d, "clima": a.clima}))


# ---------------------------------------------------------------- master
def cmd_master(a):
    exigir("ffmpeg", "Instale o ffmpeg.")
    tmp = str(Path(a.video).with_suffix(".tmp.mp4"))
    rodar(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-c:v", "copy", "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=8", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", tmp])
    os.replace(tmp, a.video)
    out = rodar(["ffmpeg", "-hide_banner", "-i", a.video, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"], capturar=True)
    m = re.findall(r"I:\s+([-\d.]+) LUFS", out)
    print(json.dumps({"video": a.video, "lufs": float(m[-1]) if m else None}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("info"); s.add_argument("arquivos", nargs="+"); s.set_defaults(f=cmd_info)
    s = sub.add_parser("folha"); s.add_argument("video"); s.add_argument("saida"); s.add_argument("--a-cada", type=float, default=2); s.add_argument("--colunas", type=int, default=5); s.add_argument("--largura", type=int, default=360); s.set_defaults(f=cmd_folha)
    s = sub.add_parser("silencios"); s.add_argument("arquivo"); s.add_argument("--limite", type=float, default=-40); s.add_argument("--minimo", type=float, default=0.35); s.add_argument("--cortar-acima", type=float, default=0.6, help="pausas maiores que isso entram no corte sugerido"); s.add_argument("--respiro", type=float, default=0.18); s.set_defaults(f=cmd_silencios)
    s = sub.add_parser("cortar"); s.add_argument("video"); s.add_argument("saida"); s.add_argument("--manter", required=True, help="ex.: 0:2.6,3.05:8.2"); s.add_argument("--fps", type=int, default=30); s.add_argument("--crf", type=int, default=14); s.set_defaults(f=cmd_cortar)
    s = sub.add_parser("vertical"); s.add_argument("video"); s.add_argument("saida"); s.add_argument("--inicio", type=float); s.add_argument("--duracao", type=float); s.add_argument("--largura", type=int, default=1080); s.add_argument("--altura", type=int, default=1920); s.add_argument("--fps", type=int, default=30); s.set_defaults(f=cmd_vertical)
    s = sub.add_parser("voz"); s.add_argument("entrada"); s.add_argument("saida"); s.add_argument("--perfil", choices=list(PERFIS_VOZ), default="normal"); s.add_argument("--inicio", type=float); s.add_argument("--duracao", type=float); s.add_argument("--lufs", type=float, default=-15); s.set_defaults(f=cmd_voz)
    s = sub.add_parser("juntar", help="partes no formato arquivo.wav@duracao"); s.add_argument("saida"); s.add_argument("partes", nargs="+"); s.set_defaults(f=cmd_juntar)
    s = sub.add_parser("transcrever"); s.add_argument("audio"); s.add_argument("saida"); s.add_argument("--marca", default="marca.json"); s.add_argument("--dicionario", help="palavras extras separadas por vírgula"); s.add_argument("--idioma", default="pt"); s.add_argument("--modelo", default=str(MODELO_PADRAO)); s.add_argument("--deslocar", type=float, default=0.0); s.set_defaults(f=cmd_transcrever)
    s = sub.add_parser("trilha"); s.add_argument("saida"); s.add_argument("--duracao", type=float, required=True); s.add_argument("--clima", choices=list(TRILHAS), default="suspense"); s.set_defaults(f=cmd_trilha)
    s = sub.add_parser("master"); s.add_argument("video"); s.add_argument("--lufs", type=float, default=-14); s.set_defaults(f=cmd_master)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
