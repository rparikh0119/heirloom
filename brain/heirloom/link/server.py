"""WebSocket server that streams Heirloom state to Unity (or any client).

Protocol v0, brain -> client, JSON text frames:
    {"type": "pose", "ch": {"head_pitch": 0.0, ...all channels...}}
"""
from __future__ import annotations

import json
import threading
import time

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

    def broadcast(self, msg: dict) -> None:
        data = json.dumps(msg)
        self._latest = data
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
            for _ in ws:  # incoming messages are ignored in v0
                pass
        except Exception:
            pass
        finally:
            with self._lock:
                self._clients.discard(ws)
            print("[link] client disconnected")
