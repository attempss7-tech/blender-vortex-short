# make_mix.py — sound mix for the V1 vortex short.
#
# voice.wav (Warm Pebble, as recorded — gain only) + an original gentle
# ambient pad score (ducked under speech) + synthesized aviation SFX
# (wind swells for the stall/peel/climb, metallic ticks for the burr pops,
# a soft chime for the "vortex generators" name moment, low jet rumble
# under the sky shots). Master gain to -14.5 LUFS integrated, look-ahead
# limiter <= -1.2 dBTP, exactly 42.768 s / 48 kHz / stereo / 24-bit.
# Same approach as chicken v3's mix.py; dsp helpers reused from there.
import json
import os
import subprocess
import sys
import time

import numpy as np
from scipy import ndimage, signal

sys.path.insert(0, "/home/hatch/workspace/chicken_short_v3/audio")
from dsp import (SR, ns, st, dbg, rng, read_wav, write_wav, integrated,
                 momentary_max, true_peak, fades, colored, lp, bp,
                 modal, pan, place, widen)  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
DUR = 42.768
N = ns(DUR)
TARGET_LUFS = -14.5
CEIL_DBTP = -1.2
DUCK_DB = -3.0

# SFX event times (seconds, from voice/words.json)
STALL = (10.11, 11.46)        # "stalling" + drop
PEEL = (12.00, 14.85)         # airflow breaks away
BURR_POPS = [18.53 + i * 0.333 for i in range(10)]  # f556+i*10
CLIMB = (33.00, 33.87)        # "steep climbs"
CHIME_T = 35.10               # "vortex generators"
RUMBLE_SPANS = [(7.20, 11.77), (22.33, 25.90), (32.37, 34.37),
                (36.67, 42.77)]


def log(*a):
    print("[%s]" % time.strftime("%H:%M:%S"), *a, flush=True)


def limiter(x, ceil_db=CEIL_DBTP, look=0.003, rel=0.08):
    """4x-oversampled peak detection, look-ahead min filter, release
    one-pole, centred smoothing -> gain curve (from chicken v3 mix.py)."""
    c = dbg(ceil_db)
    n = x.shape[1]
    up = np.abs(signal.resample_poly(x, 4, 1, axis=-1)).max(0)
    pk = np.pad(up, (0, max(0, 4 * n - len(up))))[: 4 * n].reshape(n, 4).max(1)
    gr = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    La = max(1, ns(look))
    g1 = ndimage.minimum_filter1d(gr, 2 * La + 1, mode="nearest")
    g2 = g1.copy()
    idx = np.flatnonzero(g1 < 1.0)
    if len(idx):
        kr = 1 - np.exp(-1 / (rel * SR))
        gap = ns(rel * 8)
        brk = np.flatnonzero(np.diff(idx) > gap)
        starts = np.concatenate([[idx[0]], idx[brk + 1]])
        ends = np.concatenate([idx[brk], [idx[-1]]])
        for a, b_ in zip(starts, ends):
            e = min(n, b_ + gap)
            seg = g1[a:e]
            out = np.empty(len(seg))
            g = 1.0
            for k in range(len(seg)):
                g = min(seg[k], g + (1 - g) * kr)
                out[k] = g
            g2[a:e] = out
    g3 = ndimage.uniform_filter1d(g2, 2 * La + 1, mode="nearest")
    g3 = np.minimum(g3, 1.0)
    return x * g3[None, :], g3


def speech_spans(words, merge=0.3):
    sp = []
    for w in words:
        s, e = float(w["s"]), float(w["e"])
        if sp and s - sp[-1][1] < merge:
            sp[-1][1] = max(sp[-1][1], e)
        else:
            sp.append([s, e])
    return sp


def duck_db(spans, depth=DUCK_DB, pre=0.08, post=0.12, att=0.07, rel=0.45):
    ctrl = 1000
    nc = int(DUR * ctrl) + 2
    va = np.zeros(nc)
    for s, e in spans:
        va[max(0, int((s - pre) * ctrl)): int((e + post) * ctrl)] = 1.0
    ka, kr = 1 - np.exp(-1 / (att * ctrl)), 1 - np.exp(-1 / (rel * ctrl))
    env = np.zeros(nc)
    e = 0.0
    for i in range(nc):
        tgt = va[i]
        e += (tgt - e) * (ka if tgt > e else kr)
        env[i] = e
    return np.interp(np.arange(N) / SR, np.arange(nc) / ctrl, depth * env)


# --------------------------------------------------------------- music

# 8 pad chords, one per ~5.35 s: C - G - Am - F - C - G - F - G
CHORDS = [
    (261.63, 329.63, 392.00),  # C
    (196.00, 246.94, 293.66),  # G
    (220.00, 261.63, 329.63),  # Am
    (174.61, 220.00, 261.63),  # F
    (261.63, 329.63, 392.00),  # C
    (196.00, 246.94, 293.66),  # G
    (174.61, 220.00, 261.63),  # F
    (196.00, 246.94, 293.66),  # G
]


def render_music(r):
    """Slow-attack sine-stack pads with 1 s crossfades + a soft sub root."""
    out = np.zeros(N)
    t = np.arange(N) / SR
    bar = DUR / len(CHORDS)
    for i, chord in enumerate(CHORDS):
        a, b = i * bar, min((i + 1) * bar + 1.0, DUR)
        ia, ib = ns(a), ns(b)
        tt = t[ia:ib] - a
        env = np.ones(ib - ia)
        atk = ns(1.5)
        env[:atk] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(atk) / atk)
        rel = ns(1.0)
        env[-rel:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(rel) / rel)
        sig = np.zeros(ib - ia)
        for f in chord:
            sig += np.sin(2 * np.pi * f * tt)
            sig += 0.25 * np.sin(2 * np.pi * f * 2 * tt + 0.3)
            sig += 0.12 * np.sin(2 * np.pi * f * 3 * tt + 0.7)
        sig += 0.5 * np.sin(2 * np.pi * chord[0] / 2 * tt)  # sub root
        # slow shimmer (beating detune)
        sig *= 1.0 + 0.06 * np.sin(2 * np.pi * 0.11 * tt + i)
        out[ia:ib] += sig * env / len(chord)
    out = lp(out, 2400)
    # gentle stereo width (widen takes MONO and returns stereo)
    return widen(out, r, ms=11.0, amount=0.5)


# --------------------------------------------------------------- sfx

def swell(noise, span, lo, hi, peak=1.0):
    """Bandpassed noise swell over a time span (raised-cosine bump)."""
    a, b = span
    ia, ib = ns(a), ns(b)
    seg = noise[ia:ib]
    seg = bp(seg, lo, hi)
    env = np.sin(np.pi * np.arange(ib - ia) / (ib - ia)) ** 2
    return seg * env * peak


def render_sfx(r):
    sfx = np.zeros((2, N))
    noise = colored(N + SR, r, slope=1.0)
    # wind: stall + peel + climb
    for span, lo, hi, pk in ((STALL, 300, 1400, 0.50),
                             (PEEL, 500, 2200, 0.55),
                             (CLIMB, 400, 1800, 0.60)):
        w = swell(noise, span, lo, hi, pk)
        place(sfx, w, span[0])
    # jet rumble bed under the sky shots (low brown noise, slow fades)
    rumble = lp(colored(N + SR, r, slope=2.0), 160)
    for a, b in RUMBLE_SPANS:
        ia, ib = ns(a), min(ns(b), N)
        env = np.ones(ib - ia)
        f = ns(0.6)
        env[:f] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(f) / f)
        env[-f:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(f) / f)
        sfx[:, ia:ib] += st(rumble[ia:ib] * env * 0.35)
    # burr ticks: 10 metallic pings, alternating pan
    for i, tp in enumerate(BURR_POPS):
        ping = modal(0.25, [(2400, 0.5, 0.06), (3600, 0.3, 0.04),
                            (5200, 0.15, 0.03)], r)
        place(sfx, pan(ping, -0.25 if i % 2 else 0.25), tp, gain=0.8)
    # soft chime on "vortex generators"
    chime = modal(1.6, [(880, 0.4, 0.8), (1320, 0.25, 0.6),
                        (1760, 0.15, 0.4)], r)
    place(sfx, chime, CHIME_T, gain=0.7)
    return sfx


# --------------------------------------------------------------- main

def main():
    t0 = time.time()
    r = rng(20261112)
    words = json.load(open(os.path.join(PROJ, "voice", "words.json")))
    spans = speech_spans(words)
    x, sr = read_wav(os.path.join(PROJ, "voice", "voice.wav"))
    assert sr == SR, sr
    v = x[0] if x.shape[0] == 1 else x.mean(0)
    voice = np.zeros(N)
    voice[: min(N, len(v))] = v[:N]
    voice = st(voice)
    log("voice: %.2f LUFS, TP %.2f dBTP, %d samples"
        % (integrated(voice), true_peak(voice), len(v)))

    m_raw = render_music(r)
    log("music raw: %.2f LUFS" % integrated(m_raw))
    dk = duck_db(spans)
    m_d = m_raw * dbg(dk)[None, :]
    # bed sits 10 LU under the voice (after ducking)
    m_gain = (integrated(voice) - 10.0) - integrated(m_d)
    m = m_d * dbg(m_gain)
    end = ns(DUR - 0.03)
    m[:, end:] *= np.linspace(1, 0, N - end)[None, :]
    log("music: gain %+.1f dB -> %.2f LUFS" % (m_gain, integrated(m)))

    s = render_sfx(r)
    # SFX peaks sit ~12 LU under the voice's loudest moments
    s_target = momentary_max(voice) - 12.0
    s_gain = s_target - momentary_max(s)
    s = s * dbg(s_gain)
    log("sfx: gain %+.1f dB, momentary max %.1f LUFS"
        % (s_gain, momentary_max(s)))

    mix = voice + m + s
    mix, _ = limiter(mix * dbg(TARGET_LUFS - integrated(mix)))
    mix = fades(mix, fin=0.003, fout=0.01)
    log("final: %.2f LUFS, TP %.2f dBTP, %.3f s"
        % (integrated(mix), true_peak(mix), mix.shape[1] / SR))

    assets = os.path.join(PROJ, "assets")
    os.makedirs(assets, exist_ok=True)
    write_wav(os.path.join(assets, "mix.wav"), mix, bits=24)
    # stems at mix gain (sum to the final mix before the limiter)
    g_master = dbg(TARGET_LUFS - integrated(voice + m + s))
    write_wav(os.path.join(assets, "stem_voice.wav"), voice * g_master,
              bits=24)
    write_wav(os.path.join(assets, "stem_music.wav"), m * g_master, bits=24)
    write_wav(os.path.join(assets, "stem_sfx.wav"), s * g_master, bits=24)
    with open(os.path.join(assets, "cues.md"), "w") as f:
        f.write("# V1 mix cues\n\n")
        f.write("Voice: Warm Pebble (avocado_v2:chip, speed 112), as "
                "recorded, gain only. Music: original 8-chord ambient pad "
                "(C-G-Am-F-C-G-F-G), ducked -3 dB under speech, bed -10 LU "
                "vs voice.\n\n")
        f.write("SFX: wind swell stall %.2f-%.2fs; wind swell peel "
                "%.2f-%.2fs; 10 burr ticks %s; climb whoosh %.2f-%.2fs; "
                "chime at %.2fs; jet rumble %s.\n\n"
                % (STALL[0], STALL[1], PEEL[0], PEEL[1],
                   ", ".join("%.2f" % t for t in BURR_POPS),
                   CLIMB[0], CLIMB[1], CHIME_T,
                   ", ".join("%.1f-%.1f" % sp for sp in RUMBLE_SPANS)))
        f.write("Master: %.2f LUFS integrated, TP %.2f dBTP, %.3f s, "
                "48 kHz stereo 24-bit.\n"
                % (integrated(mix), true_peak(mix), mix.shape[1] / SR))
    log("wrote assets/mix.wav (+ stems, cues.md) in %.1fs"
        % (time.time() - t0))


if __name__ == "__main__":
    main()
