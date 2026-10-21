"""The cartridge core: the binder that holds everything Heirloom has learned (docs/cartridge-format.md).

A cartridge is a folder. Move it to another body and the wear moves with it (Rule 6).

    cartridge/
      cartridge.json      version, droid id, the list of layers (one per owner, oldest first)
      layers/L1/          one folder per layer. Each wear plug-in owns one file in here
      history.json        every handoff, and every body it has run in

The core only knows about layers. It never looks inside a plug-in's file (dials.json, patina.json...).
Plug-ins read and write their own file with read_page() and write_page().

Rules it follows:
    - Unknown files and unknown fields are kept untouched, so old and new brains can share cartridges.
    - A missing page means "nothing learned yet", never an error.
    - Exactly one layer is active: the current owner's.
    - Mistakes stop with a message naming the file and field, like reactions.py.
"""
from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

FORMAT_VERSION = 1

# How much each layer's wear counts (D47). "fade" starts at 0.5 and shrinks to 0 over FADE_DAYS.
WEIGHTS = {"active": 1.0, "keep": 1.0, "blend": 0.5, "fade": 0.5}
FADE_DAYS = 56                       # about 8 weeks (open call in the doc)
MEMORIES = ("open", "on_request")    # on_request = "rested": its memories only come back when asked (D45)
SOURCES = ("lived", "simulated")     # simulated layers come from the time skip (D46)

LAYER_KEYS = {"id", "label", "since", "until", "source", "weight", "memories", "fade_from"}


class CartridgeError(ValueError):
    pass


def _today(on: date | None) -> date:
    return on or date.today()


def _parse_day(text: str, where: str) -> date:
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        raise CartridgeError(f"{where}: {text!r} is not a date like 2026-10-21") from None


def _write_json(path: Path, data: dict) -> None:
    """Write to a temporary file first, then swap it in. If the drive is pulled mid-save
    (the Oct 19 scare), the old file is still there instead of half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CartridgeError(f"{path.name}: not valid JSON ({e.msg}, line {e.lineno})") from None


# --------------------------------------------------------------------------------------------
# Layers
# --------------------------------------------------------------------------------------------

@dataclass
class Layer:
    """One owner's chapter."""
    id: str
    label: str
    since: str
    until: str | None = None
    source: dict = field(default_factory=lambda: {"type": "lived"})
    weight: str = "active"
    memories: str = "open"
    fade_from: str | None = None                    # the day "fade" was chosen
    extra: dict = field(default_factory=dict)       # fields a newer brain added. Kept as they are

    def weight_now(self, on: date | None = None) -> float:
        """How much this layer's wear counts today, from 0 to 1."""
        w = WEIGHTS[self.weight]
        if self.weight != "fade":
            return w
        start = _parse_day(self.fade_from or self.until or self.since, f"layer {self.id} fade_from")
        days = (_today(on) - start).days
        return max(0.0, w * (1.0 - days / FADE_DAYS))

    def to_dict(self) -> dict:
        d = {"id": self.id, "label": self.label, "since": self.since, "until": self.until,
             "source": self.source, "weight": self.weight, "memories": self.memories}
        if self.fade_from:
            d["fade_from"] = self.fade_from
        return {**d, **self.extra}

    @staticmethod
    def from_dict(raw: dict, where: str) -> "Layer":
        for key in ("id", "label", "since"):
            if key not in raw:
                raise CartridgeError(f"{where}: a layer is missing {key!r}")
        lid = raw["id"]
        layer = Layer(id=lid, label=raw["label"], since=raw["since"], until=raw.get("until"),
                      source=raw.get("source", {"type": "lived"}), weight=raw.get("weight", "keep"),
                      memories=raw.get("memories", "open"), fade_from=raw.get("fade_from"),
                      extra={k: v for k, v in raw.items() if k not in LAYER_KEYS})
        if layer.weight not in WEIGHTS:
            raise CartridgeError(f"{where}: layer {lid} weight {layer.weight!r}. Allowed: {list(WEIGHTS)}")
        if layer.memories not in MEMORIES:
            raise CartridgeError(f"{where}: layer {lid} memories {layer.memories!r}. Allowed: {list(MEMORIES)}")
        if layer.source.get("type") not in SOURCES:
            raise CartridgeError(f"{where}: layer {lid} source type {layer.source.get('type')!r}. Allowed: {list(SOURCES)}")
        _parse_day(layer.since, f"{where}: layer {lid} since")
        if layer.until:
            _parse_day(layer.until, f"{where}: layer {lid} until")
        return layer


# --------------------------------------------------------------------------------------------
# The cartridge
# --------------------------------------------------------------------------------------------

class Cartridge:
    def __init__(self, folder: Path, droid: dict, layers: list[Layer], history: dict,
                 version: int = FORMAT_VERSION, extra: dict | None = None) -> None:
        self.folder = Path(folder)
        self.droid = droid
        self.layers = layers
        self.history = history
        self.version = version
        self.extra = extra or {}          # top-level fields a newer brain added. Kept as they are
        self._batch: dict | None = None   # pages held in memory during batch()

    # ---- making and opening ----

    @classmethod
    def create(cls, folder: Path, label: str = "first home", source: dict | None = None,
               on: date | None = None) -> "Cartridge":
        """A brand new droid's cartridge: one active layer, nothing learned yet."""
        folder = Path(folder)
        if (folder / "cartridge.json").exists():
            raise CartridgeError(f"{folder}: already has a cartridge. Open it instead")
        day = _today(on).isoformat()
        droid = {"id": "hl-" + uuid.uuid4().hex[:4], "born": day}
        first = Layer(id="L1", label=label, since=day, source=source or {"type": "lived"})
        cart = cls(folder, droid, [first], {"handoffs": [], "seated_in": []})
        cart.save()
        return cart

    @classmethod
    def open(cls, folder: Path) -> "Cartridge":
        folder = Path(folder)
        main = folder / "cartridge.json"
        if not main.exists():
            raise CartridgeError(f"{folder}: no cartridge.json here")
        raw = _read_json(main)
        version = raw.get("format_version")
        if not isinstance(version, int):
            raise CartridgeError("cartridge.json: needs a whole-number \"format_version\"")
        layers = [Layer.from_dict(l, "cartridge.json") for l in raw.get("layers", [])]
        hist_path = folder / "history.json"
        history = _read_json(hist_path) if hist_path.exists() else {}
        history.setdefault("handoffs", [])
        history.setdefault("seated_in", [])
        extra = {k: v for k, v in raw.items() if k not in ("format_version", "droid", "layers")}
        cart = cls(folder, raw.get("droid", {}), layers, history, version, extra)
        cart._check()
        return cart

    def _check(self) -> None:
        if not self.layers:
            raise CartridgeError("cartridge.json: has no layers")
        ids = [l.id for l in self.layers]
        if len(ids) != len(set(ids)):
            raise CartridgeError(f"cartridge.json: two layers share an id ({ids})")
        active = [l.id for l in self.layers if l.weight == "active"]
        if len(active) != 1:
            raise CartridgeError(f"cartridge.json: needs exactly one active layer, found {active or 'none'}")

    def save(self) -> None:
        """Writes cartridge.json and history.json. Plug-in pages are saved by write_page()."""
        if self.version > FORMAT_VERSION:
            raise CartridgeError(f"this cartridge is format {self.version}, this brain only knows "
                                 f"{FORMAT_VERSION}. Not saving, so nothing a newer brain wrote is lost")
        self._check()
        data = {"format_version": self.version, "droid": self.droid,
                "layers": [l.to_dict() for l in self.layers], **self.extra}
        _write_json(self.folder / "cartridge.json", data)
        _write_json(self.folder / "history.json", self.history)
        for l in self.layers:
            (self.folder / "layers" / l.id).mkdir(parents=True, exist_ok=True)

    # ---- layers ----

    @property
    def active(self) -> Layer:
        return next(l for l in self.layers if l.weight == "active")

    def layer(self, layer_id: str) -> Layer:
        for l in self.layers:
            if l.id == layer_id:
                return l
        raise CartridgeError(f"no layer called {layer_id!r}. Layers: {[l.id for l in self.layers]}")

    def handoff(self, label: str, choices: dict[str, str] | None = None, source: dict | None = None,
                on: date | None = None) -> Layer:
        """A new owner. The current layer closes, a new active one starts.

        choices: what the new owner picked for each old layer, e.g. {"L1": "keep"} or {"L1": "fade"}.
        Old layers not mentioned default to "keep" (nothing changes unless you choose, Rule 3).
        """
        day = _today(on).isoformat()
        old = self.active
        old.until = day
        old.weight = "keep"
        for lid, weight in (choices or {}).items():
            self.set_weight(lid, weight, on=on)
        n = max(int(l.id[1:]) for l in self.layers if l.id[1:].isdigit()) + 1
        new = Layer(id=f"L{n}", label=label, since=day, source=source or {"type": "lived"})
        self.layers.append(new)
        self.history["handoffs"].append({"from": old.id, "to": new.id, "date": day,
                                         "choices": {l.id: l.weight for l in self.layers if l is not new}})
        self.save()
        return new

    def set_weight(self, layer_id: str, weight: str, on: date | None = None) -> None:
        if weight == "active" or weight not in WEIGHTS:
            raise CartridgeError(f"weight {weight!r}. Choose from: keep, blend, fade")
        l = self.layer(layer_id)
        if l.weight == "active":
            raise CartridgeError(f"{layer_id} is the current owner's layer. A handoff closes it")
        l.weight = weight
        l.fade_from = _today(on).isoformat() if weight == "fade" else None

    def set_memories(self, layer_id: str, memories: str) -> None:
        if memories not in MEMORIES:
            raise CartridgeError(f"memories {memories!r}. Choose from: {', '.join(MEMORIES)}")
        self.layer(layer_id).memories = memories

    def weights(self, on: date | None = None) -> dict[str, float]:
        """How much every layer counts today. Plug-ins use this to blend."""
        return {l.id: l.weight_now(on) for l in self.layers}

    # ---- pages (for plug-ins) ----

    def read_page(self, layer_id: str, name: str) -> dict:
        """A plug-in's file in one layer, e.g. read_page("L1", "patina"). Missing = {} (nothing learned yet)."""
        self.layer(layer_id)
        if self._batch is not None and (layer_id, name) in self._batch:
            return dict(self._batch[(layer_id, name)])
        path = self.folder / "layers" / layer_id / f"{name}.json"
        data = _read_json(path) if path.exists() else {}
        if self._batch is not None:
            self._batch[(layer_id, name)] = data
        return dict(data)

    def write_page(self, layer_id: str, name: str, data: dict) -> None:
        self.layer(layer_id)
        if self._batch is not None:
            self._batch[(layer_id, name)] = dict(data)
            return
        _write_json(self.folder / "layers" / layer_id / f"{name}.json", data)

    @contextmanager
    def batch(self):
        """Hold page changes in memory and write them once at the end.
        The time skip uses this, so 12 years of moments don't mean 100,000 file writes."""
        self._batch = {}
        try:
            yield self
        finally:
            pages, self._batch = self._batch, None
            for (lid, name), data in pages.items():
                if data:
                    _write_json(self.folder / "layers" / lid / f"{name}.json", data)

    # ---- bodies ----

    def seat(self, body: str, when: datetime | None = None) -> None:
        """Log that this cartridge is now running in a body (week 9 transfer proof)."""
        stamp = (when or datetime.now()).isoformat(timespec="minutes")
        self.history["seated_in"].append({"body": body, "from": stamp})
        self.save()

    # ---- self-check ----

    def health(self) -> tuple[bool, str]:
        if self.version > FORMAT_VERSION:
            return False, f"made by a newer brain (format {self.version}). Read only"
        try:
            self._check()
        except CartridgeError as e:
            return False, str(e)
        return True, f"ok, {len(self.layers)} layer(s), active {self.active.id}"
