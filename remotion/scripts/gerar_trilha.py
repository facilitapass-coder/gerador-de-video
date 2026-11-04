"""Gera uma trilha instrumental original (sem direitos de terceiros) para Stories sem fala.
Uso (na raiz): .venv/bin/python remotion/scripts/gerar_trilha.py trabalho/musica/trilha-facilita-01.wav"""
import subprocess, sys, wave
from pathlib import Path
import numpy as np

SR, BPM = 48000, 104
T = 60 / BPM                      # tempo
COMPASSO = 4 * T
rng = np.random.default_rng(7)
nota = lambda n: 440.0 * 2 ** ((n - 69) / 12)
# Dó maior: C – G – Am – F (tônica, quinta, sexta menor, quarta)
ACORDES = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69])]
N_COMPASSOS = 32
total = int((N_COMPASSOS * COMPASSO + 2) * SR)
mix = np.zeros(total)

def soma(sinal, inicio):
    i = int(inicio * SR); f = min(total, i + len(sinal)); mix[i:f] += sinal[: f - i]

def marimba(f, dur=0.9, amp=1.0):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 9) + 0.12 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 16)
    return amp * s * np.exp(-t * 6.5) * np.minimum(1, t / 0.004)

def pad(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    s = sum(np.sin(2 * np.pi * nota(n) * t + rng.uniform(0, 6)) + 0.25 * np.sin(2 * np.pi * 2 * nota(n) * t) for n in notas)
    env = np.minimum(1, t / 0.5) * np.minimum(1, (dur - t) / 0.5)
    return 0.045 * s * env

def baixo(f, dur=0.55):
    t = np.arange(int(dur * SR)) / SR
    return 0.42 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 4.2) * np.minimum(1, t / 0.006)

def bumbo():
    t = np.arange(int(0.32 * SR)) / SR
    f = 46 + 80 * np.exp(-t * 28)
    return 0.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)

def chocalho(amp):
    n = int(0.07 * SR); r = rng.standard_normal(n)
    r = r - np.convolve(r, np.ones(8) / 8, mode="same")          # tira os graves
    return amp * r * np.exp(-np.arange(n) / SR * 55)

def estalo():
    n = int(0.12 * SR); r = rng.standard_normal(n)
    r = np.convolve(r - np.convolve(r, np.ones(24) / 24, mode="same"), np.ones(3) / 3, mode="same")
    return 0.16 * r * np.exp(-np.arange(n) / SR * 34)

PADRAO = [0, 2, 1, 3, 2, 1, 3, 2]                                   # arpejo em colcheias
for c in range(N_COMPASSOS):
    t0 = c * COMPASSO; raiz, notas = ACORDES[c % 4]
    cheio = c >= 4 and c < N_COMPASSOS - 2                           # entrada só com marimba e pad
    soma(pad(notas[:3], COMPASSO + 0.4), t0)
    for k, p in enumerate(PADRAO):
        oitava = 12 if (c // 4) % 2 == 1 and k in (3, 7) else 0
        soma(marimba(nota(notas[p] + oitava), amp=0.30 if k % 2 == 0 else 0.22), t0 + k * T / 2 + (0.012 if k % 2 else 0))
    if c >= 2:
        soma(baixo(nota(raiz)), t0); soma(baixo(nota(raiz)), t0 + 2.5 * T)
        if cheio: soma(baixo(nota(raiz + 7), 0.3), t0 + 3.5 * T)
    if cheio:
        soma(bumbo(), t0); soma(bumbo(), t0 + 2 * T)
        soma(estalo(), t0 + T); soma(estalo(), t0 + 3 * T)
        for k in range(8): soma(chocalho(0.05 if k % 2 == 0 else 0.085), t0 + k * T / 2)

mix = np.tanh(mix * 1.4)
mix /= np.abs(mix).max() / 0.9
bruto = Path(sys.argv[1]).with_suffix(".bruto.wav")
with wave.open(str(bruto), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(bruto), "-af",
                "aecho=0.8:0.6:70|140:0.22|0.12,lowpass=f=9500,highpass=f=35,loudnorm=I=-16:TP=-1.5:LRA=9", "-ac", "2", "-ar", "48000", sys.argv[1]], check=True)
bruto.unlink()
print("trilha:", sys.argv[1], f"{N_COMPASSOS * COMPASSO:.1f}s a {BPM} BPM")
