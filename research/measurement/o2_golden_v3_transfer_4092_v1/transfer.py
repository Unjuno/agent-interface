"""Research-only exact O2 transfer variants for Issue #4103.

The two encoders differ only in changed-tile materialization. Neither grants
input authority and neither changes AIT1 metadata, zlib settings, or selection.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
from time import perf_counter_ns
import numpy as np

ROOT = Path(os.environ.get("AGENT_INTERFACE_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "research" / "observation_tiles"))
import tile_transport as reference

Frame = reference.Frame
TILE = reference.TILE
packet = reference.packet


def dirty_coordinates(a: np.ndarray, b: np.ndarray, size: int) -> list[tuple[int, int]]:
    height, width, channels = b.shape
    different = np.not_equal(a, b).reshape(height, width * channels)
    horizontal = np.logical_or.reduceat(
        different, np.arange(0, width * channels, size * channels), axis=1
    )
    mask = np.logical_or.reduceat(horizontal, np.arange(0, height, size), axis=0)
    rows, cols = np.nonzero(mask)
    return [(int(x) * size, int(y) * size) for y, x in zip(rows, cols)]


class _Base(reference.Encoder):
    contiguous = False

    def encode(self, frame, *, action_id, observed_ns, context=()):
        start = perf_counter_ns()
        seq = self.sequence + 1
        meta = dict(
            stream=self.stream, sequence=seq, base=self.sequence,
            width=frame.width, height=frame.height, mode=frame.mode,
            action_id=action_id, observed_ns=observed_ns, context=context,
        )
        old = self.previous
        compatible = old is not None and (old.width, old.height, old.mode) == (
            frame.width, frame.height, frame.mode
        )
        changed = 0
        if compatible and old.pixels == frame.pixels:
            meta["kind"] = "unchanged"
            wire = packet(meta, b"")
        else:
            meta["kind"] = "full"
            wire = packet(meta, frame.pixels)
            if compatible and self.strategy == "O2":
                channels = {"RGB": 3, "RGBA": 4, "L": 1}[frame.mode]
                shape = (frame.height, frame.width, channels)
                a = np.frombuffer(old.pixels, np.uint8).reshape(shape)
                b = np.frombuffer(frame.pixels, np.uint8).reshape(shape)
                pieces: list[bytes] = []
                for x, y in dirty_coordinates(a, b, self.tile_size):
                    tile = b[y:y+self.tile_size, x:x+self.tile_size]
                    h, w = tile.shape[:2]
                    raw = np.ascontiguousarray(tile).tobytes() if self.contiguous else tile.tobytes()
                    pieces.extend((TILE.pack(x, y, w, h), raw))
                    changed += 1
                tile_meta = dict(meta, kind="tiles", count=changed)
                candidate = packet(tile_meta, b"".join(pieces))
                if len(candidate) < len(wire):
                    wire, meta = candidate, tile_meta
        self.previous, self.sequence = frame, seq
        self.last = dict(
            kind=meta["kind"], wire_bytes=len(wire), changed_tiles=changed,
            encode_ns=perf_counter_ns() - start,
        )
        return wire


class VectorEncoder(_Base):
    contiguous = False


class ContiguousEncoder(_Base):
    contiguous = True
