#!/usr/bin/env python3
"""Write the JumpCut jam music loop as a WAV by code (stdlib only, deterministic, original, no samples, no AI).

112 BPM, 8 bars (Am F C G, two bars each): kick, off-beat hat, saw bass, soft triad pad, a sparse pluck line.
All envelopes end inside the loop, so the file loops without a click. Usage: synth_music.py OUT.wav            (the loop)
       synth_music.py --stinger OUT.wav  (the 1.1 s CUT stinger: falling saw plus a noise hit)
       synth_music.py --cut OUT.wav      (the 0.32 s player-cut hit: tape snip plus slate clack)
       synth_music.py --sfx OUTDIR       (the five short UI action sounds)
Seed: random.Random(1) in both. Own work, deterministic: the same script and commit give the same bytes.
"""
import math
import random
import struct
import sys
import wave

SR, BPM, BARS = 44100, 112, 8
BEAT = 60.0 / BPM
N = int(round(BARS * 4 * BEAT * SR))
CHORDS = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]  # root MIDI + triad
PLUCK = [0, 7, 12, 7, 15, 12, 7, 3]  # semitones over the chord root, one per 8th in a bar


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def main(out):
    rnd = random.Random(1)
    buf = [0.0] * N

    def add(i, v):
        buf[i % N] += v  # wrap tails round the loop point

    for bar in range(BARS):
        root, triad = CHORDS[bar // 2]
        t0 = bar * 4 * BEAT
        for beat in range(4):  # kick
            s = int((t0 + beat * BEAT) * SR)
            for k in range(int(0.22 * SR)):
                t = k / SR
                add(s + k, 0.9 * math.sin(2 * math.pi * (50 * t + 90 * (1 - math.exp(-t * 28)) / 28 * 1.0)) * math.exp(-t * 16))
        for e in range(8):  # 8th grid
            tt = t0 + e * BEAT / 2
            s = int(tt * SR)
            if e % 2 == 1:  # hat on the off-beat
                for k in range(int(0.05 * SR)):
                    add(s + k, 0.12 * (rnd.random() * 2 - 1) * math.exp(-k / SR * 90))
            f = hz(root - 12)  # bass: saw through a simple one-pole low-pass
            lp, ph = 0.0, 0.0
            for k in range(int(0.24 * SR)):
                ph = (ph + f / SR) % 1.0
                lp += 0.07 * ((2 * ph - 1) - lp)
                add(s + k, 0.5 * lp * math.exp(-k / SR * 6))
            if e % 2 == 0 or e == 7:  # pluck
                fp = hz(root + 12 + PLUCK[e])
                for k in range(int(0.3 * SR)):
                    t = k / SR
                    add(s + k, 0.16 * (math.sin(2 * math.pi * fp * t) + 0.3 * math.sin(4 * math.pi * fp * t)) * math.exp(-t * 9))
        dur = int(4 * BEAT * SR)  # pad: detuned sines with a fade in/out per bar
        for m in triad:
            for d in (-0.4, 0.4):
                fm = hz(m + 12) * 2 ** (d / 1200)
                for k in range(dur):
                    env = min(1.0, k / (0.25 * SR), (dur - k) / (0.25 * SR))
                    add(int(t0 * SR) + k, 0.05 * env * math.sin(2 * math.pi * fm * k / SR))
    peak = max(abs(x) for x in buf) or 1.0
    g = 0.89 / peak
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * g)) * 32767)) for x in buf))
    print(f"wrote {out}: {N / SR:.2f} s, {BPM} BPM, {BARS} bars")


def stinger(out):
    rnd = random.Random(1)
    n = int(1.1 * SR)
    ph, lp, buf = 0.0, 0.0, []
    for k in range(n):
        t = k / SR
        f = 70 + 330 * math.exp(-t * 3.2)  # falling pitch
        ph = (ph + f / SR) % 1.0
        lp += 0.12 * ((2 * ph - 1) - lp)
        noise = (rnd.random() * 2 - 1) * math.exp(-t * 14) * 0.5
        buf.append((0.8 * lp * math.exp(-t * 3.0) + noise) * min(1.0, t / 0.004))
    peak = max(abs(x) for x in buf) or 1.0
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * 0.85 * 32767)) for x in buf))
    print(f"wrote {out}: {n / SR:.2f} s stinger")


def _write(path, buf, gain=0.85):
    peak = max(abs(x) for x in buf) or 1.0
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x / peak * gain * 32767)) for x in buf))


def _tone(freqs, dur, decay, sq=False):
    """Sequence of (freq, start_s) notes, sine (or soft square), exponential decay each."""
    n = int((max(s for _, s in freqs) + dur) * SR) + 2
    buf = [0.0] * n
    for f, t0 in freqs:
        for k in range(int(dur * SR)):
            t = k / SR
            v = math.sin(2 * math.pi * f * t)
            if sq:
                v = 0.6 * v + 0.4 * math.sin(2 * math.pi * 3 * f * t)
            i = int(t0 * SR) + k
            buf[i] += v * math.exp(-t * decay) * min(1.0, t / 0.004)
    return buf


def _bandpass(x, f, q):
    """RBJ biquad band-pass (0 dB peak), direct form I."""
    w0 = 2 * math.pi * f / SR
    al = math.sin(w0) / (2 * q)
    a0 = 1 + al
    b0, b2, a1, a2 = al / a0, -al / a0, -2 * math.cos(w0) / a0, (1 - al) / a0
    y, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
    for v in x:
        o = b0 * v + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, v, y1, o
        y.append(o)
    return y


def cut(out):
    """The player CUT hit (0.32 s): a tape-splice snip, then a wooden slate clack with a short room tail.
    Snip = 3 ms high-passed noise tick; clack (at 45 ms) = sharp noise crack plus three wood resonances
    (1.15, 2.35, 3.9 kHz) and a falling 210->150 Hz body thump; room = four lowpassed early-reflection taps."""
    rnd = random.Random(3)
    n = int(0.32 * SR)
    noise = [rnd.random() * 2 - 1 for _ in range(n)]
    dry = [0.0] * n
    # snip: high-passed noise tick (noise minus a one-pole lowpass of itself)
    lp = 0.0
    for k in range(int(0.004 * SR)):
        lp += 0.35 * (noise[k] - lp)
        dry[k] += 0.4 * (noise[k] - lp) * math.exp(-k / SR * 900)
    t0 = int(0.045 * SR)
    m = n - t0
    exc = [noise[t0 + k] * math.exp(-k / SR * 130) for k in range(m)]
    wood = [0.0] * m
    for f, q, g in ((1150, 6, 1.0), (2350, 8, 0.75), (3900, 5, 0.45)):
        for k, v in enumerate(_bandpass(exc, f, q)):
            wood[k] += g * v
    ph = 0.0
    for k in range(m):
        t = k / SR
        ph += 2 * math.pi * (150 + 60 * math.exp(-t * 60)) / SR
        crack = exc[k] * math.exp(-t * 700) * 0.9
        body = math.sin(ph) * math.exp(-t * 45) * 0.55
        dry[t0 + k] += (3.2 * wood[k] + crack + body) * min(1.0, t / 0.0004)
    buf = dry[:]
    for ms, g in ((17, 0.26), (29, 0.18), (41, 0.12), (53, 0.08)):
        d, lp = int(ms / 1000 * SR), 0.0
        for k in range(d, n):
            lp += 0.3 * (dry[k - d] - lp)
            buf[k] += g * lp
    fade = int(0.03 * SR)
    for k in range(fade):
        buf[n - 1 - k] *= k / fade
    # soft-clip the crack so the body and wood carry: same peak, about 8 dB more loudness
    peak = max(abs(x) for x in buf) or 1.0
    buf = [math.tanh(4.0 * x / peak) for x in buf]
    _write(out, buf, 0.9)
    print(f"wrote {out}: {n / SR:.2f} s cut hit")


def sfx(outdir):
    """Five short action sounds, original synthesis: pause, resume, wrap, no film, shot kept."""
    import os
    os.makedirs(outdir, exist_ok=True)
    _write(f"{outdir}/sfx_pause.wav", _tone([(440, 0.0), (330, 0.09)], 0.25, 9))
    _write(f"{outdir}/sfx_resume.wav", _tone([(330, 0.0), (494, 0.09)], 0.25, 9))
    _write(f"{outdir}/sfx_wrap.wav", _tone([(392, 0.0), (494, 0.14), (587, 0.28), (784, 0.42)], 0.9, 3.2))
    rnd = random.Random(2)
    nf = _tone([(150, 0.0), (120, 0.12)], 0.2, 14, sq=True)
    _write(f"{outdir}/sfx_nofilm.wav", [x + (rnd.random() * 2 - 1) * 0.05 for x in nf])
    _write(f"{outdir}/sfx_keep.wav", _tone([(660, 0.0), (990, 0.07)], 0.3, 10))
    print(f"wrote 5 sfx to {outdir}")


if __name__ == "__main__":
    if sys.argv[1] == "--sfx":
        sfx(sys.argv[2])
    elif sys.argv[1] == "--cut":
        cut(sys.argv[2])
    elif sys.argv[1] == "--stinger":
        stinger(sys.argv[2])
    else:
        main(sys.argv[1])
