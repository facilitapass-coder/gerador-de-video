"""Gera trilhas instrumentais originais (sem direitos de terceiros), uma por ambiente:
  fiesta   cumbia animada: bar, noite, mercado, jantar, chegada
  mariachi polca com trompetes e violão: aberturas, deslocamentos, café, dança
  lounge   bossa suave: La Casa de la Playa
  aventura percussão e baixo pulsando: Xplor Fuego, túneis, toboáguas
  tropical marimba leve: manhã, piscina, natureza
Uso (na raiz): .venv/bin/python remotion/scripts/gerar_trilhas.py trabalho/musica"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np

SR = 48000
rng = np.random.default_rng(11)
NOMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(n):
    """'A4' -> 440.0"""
    return 440.0 * 2 ** ((NOMES[n[:-1]] + 12 * (int(n[-1]) + 1) - 69) / 12)


class Faixa:
    def __init__(self, segundos):
        self.x = np.zeros(int(segundos * SR))

    def soma(self, sinal, inicio, ganho=1.0):
        i = int(inicio * SR)
        if i >= len(self.x) or i < 0:
            return
        f = min(len(self.x), i + len(sinal))
        self.x[i:f] += ganho * sinal[: f - i]


def env(n, ataque=0.005, solta=0.05):
    t = np.arange(n) / SR
    return np.minimum(1, t / ataque) * np.minimum(1, (n / SR - t) / solta)


def corda(f, dur, brilho=0.5, queda=0.996):
    """Corda dedilhada (Karplus-Strong em blocos): violão, guitarrón, vihuela."""
    p = max(2, int(SR / f)); n = int(dur * SR)
    bloco = rng.uniform(-1, 1, p)
    for _ in range(int(3 * (1 - brilho)) + 1):                      # menos brilho = mais filtro
        bloco = 0.5 * (bloco + np.roll(bloco, 1))
    saida = np.empty(n + p)
    for k in range(0, n + p, p):
        saida[k:k + p] = bloco[: min(p, n + p - k)]
        bloco = 0.5 * (bloco + np.roll(bloco, 1)) * queda
    return saida[:n] * env(n, 0.002, 0.03)


def rasgueado(notas, dur=0.22, brilho=0.8):
    """Acorde rasgueado: as cordas entram com poucos milissegundos de diferença."""
    n = int((dur + 0.05) * SR); s = np.zeros(n)
    for i, nt in enumerate(notas):
        c = corda(hz(nt), dur, brilho, 0.992); a = int(i * 0.009 * SR)
        s[a:a + len(c)] += c[: n - a]
    return s * env(n, 0.002, 0.06) / len(notas)


def trompete(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.6 * t) * np.minimum(1, t / 0.25)
    fase = 2 * np.pi * np.cumsum(f * vib) / SR
    brilho = np.minimum(1, t / 0.04) * (0.75 + 0.25 * np.exp(-t * 3))
    s = sum(np.sin(k * fase) * (brilho ** (k - 1)) / k ** 1.15 for k in range(1, 10) if k * f < 9000)
    return s * env(n, 0.03, 0.07) * 0.5


def sanfona(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for des in (0.996, 1.004):
        s += sum(np.sin(2 * np.pi * k * f * des * t) / k for k in range(1, 9) if k * f < 7000)
    return s * env(n, 0.02, 0.05) * (0.85 + 0.15 * np.sin(2 * np.pi * 6 * t)) * 0.28


def piano_eletrico(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 5) + 0.15 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 12)
    return s * np.exp(-t * 1.8) * env(n, 0.004, 0.08) * (0.9 + 0.1 * np.sin(2 * np.pi * 4.5 * t))


def marimba(f, dur=0.8):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 9) + 0.12 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 16)
    return s * np.exp(-t * 6.5) * np.minimum(1, t / 0.004)


def baixo(f, dur=0.45):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)) * np.exp(-t * 3.5) * env(n, 0.006, 0.05)


def bumbo(forca=1.0):
    t = np.arange(int(0.3 * SR)) / SR
    return forca * np.sin(2 * np.pi * np.cumsum(46 + 85 * np.exp(-t * 30)) / SR) * np.exp(-t * 11)


def ruido(dur, queda, grave=8):
    n = int(dur * SR); r = rng.standard_normal(n)
    r = r - np.convolve(r, np.ones(grave) / grave, mode="same")
    return r * np.exp(-np.arange(n) / SR * queda)


def caixa():
    t = np.arange(int(0.16 * SR)) / SR
    return 0.5 * ruido(0.16, 30, 20) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 28)


def conga(f=210):
    t = np.arange(int(0.22 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.25 * np.exp(-t * 60))) / SR) * np.exp(-t * 17)


def tom(f=110):
    t = np.arange(int(0.4 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-t * 25))) / SR) * np.exp(-t * 8)


def campana():
    t = np.arange(int(0.18 * SR)) / SR
    return (np.sign(np.sin(2 * np.pi * 545 * t)) + np.sign(np.sin(2 * np.pi * 815 * t))) * np.exp(-t * 26) * 0.25


def guiro(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return ruido(dur, 4, 6) * (0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 42 * t))) * env(n, 0.004, 0.02)


TRIADES = {"G": ["G3", "B3", "D4", "G4"], "D7": ["D3", "A3", "C4", "F#4"], "C": ["C3", "G3", "C4", "E4"],
           "Am": ["A3", "C4", "E4", "A4"], "F": ["F3", "A3", "C4", "F4"], "E": ["E3", "G#3", "B3", "E4"], "Gm": ["G3", "B3", "D4", "G4"],
           "Dm": ["D3", "A3", "D4", "F4"], "Bb": ["A#2", "F3", "A#3", "D4"], "Cx": ["C3", "G3", "C4", "E4"]}
RAIZ_QUINTA = {"G": ("G2", "D2"), "D7": ("D2", "A2"), "C": ("C2", "G2"), "Am": ("A2", "E2"), "F": ("F2", "C2"), "E": ("E2", "B2"),
               "Dm": ("D2", "A2"), "Bb": ("A#1", "F2"), "Cx": ("C2", "G2")}
ESCALA_G = ["G3", "A3", "B3", "C4", "D4", "E4", "F#4", "G4", "A4", "B4", "C5", "D5", "E5", "F#5", "G5", "A5", "B5", "C6"]
terca_abaixo = lambda n: ESCALA_G[max(0, ESCALA_G.index(n) - 2)]


def mariachi():
    """Polca ranchera em Sol maior: guitarrón no tempo, vihuela no contratempo, dois trompetes em terças."""
    T = 60 / 118; C = 4 * T
    A = [("G", "B4 D5 B4 G4"), ("G", "B4 D5 G5 -"), ("D7", "A4 C5 A4 F#4"), ("D7", "A4 C5 F#5 -"),
         ("D7", "F#5 E5 D5 C5"), ("D7", "A4 C5 E5 D5"), ("G", "B4 D5 G5 D5"), ("G", "B4 - G4 -")]
    B = [("C", "E5 G5 E5 C5"), ("C", "E5 G5 C6 -"), ("G", "D5 G5 D5 B4"), ("G", "D5 G5 B5 -"),
         ("D7", "C5 E5 F#5 A5"), ("D7", "F#5 E5 D5 C5"), ("G", "B4 D5 G5 B5"), ("G", "G5 - - -")]
    intro = [("G", "- - - -"), ("D7", "- - - -")]
    forma = intro + A + A + B + A
    fx = Faixa(len(forma) * C + 2)
    for c, (ac, mel) in enumerate(forma):
        t0 = c * C; r, q = RAIZ_QUINTA[ac]
        fx.soma(corda(hz(r), 0.7, 0.3, 0.997), t0, 0.9); fx.soma(corda(hz(q), 0.7, 0.3, 0.997), t0 + 2 * T, 0.8)
        for b in (1, 3):
            fx.soma(rasgueado(TRIADES[ac][1:], 0.2), t0 + b * T, 0.55)
            fx.soma(rasgueado(TRIADES[ac][1:], 0.12), t0 + b * T + T / 2, 0.3)
        for k in range(8):
            fx.soma(ruido(0.05, 60), t0 + k * T / 2, 0.035 if k % 2 == 0 else 0.06)
        notas = mel.split(); k = 0
        while k < 4:
            if notas[k] != "-":
                dur = 1
                while k + dur < 4 and notas[k + dur] == "-": dur += 1
                fx.soma(trompete(hz(notas[k]), dur * T * 0.92), t0 + k * T, 0.34)
                fx.soma(trompete(hz(terca_abaixo(notas[k])), dur * T * 0.92), t0 + k * T + 0.008, 0.24)
                k += dur
            else:
                k += 1
    return fx.x, 118


def fiesta():
    """Cumbia em Lá menor: güiro, congas, baixo marcado, violão no contratempo e sanfona na melodia."""
    T = 60 / 98; C = 4 * T
    F1 = [("Am", "A4 - C5 E5 - C5 A4 -"), ("G", "G4 - B4 D5 - B4 G4 -"), ("F", "F4 - A4 C5 - A4 F4 -"), ("E", "E4 - G#4 B4 - D5 B4 G#4")]
    F2 = [("Am", "E5 - E5 D5 C5 - A4 -"), ("G", "D5 - D5 C5 B4 - G4 -"), ("F", "C5 - C5 B4 A4 - F4 -"), ("E", "B4 - G#4 - E5 E5 E5 -")]
    intro = [("Am", "- - - - - - - -"), ("E", "- - - - - - - -")]
    forma = intro + F1 + F2 + F1 + F2 + F1 + F2
    fx = Faixa(len(forma) * C + 2)
    for c, (ac, mel) in enumerate(forma):
        t0 = c * C; r, q = RAIZ_QUINTA[ac]
        fx.soma(baixo(hz(r), 0.5), t0, 0.75); fx.soma(baixo(hz(q), 0.3), t0 + 1.5 * T, 0.6)
        fx.soma(baixo(hz(r), 0.45), t0 + 2 * T, 0.75); fx.soma(baixo(hz(q), 0.3), t0 + 3 * T, 0.6)
        for b in range(4):
            fx.soma(guiro(T / 2 * 0.9), t0 + b * T, 0.09)
            fx.soma(guiro(T / 4 * 0.8), t0 + b * T + T / 2, 0.07); fx.soma(guiro(T / 4 * 0.8), t0 + b * T + 3 * T / 4, 0.07)
            fx.soma(rasgueado(TRIADES[ac][1:], 0.13, 0.9), t0 + b * T + T / 2, 0.5)
            if b in (0, 2): fx.soma(bumbo(0.75), t0 + b * T); fx.soma(campana(), t0 + b * T, 0.5)
        for pos, f0 in ((1, 260), (1.5, 210), (2.75, 260), (3.5, 210), (3.75, 180)):
            fx.soma(conga(f0), t0 + pos * T, 0.32)
        notas = mel.split(); k = 0
        while k < 8:
            if notas[k] != "-":
                dur = 1
                while k + dur < 8 and notas[k + dur] == "-": dur += 1
                fx.soma(sanfona(hz(notas[k]), dur * T / 2 * 0.9), t0 + k * T / 2, 0.5)
                k += dur
            else:
                k += 1
    return fx.x, 98


def lounge():
    """Bossa suave em Dó: piano elétrico, baixo acústico, chocalho e aro."""
    T = 60 / 88; C = 4 * T
    prog = [("C", ["C4", "E4", "G4", "B4"], "C2", "G2"), ("Am", ["A3", "C#4", "E4", "G4"], "A2", "E2"),
            ("Dm", ["D4", "F4", "A4", "C5"], "D2", "A2"), ("G", ["G3", "B3", "D4", "F4"], "G2", "D2")]
    mel = ["E5 - G5 - - B4 - -", "C#5 - E5 - - - G4 -", "F5 - A5 - - C5 - -", "D5 - B4 - - - - -"]
    n = 28; fx = Faixa(n * C + 2)
    for c in range(n):
        _, notas, r, q = prog[c % 4]; t0 = c * C
        for pos in (0, 1.5, 2.5):
            for nt in notas: fx.soma(piano_eletrico(hz(nt), 0.9), t0 + pos * T, 0.11)
        fx.soma(baixo(hz(r), 0.9), t0, 0.6); fx.soma(baixo(hz(q), 0.4), t0 + 1.5 * T, 0.45); fx.soma(baixo(hz(q), 0.6), t0 + 2 * T, 0.5); fx.soma(baixo(hz(r), 0.3), t0 + 3.5 * T, 0.45)
        for k in range(8): fx.soma(ruido(0.06, 45), t0 + k * T / 2, 0.03 if k % 2 == 0 else 0.05)
        if c >= 2:
            for pos in (0, 1.5, 3, 5, 6.5): fx.soma(ruido(0.03, 90, 3), t0 + (pos % 8) * T / 2, 0.09)
        if c >= 4:
            ns = mel[c % 4].split(); k = 0
            while k < 8:
                if ns[k] != "-":
                    dur = 1
                    while k + dur < 8 and ns[k + dur] == "-": dur += 1
                    fx.soma(piano_eletrico(hz(ns[k]), dur * T / 2 + 0.3), t0 + k * T / 2, 0.22); k += dur
                else:
                    k += 1
    return fx.x, 88


def aventura():
    """Ré menor, percussão de tambores, baixo pulsando e ostinato de marimba."""
    T = 60 / 114; C = 4 * T
    prog = [("Dm", "D5 F5 A5 F5 D5 F5 A5 F5"), ("Dm", "D5 F5 A5 F5 D5 A5 G5 F5"), ("Bb", "D5 F5 A#5 F5 D5 F5 A#5 F5"), ("Cx", "E5 G5 C6 G5 E5 G5 C6 E5")]
    n = 30; fx = Faixa(n * C + 2)
    for c in range(n):
        ac, ost = prog[c % 4]; t0 = c * C; r, q = RAIZ_QUINTA[ac]; cheio = c >= 4
        for k in range(8):
            fx.soma(baixo(hz(r), 0.22), t0 + k * T / 2, 0.55 if k % 2 == 0 else 0.35)
        for k, nt in enumerate(ost.split()):
            fx.soma(marimba(hz(nt), 0.5), t0 + k * T / 2, 0.2 if cheio else 0.14)
        if c >= 2:
            for pos, f0 in ((0, 95), (0.75, 95), (1.5, 130), (2, 95), (2.75, 130), (3.5, 160)):
                fx.soma(tom(f0), t0 + pos * T, 0.5)
        if cheio:
            fx.soma(bumbo(0.9), t0); fx.soma(bumbo(0.9), t0 + 2 * T); fx.soma(bumbo(0.6), t0 + 2.5 * T)
            fx.soma(caixa(), t0 + T, 0.45); fx.soma(caixa(), t0 + 3 * T, 0.45)
            for k in range(16): fx.soma(ruido(0.03, 90), t0 + k * T / 4, 0.03 if k % 4 else 0.06)
            notas = TRIADES[ac]
            t = np.arange(int(C * SR)) / SR
            pad = sum(np.sin(2 * np.pi * hz(x) * 2 * t) for x in notas[1:]) * env(len(t), 0.4, 0.4)
            fx.soma(pad, t0, 0.03)
    return fx.x, 114


def tropical():
    """Marimba leve em Dó maior (a trilha calma)."""
    T = 60 / 104; C = 4 * T
    ac = [("C2", ["C4", "E4", "G4", "C5"]), ("G2", ["B3", "D4", "G4", "B4"]), ("A2", ["A3", "C4", "E4", "A4"]), ("F2", ["A3", "C4", "F4", "A4"])]
    n = 32; fx = Faixa(n * C + 2)
    for c in range(n):
        r, notas = ac[c % 4]; t0 = c * C; cheio = 4 <= c < n - 2
        for k, p in enumerate([0, 2, 1, 3, 2, 1, 3, 2]):
            fx.soma(marimba(hz(notas[p])), t0 + k * T / 2 + (0.012 if k % 2 else 0), 0.3 if k % 2 == 0 else 0.22)
        t = np.arange(int((C + 0.4) * SR)) / SR
        fx.soma(sum(np.sin(2 * np.pi * hz(x) * t) for x in notas[:3]) * env(len(t), 0.5, 0.5), t0, 0.04)
        if c >= 2: fx.soma(baixo(hz(r), 0.55), t0, 0.55); fx.soma(baixo(hz(r), 0.55), t0 + 2.5 * T, 0.5)
        if cheio:
            fx.soma(bumbo(0.6), t0); fx.soma(bumbo(0.6), t0 + 2 * T)
            fx.soma(ruido(0.12, 34, 24), t0 + T, 0.16); fx.soma(ruido(0.12, 34, 24), t0 + 3 * T, 0.16)
            for k in range(8): fx.soma(ruido(0.07, 55), t0 + k * T / 2, 0.05 if k % 2 == 0 else 0.085)
    return fx.x, 104


destino = Path(sys.argv[1]); destino.mkdir(parents=True, exist_ok=True)
info = {}
for nome, gera in (("fiesta", fiesta), ("mariachi", mariachi), ("lounge", lounge), ("aventura", aventura), ("tropical", tropical)):
    x, bpm = gera()
    x = np.tanh(x * 1.5); x /= np.abs(x).max() / 0.9
    bruto = destino / f"{nome}.bruto.wav"
    with wave.open(str(bruto), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(bruto), "-af",
                    "aecho=0.8:0.55:65|130:0.2|0.1,lowpass=f=11000,highpass=f=35,loudnorm=I=-16:TP=-1.5:LRA=9", "-ac", "2", "-ar", "48000", str(destino / f"{nome}.wav")], check=True)
    bruto.unlink(); info[nome] = {"bpm": bpm, "segundos": round(len(x) / SR, 1)}
    print(nome, info[nome])
import json
(destino / "trilhas.json").write_text(json.dumps(info, indent=1))
