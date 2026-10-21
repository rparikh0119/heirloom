"""A wear plug-in: one kind of wear (dials, patina, later dialect). Each owns one page per layer.

The plot test (docs/cartridge-format.md): a kind of wear only belongs here if it changes what
the NEXT owner meets.

To add one, make a new file in this folder with a Wear subclass. The brain finds it by `name`.
It's only used when the brain runs with a cartridge.
"""
from __future__ import annotations


class Wear:
    name = ""        # also the page name: layers/L1/<name>.json

    def attach(self, cartridge, brain) -> None:
        """Called once at startup with the cartridge and the brain."""
        self.cart = cartridge
        for layer in cartridge.layers:
            self.validate(cartridge.read_page(layer.id, self.name), f"layers/{layer.id}/{self.name}.json")

    def record(self, event, mode: str, t: float) -> bool:
        """Something happened. Update the active layer. Return True if anything changed."""
        return False

    def apply(self, brain) -> None:
        """Blend every layer by weight and push the result into the brain."""

    def validate(self, data: dict, where: str) -> None:
        """Check this plug-in's page. Raise ValueError with a clear message if it's wrong."""

    def health(self) -> tuple[bool, str]:
        return True, "ok"
