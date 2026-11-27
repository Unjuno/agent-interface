"""Health and ammunition status numbers from exact Freedoom X11 frames."""
from doom_hud_signal_v1 import DoomStatusNumberReader as HealthReader


ANCHORS = {"ammo": (10, 411), "health": (102, 411)}


class DoomStatusNumberReader(HealthReader):
    """Extend the hash-bound v1 glyph reader to the adjacent ammo number."""

    def __init__(self, wad_path, signal_id="health", local_anchor=None, **kwargs):
        if signal_id not in ANCHORS:
            raise ValueError("validated health or ammo signal_id required")
        expected_anchor = ANCHORS[signal_id]
        if local_anchor is not None and local_anchor != expected_anchor:
            raise ValueError("frozen signal-specific HUD anchor required")
        super().__init__(wad_path, signal_id="health",
                         local_anchor=expected_anchor, **kwargs)
        self.signal_id = signal_id
