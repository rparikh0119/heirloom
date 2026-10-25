"""How voice memories sound when Heirloom plays them back (D33, D69).

It's always the real person's recording, never a voice of its own. Played back, it sounds like it's
coming through the droid's small speaker: warm, a little robotic, clearly them. Think R2-D2 playing
Leia's message. A soft chirp before and after frames it, so the droid presents the memory rather
than pretending to be the person.

The original recording is kept untouched in the cartridge. This is only applied on playback.

Three strengths to choose between by ear (python scripts/voice_styles.py makes all three from your
latest recording). The chosen one is STYLE below.
"""
from __future__ import annotations

import numpy as np

STYLE = "heirloom"   # between radio and transmission, no buzz (Riya, Oct 25: transmission sounded like a zombie)

# The Quest mic records at 16 kHz, so anything gentler than "radio" sounded the same as the original.
# The buzz (ring modulation) is what made "transmission" sound like a corpse. Keep it out of the default.
STYLES = {
    #               low cut  high cut  body ring (Hz, amount)  metal (ms, amount)  crunch (bits, rate)  buzz (Hz, mix)  warmth
    "radio":        dict(low=250, high=4500, ring=(1900, 0.6), metal=(2.4, 0.22), bits=8, rate=11025, buzz=(0, 0.0), warmth=0.9),
    "heirloom":     dict(low=280, high=4000, ring=(1800, 0.75), metal=(2.2, 0.27), bits=7, rate=9600, buzz=(0, 0.0), warmth=1.05),
    "transmission": dict(low=320, high=3600, ring=(1700, 0.9), metal=(2.0, 0.32), bits=6, rate=8000, buzz=(70, 0.18), warmth=1.2),
}


def tape(samples: np.ndarray, sr: int, seed: int | None = None, style: str | None = None) -> np.ndarray:
    """Float samples in -1..1 in, the droid-speaker version out (same length, same rate)."""
    p = STYLES[style or STYLE]
    x = np.asarray(samples, dtype=np.float64)
    n = len(x)
    if n == 0:
        return x.astype(np.float32)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak

    # Small speaker: thinner lows, softer top, and a gentle resonance from its little body.
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / sr)
    shape = 1 / np.sqrt(1 + (p["low"] / np.maximum(f, 1)) ** 4) / np.sqrt(1 + (f / p["high"]) ** 4)
    ring_hz, ring_amt = p["ring"]
    shape = shape * (1 + ring_amt * np.exp(-0.5 * ((f - ring_hz) / (ring_hz * 0.25)) ** 2))
    x = np.fft.irfft(spec * shape, n)

    # A faint metallic shimmer: the sound bouncing once inside a small metal shell.
    ms, amt = p["metal"]
    if amt > 0:
        d = int(sr * ms / 1000)
        x = x + amt * np.concatenate([np.zeros(d), x[:-d]])

    # A light digital crunch, like an old answering machine (fewer bits, lower sample rate).
    if p["rate"] and p["rate"] < sr:
        step = sr / p["rate"]
        held = np.floor(np.arange(n) / step) * step
        x = np.interp(held, np.arange(n), x)
        x = np.convolve(x, np.ones(3) / 3, mode="same")          # soften the steps so it stays warm
    if p["bits"]:
        levels = 2 ** (p["bits"] - 1)
        x = np.round(x * levels) / levels

    # A faint robotic buzz under the voice (ring modulation, mixed low so it stays them).
    buzz_hz, mix = p["buzz"]
    if mix > 0:
        t = np.arange(n) / sr
        x = (1 - mix) * x + mix * x * np.sin(2 * np.pi * buzz_hz * t) * 1.6

    # Warmth: rounds the peaks a little.
    if p["warmth"] > 0:
        x = np.tanh(p["warmth"] * x) / np.tanh(p["warmth"])
    return (0.8 * x / (np.max(np.abs(x)) or 1.0)).astype(np.float32)


def framed(clip: np.ndarray, sr: int) -> np.ndarray:
    """A soft chirp, the memory, a soft chirp. The droid presents the recording (D69)."""
    from .chirps import SR as CHIRP_SR, render

    def at_rate(name):
        c = render(name, variation=0.03) * 0.45
        return np.interp(np.arange(0, len(c), CHIRP_SR / sr), np.arange(len(c)), c).astype(np.float32)

    gap = np.zeros(int(0.2 * sr), dtype=np.float32)
    return np.concatenate([at_rate("listen"), gap, clip.astype(np.float32), gap, at_rate("saved")])
