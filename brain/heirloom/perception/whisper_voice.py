"""Offline voice listener using Whisper (faster-whisper), so it understands ordinary speech (D63).

Works like voice.py from the brain's side (start, stop, pop_events, addressed, listening), but:
  - Whisper hears every word, so "hi", "hey there", "hiya" all land, in any accent it handles.
  - Phrases are matched loosely (intents.EXTRA), and the name can be heard as "heir loom" etc.
  - Nothing leaves the computer. The model downloads once (base.en about 145 MB) and runs on the CPU.

How it hears a sentence:
  1. A simple loudness gate watches the mic. It learns how loud the room is while you're quiet.
  2. When you speak (louder than the room), it records until you've been quiet for END_SILENCE.
  3. That clip goes to Whisper. Low-confidence results are dropped, because Whisper is known to
     "hear" things like "thank you" in noise, which here would be praise for nothing.

Needs:  python -m pip install faster-whisper sounddevice
"""
from __future__ import annotations

import queue
import threading
import time
from collections import deque

import numpy as np

from ..events import Event
from .intents import match, normalize

SAMPLE_RATE = 16000
FRAME = 480                 # 30 ms of audio per frame
LISTEN_SECONDS = 5.0        # after hearing just the name, how long it waits for a command
START_FRAMES = 3            # 90 ms louder than the room = you started talking
END_SILENCE = 0.35          # seconds of quiet = you stopped talking
MAX_SECONDS = 6.0           # never record longer than this in one go
MIN_SECONDS = 0.2           # shorter than this is a click or a bump, not a word
PRE_ROLL = 0.25             # keep this much audio from before it noticed, so the first sound isn't cut off
LOUDER_THAN_ROOM = 3.0      # how much louder than the room's hum counts as speech
FLOOR = 0.004               # quietest level ever treated as the room (so a silent mic doesn't trigger on nothing)

# Whisper is told what it's likely to hear. This nudges it toward the name and the commands.
PROMPT = "Heirloom, hi. Good job. Not now. Go to sleep. Wake up. Come here. Sorry. I love you. Shh."

# Recording a voice memory ("record this"): people pause mid-sentence, so it waits longer.
RECORD_WAIT = 15.0          # seconds it waits for you to start
RECORD_END_SILENCE = 1.5    # seconds of quiet that end a recording
RECORD_MAX = 30.0           # longest recording
RECORD_MIN = 0.5            # shorter than this isn't a memory
UNDERSTAND_MAX_WORDS = 25   # longer than this: a conversation in the room, not something said to the droid


def confident(segments: list) -> bool:
    """Keep only what Whisper is fairly sure was speech. Thresholds follow Whisper's own
    no-speech rule (no_speech_prob > 0.6 and avg_logprob < -1 means silence) plus a stricter
    logprob floor, because a false "thank you" or "no" changes how the droid is treated."""
    if not segments:
        return False
    for s in segments:
        if s.no_speech_prob > 0.6 and s.avg_logprob < -1.0:
            return False
        if s.avg_logprob < -1.2:
            return False
    return True


class Segmenter:
    """Splits a stream of 30 ms frames into utterances, using loudness against the room's hum."""

    def __init__(self) -> None:
        self.end_silence = END_SILENCE
        self.max_seconds = MAX_SECONDS
        self.noise = FLOOR * 2
        self._pre: deque[np.ndarray] = deque(maxlen=int(PRE_ROLL * SAMPLE_RATE / FRAME))
        self._clip: list[np.ndarray] = []
        self._loud_run = 0
        self._quiet = 0.0
        self.talking = False

    def feed(self, frame: np.ndarray) -> np.ndarray | None:
        """Give it one frame (float32, -1..1). Returns a finished utterance, or None."""
        level = float(np.sqrt(np.mean(frame * frame)))
        loud = level > max(FLOOR, self.noise) * LOUDER_THAN_ROOM
        dt = len(frame) / SAMPLE_RATE

        if not self.talking:
            if not loud:   # learn the room slowly, only while nobody's talking
                self.noise = max(FLOOR, 0.98 * self.noise + 0.02 * level)
            self._loud_run = self._loud_run + 1 if loud else 0
            self._pre.append(frame)
            if self._loud_run >= START_FRAMES:
                self.talking, self._clip, self._quiet = True, list(self._pre), 0.0
            return None

        self._clip.append(frame)
        self._quiet = 0.0 if loud else self._quiet + dt
        length = len(self._clip) * FRAME / SAMPLE_RATE
        if self._quiet >= self.end_silence or length >= self.max_seconds:
            clip = np.concatenate(self._clip)
            self.talking, self._clip, self._loud_run = False, [], 0
            self._pre.clear()
            return clip if length - self._quiet >= MIN_SECONDS else None
        return None


class WhisperListener:
    def __init__(self, mic: int | None = None, model: str = "base.en", listen_seconds: float = LISTEN_SECONDS,
                 require_wake_word: bool = True) -> None:
        self.mic = mic
        self.model_name = model
        self.listen_seconds = listen_seconds
        self.require_wake_word = require_wake_word
        self.addressed = False          # set every tick by run.py: True while it has noticed you (close by)
        self.last_heard = ""
        self._events: deque[str] = deque(maxlen=20)
        self._lock = threading.Lock()
        self._audio: queue.Queue[np.ndarray] = queue.Queue()
        self._listen_until = 0.0
        self._stop = threading.Event()
        self._model = None
        self.segmenter = Segmenter()
        self._armed_until = 0.0         # recording a voice memory until this time (or the next sentence)

    # ---------- public ----------
    def start(self) -> "WhisperListener":
        import sounddevice as sd
        from faster_whisper import WhisperModel

        print(f"[voice] loading Whisper {self.model_name} (downloads once)...")
        t = time.perf_counter()
        self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        self._transcribe(np.zeros(SAMPLE_RATE // 2, dtype=np.float32))     # warm up, so the first word isn't slow
        print(f"[voice] Whisper ready in {time.perf_counter() - t:.1f} s")
        self._stream = sd.InputStream(samplerate=SAMPLE_RATE, blocksize=FRAME, dtype="float32",
                                      channels=1, device=self.mic, callback=self._on_audio)
        self._stream.start()
        name = sd.query_devices(self.mic, "input")["name"]
        how = ("Up close just talk. From further away say \"Heirloom\" first." if self.require_wake_word
               else "Just talk to it.")
        print(f"[voice] listening on: {name}. {how}")
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if getattr(self, "_stream", None) is not None:
            self._stream.stop()
            self._stream.close()

    def pop_events(self) -> list[str]:
        with self._lock:
            events = list(self._events)
            self._events.clear()
        return events

    @property
    def listening(self) -> bool:
        return time.monotonic() < self._listen_until

    # ---------- internals ----------
    def _on_audio(self, indata, frames, time_info, status) -> None:
        self._audio.put(indata[:, 0].copy())    # audio thread: keep it tiny

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                frame = self._audio.get(timeout=0.5)
            except queue.Empty:
                continue
            if self._armed_until and time.monotonic() > self._armed_until and not self.segmenter.talking:
                print("[voice] nothing to record, stopped waiting")
                self._disarm()
            was_talking = self.segmenter.talking
            clip = self.segmenter.feed(frame)
            if self.segmenter.talking and not was_talking and (self.addressed or not self.require_wake_word):
                self._emit("hearing")          # you started talking: it perks up before it knows what you said
            if clip is not None:
                self.hear_clip(clip)

    def _transcribe(self, clip: np.ndarray) -> tuple[str, bool]:
        segments, _ = self._model.transcribe(clip, language="en", beam_size=1, without_timestamps=True,
                                             condition_on_previous_text=False, initial_prompt=PROMPT,
                                             hotwords="Heirloom", vad_filter=False)
        segments = list(segments)
        return " ".join(s.text.strip() for s in segments).strip(), confident(segments)

    @property
    def recording(self) -> bool:
        return self._armed_until > 0

    def _arm(self) -> None:
        self._armed_until = time.monotonic() + RECORD_WAIT
        self.segmenter.end_silence, self.segmenter.max_seconds = RECORD_END_SILENCE, RECORD_MAX

    def _disarm(self) -> None:
        self._armed_until = 0.0
        self.segmenter.end_silence, self.segmenter.max_seconds = END_SILENCE, MAX_SECONDS

    def _keep(self, clip: np.ndarray) -> None:
        """The sentence after 'record this' is the memory, not a command."""
        text, _ = self._transcribe(clip)
        self._disarm()
        _, event = match(text, loose=True)
        if event in ("not_now", "scold") and len(normalize(text).split()) <= 3:
            print(f"[voice] heard \"{text}\" -> cancelled the recording")
            self._emit("not_now", text)
            return
        if len(clip) / SAMPLE_RATE < RECORD_MIN:
            print("[voice] too short to keep")
            self._emit("not_now", text)
            return
        print(f"[voice] recorded {len(clip) / SAMPLE_RATE:.1f} s: \"{text}\"")
        self._emit("recorded", text, audio=clip, sr=SAMPLE_RATE)

    def hear_clip(self, clip: np.ndarray) -> None:
        if self.recording:
            self._keep(clip)
            return
        t = time.perf_counter()
        text, sure = self._transcribe(clip)
        took = time.perf_counter() - t
        if not text:
            return
        if not sure:
            print(f"[voice] heard \"{text}\" -> ignored (not confident, probably noise)  [{took:.2f} s]")
            return
        self._heard(text, took)

    def _heard(self, text: str, took: float = 0.0) -> None:
        self.last_heard = text
        woke, event = match(text, loose=True)
        open_window = self.listening or self.addressed or not self.require_wake_word

        if woke and event:
            self._act(event, text)
            tag = event
        elif woke:
            self._emit("listen", text)
            self._listen_until = time.monotonic() + self.listen_seconds
            tag = "listen"
        elif event and open_window:
            self._act(event, text)
            tag = event
        elif event:
            tag = f"ignored (would be {event}, but you're too far away. Say its name or come closer)"
        elif (open_window or woke) and 0 < len(normalize(text).split()) <= UNDERSTAND_MAX_WORDS:
            self._emit("unknown", text)                    # the brain tries learned words and meaning, or asks "huh?"
            tag = "no exact words, asking the brain"
        else:
            tag = "ignored (very long, probably not talking to it)"
        print(f"[voice] heard \"{text}\" -> {tag}  [{took:.2f} s]")

    def _act(self, event: str, text: str) -> None:
        self._emit(event, text)
        self._listen_until = 0.0
        if event == "record":
            self._arm()

    def _emit(self, name: str, said: str = "", **data) -> None:
        """Events carry what was said, so 'play the one about the recipe' can find the right memory."""
        with self._lock:
            self._events.append(Event(name, source="voice", data={"said": said, **data}))
