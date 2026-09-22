"""Research-only ordered lossless transport; byte counts are NOT model tokens.

O1 sends full frames or exact-repeat references. O2 additionally sends changed
tiles. Both use the same zlib level. O2 selects the smaller actual wire packet
of tiles/full; the extra encoding work is intentionally measured, not hidden.
"""
import json
import struct
import zlib
from time import perf_counter_ns
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "observation_gating"))
from exact_gate import Frame

PREFIX = struct.Struct("!4sI")
TILE = struct.Struct("!IIII")


def packet(meta, payload):
    header = json.dumps(meta, separators=(",", ":"), sort_keys=True).encode()
    return PREFIX.pack(b"AIT1", len(header)) + header + zlib.compress(payload, 1)


class Encoder:
    def __init__(self, stream, strategy="O2", tile_size=64):
        if strategy not in ("O1", "O2") or tile_size <= 0:
            raise ValueError("Invalid strategy or tile size")
        self.stream, self.strategy, self.tile_size = stream, strategy, tile_size
        self.previous, self.sequence = None, 0
        self.last = {}

    def encode(self, frame, *, action_id, observed_ns, context=()):
        start = perf_counter_ns()
        seq = self.sequence + 1
        meta = dict(stream=self.stream, sequence=seq, base=self.sequence,
                    width=frame.width, height=frame.height, mode=frame.mode,
                    action_id=action_id, observed_ns=observed_ns, context=context)
        old = self.previous
        compatible = old is not None and (old.width, old.height, old.mode) == (
            frame.width, frame.height, frame.mode)
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
                pieces = []
                size = self.tile_size
                for y in range(0, frame.height, size):
                    for x in range(0, frame.width, size):
                        tile = b[y:y+size, x:x+size]
                        if not np.array_equal(tile, a[y:y+size, x:x+size]):
                            h, w = tile.shape[:2]
                            pieces.extend((TILE.pack(x, y, w, h), tile.tobytes()))
                            changed += 1
                tile_meta = dict(meta, kind="tiles", count=changed)
                candidate = packet(tile_meta, b"".join(pieces))
                if len(candidate) < len(wire):
                    wire, meta = candidate, tile_meta
        # Commit state only after successful serialization.
        self.previous, self.sequence = frame, seq
        self.last = dict(kind=meta["kind"], wire_bytes=len(wire),
                         changed_tiles=changed, encode_ns=perf_counter_ns()-start)
        return wire


class Decoder:
    """Atomic accept: bad packets never advance sequence or alter the base.

    This local prototype assumes trusted bounded producers. It is not a network
    endpoint or a hardened parser for hostile compressed input.
    """
    def __init__(self, stream):
        self.stream, self.sequence, self.frame = stream, 0, None
        self.metadata = None

    def accept(self, wire):
        magic, size = PREFIX.unpack_from(wire)
        if magic != b"AIT1" or size > len(wire)-PREFIX.size:
            raise ValueError("Invalid packet")
        meta = json.loads(wire[PREFIX.size:PREFIX.size+size])
        if (meta["stream"] != self.stream or meta["sequence"] != self.sequence+1
                or meta["base"] != self.sequence):
            raise ValueError("Stream gap/reorder/wrong base: start a new stream")
        decompressor = zlib.decompressobj()
        data = decompressor.decompress(wire[PREFIX.size+size:])
        if not decompressor.eof or decompressor.unused_data or decompressor.unconsumed_tail:
            raise ValueError("Incomplete or trailing compressed stream")
        width, height, mode = meta["width"], meta["height"], meta["mode"]
        kind = meta["kind"]
        if kind == "full":
            frame = Frame(width, height, mode, data)
        else:
            old = self.frame
            if old is None or (width, height, mode) != (old.width, old.height, old.mode):
                raise ValueError("Missing or incompatible base")
            if kind == "unchanged":
                if data:
                    raise ValueError("Unexpected unchanged payload")
                frame = old
            elif kind == "tiles":
                if type(meta["count"]) is not int or meta["count"] <= 0:
                    raise ValueError("Invalid tile count")
                channels = {"RGB": 3, "RGBA": 4, "L": 1}[mode]
                array = np.frombuffer(old.pixels, np.uint8).reshape(height, width, channels).copy()
                covered = np.zeros((height, width), dtype=bool)
                offset = 0
                for _ in range(meta["count"]):
                    x, y, w, h = TILE.unpack_from(data, offset)
                    offset += TILE.size
                    length = w*h*channels
                    if (w <= 0 or h <= 0 or x+w > width or y+h > height
                            or offset+length > len(data) or covered[y:y+h, x:x+w].any()):
                        raise ValueError("Invalid or overlapping tile")
                    array[y:y+h, x:x+w] = np.frombuffer(data[offset:offset+length], np.uint8).reshape(h,w,channels)
                    covered[y:y+h, x:x+w] = True
                    offset += length
                if offset != len(data):
                    raise ValueError("Trailing tile bytes")
                frame = Frame(width, height, mode, array.tobytes())
            else:
                raise ValueError("Unknown packet kind")
        self.frame, self.sequence, self.metadata = frame, meta["sequence"], meta
        return frame
