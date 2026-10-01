"""Opt-in research encoder; no change to canonical O2 or native input."""
from pathlib import Path
import sys
from time import perf_counter_ns
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'vendor' / 'observation_tiles'))
from tile_transport import Encoder, Decoder, Frame, TILE, packet


class DenseEncoder(Encoder):
    """Detect every dirty tile first; when all are dirty, keep the full packet.

    Exact decoded pixels are preserved. Minimum-wire choice is NOT preserved.
    For non-dense updates, tile ordering, compression and tie rules are unchanged.
    """
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
            meta['kind'] = 'unchanged'
            wire = packet(meta, b'')
        else:
            meta['kind'] = 'full'
            wire = packet(meta, frame.pixels)
            if compatible and self.strategy == 'O2':
                shape = (frame.height, frame.width, {'RGB': 3, 'RGBA': 4, 'L': 1}[frame.mode])
                a = np.frombuffer(old.pixels, np.uint8).reshape(shape)
                b = np.frombuffer(frame.pixels, np.uint8).reshape(shape)
                dirty = []
                size = self.tile_size
                total = 0
                for y in range(0, frame.height, size):
                    for x in range(0, frame.width, size):
                        total += 1
                        if not np.array_equal(b[y:y+size, x:x+size], a[y:y+size, x:x+size]):
                            dirty.append((x, y))
                changed = len(dirty)
                if changed < total:
                    pieces = []
                    for x, y in dirty:
                        tile = b[y:y+size, x:x+size]
                        h, w = tile.shape[:2]
                        pieces.extend((TILE.pack(x, y, w, h), np.ascontiguousarray(tile).tobytes()))
                    tile_meta = dict(meta, kind='tiles', count=changed)
                    alternative = packet(tile_meta, b''.join(pieces))
                    if len(alternative) < len(wire):
                        wire, meta = alternative, tile_meta
        self.previous, self.sequence = frame, seq
        self.last = dict(kind=meta['kind'], wire_bytes=len(wire),
                         changed_tiles=changed, encode_ns=perf_counter_ns()-start)
        return wire
