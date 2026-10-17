"""WebSocket server that streams Heirloom state to Unity (or any client).

Protocol v0, JSON text frames:
    brain -> client   {"type": "pose", "ch": {"head_pitch": 0.0, ...all channels...}}
                      {"type": "state", ...}            (what the brain is doing, for the MR overlay)
                      {"type": "sound", "name": "happy", "wav_b64": "..."}  (16-bit mono WAV)
    client -> brain   {"type": "user", "head": [x, y, z]}  (user's head, metres, robot space)
                      {"type": "event", "name": "wave"}    (gestures, voice commands, buttons)
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque

from websockets.sync.server import serve


class LinkServer:
    _instance: "LinkServer | None" = None

    @classmethod
    def get(cls, host: str = "0.0.0.0", port: int = 8765) -> "LinkServer":
        """One shared server per process."""
        if cls._instance is None:
            cls._instance = cls(host, port)
            cls._instance.start()
        return cls._instance

    def __init__(self, host: str, port: int) -> None:
        self.host, self.port = host, port
        self._clients: set = set()
        self._lock = threading.Lock()
        self._latest: str | None = None
        self._incoming: dict[str, tuple[dict, float]] = {}
        self._events: deque[str] = deque(maxlen=50)
        self._server = None

    def start(self) -> None:
        self._server = serve(self._handler, self.host, self.port)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        print(f"[link] listening on ws://{self.host}:{self.port}")

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server = None
        LinkServer._instance = None

    @property
    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def wait_for_client(self, timeout: float | None = None) -> bool:
        start = time.monotonic()
        while self.client_count == 0:
            if timeout is not None and time.monotonic() - start > timeout:
                return False
            time.sleep(0.1)
        return True

    def latest(self, msg_type: str, max_age: float | None = None) -> dict | None:
        """Newest message of a type received from any client, or None if missing or older than max_age seconds."""
        with self._lock:
            item = self._incoming.get(msg_type)
        if item is None:
            return None
        msg, stamp = item
        if max_age is not None and time.monotonic() - stamp > max_age:
            return None
        return msg

    def pop_events(self) -> list[str]:
        """All event names received since the last call, oldest first."""
        with self._lock:
            events = list(self._events)
            self._events.clear()
        return events

    def broadcast(self, msg: dict) -> None:
        data = json.dumps(msg)
        if msg.get("type") == "pose":
            self._latest = data  # sent to clients as soon as they connect
        with self._lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                ws.send(data)
            except Exception:
                with self._lock:
                    self._clients.discard(ws)

    def _handler(self, ws) -> None:
        with self._lock:
            self._clients.add(ws)
        print("[link] client connected")
        try:
            if self._latest is not None:
                ws.send(self._latest)
            for raw in ws:
                try:
                    msg = json.loads(raw)
                    msg_type = msg.get("type")
                except (ValueError, AttributeError):
                    continue
                if msg_type == "event" and msg.get("name"):
                    with self._lock:
                        self._events.append(msg["name"])
                elif msg_type:
                    with self._lock:
                        self._incoming[msg_type] = (msg, time.monotonic())
        except Exception:
            pass
        finally:
            with self._lock:
                self._clients.discard(ws)
            print("[link] client disconnected")
