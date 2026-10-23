"""Offline voice listener. Talk to it when it has noticed you, or say "Heirloom" from further away.

When you're close enough that it notices you (run.py sets `addressed`), commands work without the
wake word, the way you'd just say "hi" to someone who's looking at you (D61). From further away,
"Heirloom" first, then a command within a few seconds.

It reacts while you're still talking when the phrase can't mean anything else ("hi" right away,
"good" waits a beat in case it's "good night"). Otherwise it waits for the pause at the end.

Runs on its own thread. Nothing leaves the computer: Vosk does speech recognition locally,
and it is limited to the phrases in intents.py, which keeps it fast and hard to fool.

The brain reads events with pop_events(), the same way it reads events from Unity:
    "listen"        the wake word was heard (Heirloom perks up)
    "good", "wave"  ...any event from intents.INTENTS

Needs:  python -m pip install -e .[voice]
The speech model (~40 MB) downloads automatically the first time.
"""
from __future__ import annotations

import json
import queue
import threading
import time
from collections import deque

from .intents import WAKE_WORDS, all_phrases, can_act_early, match

MODEL_NAME = "vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
LISTEN_SECONDS = 5.0
BLOCK = 1600          # samples per read: 0.1 s, so it notices you've spoken sooner
SETTLE = 2            # an early guess must stay the same for this many reads before it acts
DEDUPE_SECONDS = 1.5  # after acting early, the same command is ignored this long (the end of the word)


class VoiceListener:
    def __init__(self, mic: int | None = None, listen_seconds: float = LISTEN_SECONDS,
                 require_wake_word: bool = True) -> None:
        self.mic = mic
        self.listen_seconds = listen_seconds
        self.require_wake_word = require_wake_word
        self._events: deque[str] = deque(maxlen=20)
        self._lock = threading.Lock()
        self._audio: queue.Queue[bytes] = queue.Queue()
        self._listen_until = 0.0
        self._stop = threading.Event()
        self.last_heard = ""
        self.addressed = False      # set every tick by run.py: True while it has noticed you (close by)
        self._guess, self._guess_count = "", 0
        self._early_event, self._early_until = None, 0.0

    # ---------- public ----------
    def start(self) -> "VoiceListener":
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)  # hide Kaldi's chatter
        print(f"[voice] loading {MODEL_NAME} (downloads once, ~40 MB)...")
        model = Model(model_name=MODEL_NAME, lang="en-us")
        self._warn_missing_words(model)

        # Only these phrases (plus "[unk]" for everything else) can ever be recognised.
        grammar = json.dumps(all_phrases() + ["[unk]"])
        self._rec = KaldiRecognizer(model, SAMPLE_RATE, grammar)

        self._stream = sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK, dtype="int16",
                                         channels=1, device=self.mic, callback=self._on_audio)
        self._stream.start()
        name = sd.query_devices(self.mic, "input")["name"]
        print(f"[voice] listening on: {name}. Up close just talk. From further away say \"{WAKE_WORDS[0]}\" first.")
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
        self._audio.put(bytes(indata))   # runs on the audio thread, so keep it tiny

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                chunk = self._audio.get(timeout=0.5)
            except queue.Empty:
                continue
            if self._rec.AcceptWaveform(chunk):   # True when a phrase just ended (a pause)
                text = json.loads(self._rec.Result()).get("text", "").replace("[unk]", "").strip()
                self._guess, self._guess_count = "", 0
                if text and not self._just_did(text):
                    self._heard(text)
            else:                                 # still talking: act now if it can't mean anything else
                text = json.loads(self._rec.PartialResult()).get("partial", "").replace("[unk]", "").strip()
                self._guess_count = self._guess_count + 1 if text and text == self._guess else 1
                self._guess = text
                if (text and self._guess_count >= SETTLE and can_act_early(text)
                        and self._would_act(text) and not self._just_did(text)):
                    self._heard(text, early=True)
                    self._early_event, self._early_until = match(text)[1], time.monotonic() + DEDUPE_SECONDS
                    self._rec.Reset()             # start fresh, so the end of the sentence doesn't fire it twice

    def _just_did(self, text: str) -> bool:
        """The same command it just acted on early, still arriving (the tail of the word, or the final result)."""
        return match(text)[1] == self._early_event and time.monotonic() < self._early_until

    def _would_act(self, text: str) -> bool:
        woke, event = match(text)
        return bool(event) and (woke or self.listening or self.addressed or not self.require_wake_word)

    def _heard(self, text: str, early: bool = False) -> None:
        self.last_heard = text
        woke, event = match(text)
        open_window = self.listening or self.addressed or not self.require_wake_word

        if woke and event:                 # "Heirloom, good job" in one breath
            self._emit(event)
            self._listen_until = 0.0
            tag = event
        elif woke:                         # just the name: perk up and wait
            self._emit("listen")
            self._listen_until = time.monotonic() + self.listen_seconds
            tag = "listen"
        elif event and open_window:        # command inside the listening window
            self._emit(event)
            self._listen_until = 0.0
            tag = event
        elif event:
            tag = f"ignored (would be {event}, but you're too far away. Say its name or come closer)"
        else:
            tag = "ignored"
        print(f"[voice] heard \"{text}\" -> {tag}" + ("  (early)" if early else ""))

    def _emit(self, event: str) -> None:
        with self._lock:
            self._events.append(event)

    @staticmethod
    def _warn_missing_words(model) -> None:
        missing = sorted({w for p in all_phrases() for w in p.split()
                          if model.vosk_model_find_word(w) == -1})
        if missing:
            print(f"[voice] WARNING: not in the speech model's vocabulary, will never be heard: {missing}")
