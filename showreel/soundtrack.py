"""Synthesizes the 15 s showreel soundtrack, locked to the same 128 BPM grid as reel.html.

    python3 soundtrack.py   → soundtrack.wav (48 kHz, stereo, 16-bit)
"""
import wave

import numpy as np

SR = 48000
DUR = 15.0
BPM = 128
B = 60 / BPM
BAR = 4 * B
N = int(SR * DUR)
rng = np.random.default_rng(2026)

L = np.zeros(N)
R = np.zeros(N)
VERB = np.zeros((2, N))  # reverb send


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def fft_filter(x, lo=None, hi=None, order=2):
    """Zero-phase Butterworth-magnitude filter in the frequency domain."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    if hi:
        X /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        X /= np.sqrt(1 + (lo / f) ** (2 * order))
    return np.fft.irfft(X, len(x))


def add(sig, at, gain=1.0, pan=0.0, send=0.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i : i + len(sig)] += sig * gain * gl * 1.414
    R[i : i + len(sig)] += sig * gain * gr * 1.414
    if send:
        VERB[0, i : i + len(sig)] += sig * gain * send * gl
        VERB[1, i : i + len(sig)] += sig * gain * send * gr


def add_st(l, r, at, gain=1.0, send=0.0):
    i = int(at * SR)
    n = min(len(l), N - i)
    L[i : i + n] += l[:n] * gain
    R[i : i + n] += r[:n] * gain
    if send:
        VERB[0, i : i + n] += l[:n] * gain * send
        VERB[1, i : i + n] += r[:n] * gain * send


def saw(freq, t, phase=0.0):
    return 2 * ((freq * t + phase) % 1) - 1


# ── instruments ──────────────────────────────────────────────────────────────
def kick(dur=0.5):
    t = tvec(dur)
    f = 44 + 120 * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.3)
    click = rng.standard_normal(len(t)) * np.exp(-t / 0.002) * 0.4
    return np.tanh(1.6 * (body + click))


def clap(dur=0.35):
    t = tvec(dur)
    n = rng.standard_normal(len(t))
    env = np.exp(-t / 0.12) * 0.7
    for k in range(3):
        env += np.where(t >= k * 0.011, np.exp(-(t - k * 0.011) / 0.005), 0)
    return fft_filter(n * env, lo=900, hi=4200)


def hat(dur=0.08, decay=0.03):
    t = tvec(dur)
    return fft_filter(rng.standard_normal(len(t)), lo=7500) * np.exp(-t / decay)


def snare(dur=0.25):
    t = tvec(dur)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)
    return 0.6 * body + fft_filter(rng.standard_normal(len(t)), lo=1500, hi=9000) * np.exp(-t / 0.07)


def impact(dur=2.4):
    t = tvec(dur)
    f = 26 + 52 * np.exp(-t / 0.35)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    crash = fft_filter(rng.standard_normal(len(t)), lo=60, hi=1600) * np.exp(-t / 0.35)
    return np.tanh(1.5 * boom) + 0.5 * crash


def whoosh(dur, lo=400, hi=5000):
    t = tvec(dur)
    env = np.sin(np.pi * t / dur) ** 2
    return fft_filter(rng.standard_normal(len(t)), lo=lo, hi=hi) * env


def riser(dur, f0=180, f1=1400):
    t = tvec(dur)
    u = t / dur
    noise = fft_filter(rng.standard_normal(len(t)), lo=2500) * u ** 3
    f = f0 * (f1 / f0) ** u
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 2 * 0.35
    return noise + tone


def pluck(m, dur=0.35, decay=0.09, bright=4000):
    t = tvec(dur)
    f = hz(m)
    s = 0.6 * np.sign(np.sin(2 * np.pi * f * t)) + 0.6 * saw(f * 1.004, t)
    return fft_filter(s, hi=bright) * np.exp(-t / decay) * (1 - np.exp(-t / 0.002))


def blip(f0, f1, dur=0.12):
    t = tvec(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (dur / 3))


def glitch(dur=0.07):
    t = tvec(dur)
    step = rng.integers(20, 120)
    sq = np.sign(np.sin(2 * np.pi * rng.uniform(300, 2500) * t))
    crushed = np.repeat(rng.standard_normal(len(t) // step + 1), step)[: len(t)]
    return (0.5 * sq + 0.6 * crushed) * np.exp(-t / 0.03)


def supersaw(notes, dur, cutoff=2400, voices=5, detune=0.012):
    t = tvec(dur)
    l = np.zeros(len(t))
    r = np.zeros(len(t))
    for m in notes:
        for v in range(voices):
            d = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune
            s = saw(hz(m) * (1 + d), t, rng.random())
            pan = (v / (voices - 1)) * 2 - 1
            l += s * (1 - pan) / 2
            r += s * (1 + pan) / 2
    return fft_filter(l, hi=cutoff), fft_filter(r, hi=cutoff)


# ── arrangement ──────────────────────────────────────────────────────────────
CHORDS = [  # (bass root, pad voicing) per bar
    (33, [57, 60, 64, 69]),  # Am
    (29, [53, 57, 60, 65]),  # F
    (36, [55, 60, 64, 67]),  # C
    (31, [55, 59, 62, 67]),  # G
    (33, [57, 60, 64, 69]),  # Am
    (29, [53, 57, 60, 65]),  # F
    (28, [56, 59, 64, 68]),  # E
    (33, [57, 60, 64, 69, 72]),  # Am (final)
]
bar_t = lambda b: b * BAR

# Bar 0 — intro: pad swell, pop, stretch whoosh, split, shimmer, riser into iris
l, r = supersaw(CHORDS[0][1], BAR, cutoff=900)
sw = np.linspace(0, 1, len(l)) ** 1.5
add_st(l * sw, r * sw, 0, 0.05, send=0.6)
add(blip(300, 1400, 0.16), 0.02, 0.45, send=0.4)
add(whoosh(0.5, 300, 3000), 0.22, 0.35, pan=-0.3)
add(blip(900, 120, 0.25), 0.62, 0.3, send=0.3)
for i, m in enumerate([76, 79, 81, 84, 88, 91]):
    add(pluck(m, 0.4, 0.12, 6000), 0.66 + i * 0.035, 0.12, pan=(i - 2.5) / 3, send=0.7)
add(riser(0.9, 200, 1600), BAR - 0.9, 0.28)
add(whoosh(0.5, 800, 7000), BAR - 0.45, 0.35, pan=0.3)

# Bars 1–6 — groove
kicks = []
for b in range(4, 28):
    t0 = b * B
    bar = b // 4
    if bar == 3 and b % 4 == 3:  # warp beat — drop kick for tension
        continue
    add(kick(), t0, 0.9)
    kicks.append(t0)
    if b % 4 in (1, 3) and bar in (2, 4, 5):
        add(clap(), t0, 0.45, send=0.35)
    add(hat(0.12, 0.05), t0 + B / 2, 0.22, pan=0.25)
    if bar in (4, 5, 6):
        for s in (1, 3):
            add(hat(0.06, 0.018), t0 + s * B / 4, 0.1, pan=-0.3)

# sidechain envelope from kicks
t_all = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    m = t_all >= k
    duck[m] = np.minimum(duck[m], 1 - 0.75 * np.exp(-(t_all[m] - k) / 0.13))

pad_l = np.zeros(N)
pad_r = np.zeros(N)
bass = np.zeros(N)
for bar in range(1, 7):
    root, notes = CHORDS[bar]
    cut = {1: 1500, 2: 1800, 3: 2000, 4: 3200, 5: 3000, 6: 3600}[bar]
    l, r = supersaw(notes, BAR + 0.02, cutoff=cut)
    i = int(bar_t(bar) * SR)
    n = min(len(l), N - i)
    pad_l[i : i + n] += l[:n]
    pad_r[i : i + n] += r[:n]
    for e in range(8):  # 8th-note octave bass
        t = tvec(B / 2)
        f = hz(root + (12 if e % 2 else 0))
        s = fft_filter(saw(f, t) + 0.6 * np.sin(2 * np.pi * f * t), hi=700 if bar < 4 else 1100)
        s *= np.exp(-t / 0.18) * (1 - np.exp(-t / 0.003))
        j = int((bar_t(bar) + e * B / 2) * SR)
        bass[j : j + len(s)] += s[: N - j]
L += pad_l * duck * 0.055
R += pad_r * duck * 0.055
VERB[0] += pad_l * duck * 0.02
VERB[1] += pad_r * duck * 0.02
L += bass * duck * 0.32
R += bass * duck * 0.32

# Bar 1 — FORM: impact + morph blips on each beat
add(impact(), bar_t(1), 0.55, send=0.5)
for k, m in enumerate([72, 76, 79, 84]):
    add(blip(hz(m) * 0.5, hz(m), 0.14), bar_t(1) + k * B, 0.28, pan=(k - 1.5) / 2, send=0.4)
add(whoosh(0.4, 200, 2500), bar_t(2) - 0.4, 0.4)

# Bar 2 — TYPE: slam + slice whooshes
add(impact(1.6), bar_t(2), 0.6, send=0.4)
for k in range(1, 4):
    add(whoosh(0.16, 1000, 8000), bar_t(2) + k * B - 0.12, 0.35, pan=(-1) ** k * 0.5)
for k in range(8):  # rhythm word: 16th ticks
    add(blip(2400, 1800, 0.04), bar_t(2) + 2 * B + k * B / 4, 0.12, pan=(k % 2) * 0.6 - 0.3)

# Bar 3 — PARTICLES: shimmer arp, explosion, warp riser
for s in range(16):
    root, notes = CHORDS[3]
    add(pluck(notes[s % 4] + 12 + (12 if s % 8 >= 4 else 0), 0.3, 0.07, 7000), bar_t(3) + s * B / 4, 0.1, pan=np.sin(s) * 0.7, send=0.6)
add(impact(), bar_t(3) + 2 * B, 0.75, send=0.6)
add(riser(BAR - 2 * B, 300, 3000), bar_t(3) + 2 * B, 0.45)
for s in range(8):  # snare roll into the drop
    add(snare(), bar_t(3) + 2 * B + s * B / 4, 0.12 + 0.05 * s, send=0.3)

# Bar 4 — DIMENSION: drop
add(impact(), bar_t(4), 0.6, send=0.5)
for s in range(32):
    root, notes = CHORDS[4 + s // 16]
    add(pluck(notes[(s * 3) % len(notes)] + 12, 0.25, 0.06, 5000), bar_t(4) + s * B / 4, 0.09, pan=((s % 4) - 1.5) / 2, send=0.35)

# Bar 5 — DATA: counter ticks
for s in range(24):
    add(blip(3200, 3000, 0.03), bar_t(5) + 0.2 + s * B / 8, 0.05, pan=0.6 * np.sin(s * 1.3))

# Bar 6 — MONTAGE: stabs + glitches on every cut, power-down at the end
root, notes = CHORDS[6]
for k in range(8):
    t0 = bar_t(6) + k * B / 2
    l, r = supersaw([n + 12 for n in notes[:3]], 0.22, cutoff=5000, voices=3)
    env = np.exp(-tvec(0.22) / 0.07)
    add_st(l * env, r * env, t0, 0.06, send=0.3)
    add(glitch(), t0, 0.22, pan=rng.uniform(-0.7, 0.7))
add(impact(1.4), bar_t(6), 0.5, send=0.3)
add(riser(BAR - 0.2, 200, 2400), bar_t(6), 0.3)
pd = tvec(0.2)
add(saw(400 * (0.08 ** (pd / 0.2)), pd) * np.exp(-pd / 0.12) * 0.5, bar_t(7) - 0.2, 0.4)

# Bar 7 — END CARD: CRT zap, final hit, ringing chord, logo sparkles
add(blip(80, 2600, 0.14), bar_t(7), 0.3)
add(impact(3.0), bar_t(7) + 0.3, 0.85, send=0.7)
add(kick(), bar_t(7) + 0.3, 0.8)
l, r = supersaw(CHORDS[7][1], 1.6, cutoff=3000)
env = np.exp(-tvec(1.6) / 0.8)
add_st(l * env, r * env, bar_t(7) + 0.3, 0.07, send=0.8)
for i in range(8):
    add(pluck(81 + [0, 3, 7, 12, 15, 19, 24, 27][i], 0.5, 0.15, 8000), bar_t(7) + 0.42 + i * 0.03, 0.07, pan=(i - 3.5) / 4, send=0.8)
add(blip(500, 1500, 0.1), bar_t(7) + 0.95, 0.15, send=0.5)

# ── reverb (convolution with decaying noise), master ─────────────────────────
irt = tvec(2.2)
for ch in range(2):
    ir = rng.standard_normal(len(irt)) * np.exp(-irt / 0.55)
    ir = fft_filter(ir, lo=200, hi=6000)
    ir /= np.sqrt(np.sum(ir ** 2))
    n = N + len(ir)
    wet = np.fft.irfft(np.fft.rfft(VERB[ch], n) * np.fft.rfft(ir, n), n)[:N]
    (L if ch == 0 else R)[:] += wet * 0.5

mix = np.vstack([fft_filter(L, lo=28), fft_filter(R, lo=28)])
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.6)  # gentle soft-clip from a known level
mix /= np.max(np.abs(mix)) / 0.89
fade_in = np.minimum(1, np.arange(N) / (0.005 * SR))
fade_out = np.minimum(1, (N - np.arange(N)) / (0.3 * SR))
mix *= fade_in * fade_out

with wave.open("soundtrack.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype(np.int16).tobytes())
print("soundtrack.wav written", mix.shape)
