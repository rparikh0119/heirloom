"""Procedural R2-style chirps. Every body plays the same sounds because the brain makes them.

A chirp is a short sequence of tones that glide in pitch. Each play is slightly different
(random pitch and speed), so it sounds alive rather than like a recording.
"""
from __future__ import annotations

import io
import random
import wave

import numpy as np

SR = 22050  # samples per second


def tone(f0: float, f1: float, dur: float, shape: str = "sine", wobble: float = 0.0,
         wobble_hz: float = 0.0, amp: float = 0.5) -> np.ndarray:
    """One note gliding from f0 to f1 Hz over dur seconds."""
    n = max(1, int(SR * dur))
    t = np.arange(n) / SR
    freq = np.geomspace(f0, f1, n)
    if wobble:
        freq = freq * (1 + wobble * np.sin(2 * np.pi * wobble_hz * t))
    phase = 2 * np.pi * np.cumsum(freq) / SR
    wave_ = np.sin(phase)
    if shape == "square":   # buzzier, more "robot"
        wave_ = 0.6 * np.tanh(4 * wave_) + 0.4 * wave_
    env = np.ones(n)
    a, r = min(n, int(0.005 * SR)), min(n, int(0.02 * SR))
    env[:a] = np.linspace(0, 1, a)
    env[n - r:] = np.linspace(1, 0, r)
    return amp * wave_ * env


def rest(dur: float) -> np.ndarray:
    return np.zeros(int(SR * dur))


# Each recipe takes p (pitch scale) and s (speed scale) so every play varies a little.
CHIRPS = {
    "hello":   lambda p, s: [tone(900 * p, 1800 * p, .08 * s), rest(.03 * s),
                             tone(1400 * p, 2600 * p, .14 * s, wobble=.05, wobble_hz=30)],
    "happy":   lambda p, s: sum(([tone((1100 + 220 * i) * p, (1700 + 320 * i) * p, .06 * s), rest(.025 * s)]
                                 for i in range(4)), []),
    "curious": lambda p, s: [tone(700 * p, 1500 * p, .18 * s), rest(.05 * s), tone(1500 * p, 1150 * p, .1 * s)],
    "sad":     lambda p, s: [tone(1200 * p, 480 * p, .4 * s, wobble=.03, wobble_hz=7)],
    "no":      lambda p, s: [tone(520 * p, 420 * p, .12 * s, "square", amp=.35), rest(.05 * s),
                             tone(470 * p, 360 * p, .16 * s, "square", amp=.35)],
    "sleepy":  lambda p, s: [tone(900 * p, 280 * p, .7 * s, wobble=.08, wobble_hz=5, amp=.4)],
    "wake":    lambda p, s: [tone(300 * p, 1250 * p, .28 * s), tone(1250 * p, 2100 * p, .09 * s)],
    "notice":  lambda p, s: [tone(1300 * p, 1900 * p, .07 * s, amp=.35)],
    "love":    lambda p, s: [tone(650 * p, 1050 * p, .2 * s, wobble=.02, wobble_hz=6, amp=.4), rest(.05 * s),
                             tone(1050 * p, 780 * p, .32 * s, wobble=.03, wobble_hz=6, amp=.4), rest(.06 * s),
                             tone(1400 * p, 1700 * p, .05 * s, amp=.25), tone(1700 * p, 1500 * p, .05 * s, amp=.25)],
    "listen":  lambda p, s: [tone(1000 * p, 1600 * p, .06 * s, amp=.35), rest(.02 * s),
                             tone(1600 * p, 2200 * p, .05 * s, amp=.3)],
    "remember": lambda p, s: [tone(700 * p, 1100 * p, .16 * s, wobble=.02, wobble_hz=5, amp=.35), rest(.05 * s),
                              tone(1100 * p, 900 * p, .22 * s, wobble=.02, wobble_hz=5, amp=.3), rest(.06 * s),
                              tone(900 * p, 1350 * p, .3 * s, wobble=.03, wobble_hz=4, amp=.3)],
    "saved":   lambda p, s: [tone(1200 * p, 1500 * p, .05 * s, amp=.3), rest(.04 * s),
                             tone(1500 * p, 1500 * p, .05 * s, amp=.3), rest(.04 * s),
                             tone(1800 * p, 2300 * p, .09 * s, amp=.3)],
    "tick":    lambda p, s: [tone(1700 * p, 1700 * p, .045 * s, amp=.3)],
    "shutter": lambda p, s: [tone(2400 * p, 900 * p, .05 * s, "square", amp=.25), rest(.03 * s),
                             tone(1300 * p, 1900 * p, .09 * s, amp=.35)],
    "grumble": lambda p, s: [tone(420 * p, 260 * p, .22 * s, "square", wobble=.12, wobble_hz=28, amp=.4),
                             rest(.04 * s),
                             tone(300 * p, 170 * p, .38 * s, "square", wobble=.18, wobble_hz=18, amp=.4)],
}


def render(name: str, variation: float = 0.08) -> np.ndarray:
    """Make a fresh take of a chirp as float samples in -1..1."""
    p = 1 + random.uniform(-variation, variation)
    s = 1 + random.uniform(-variation, variation)
    parts = CHIRPS[name](p, s)
    return np.clip(np.concatenate(parts), -1, 1)


def to_wav_bytes(samples: np.ndarray, sr: int = SR) -> bytes:
    """16-bit mono WAV, readable by Unity, a browser, or the droid's speaker."""
    pcm = (samples * 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)
    return buf.getvalue()
