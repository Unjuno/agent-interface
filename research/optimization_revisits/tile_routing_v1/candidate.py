"""Opt-in research encoder: exact tile coverage selects one AIT1 encoding.

The existing decoder and packet format are unchanged. This is transport only;
no target validity, task relevance, freshness or input authority is inferred.
"""
from pathlib import Path
import sys
from time import perf_counter_ns

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/observation_tiles'))
from tile_transport import Encoder, TILE, packet


class CoverageEncoder(Encoder):
    """Use tiles at <=25% changed tile area; otherwise full, with early exit.

    The threshold is an uncalibrated frozen hypothesis, not a compressed-size
    bound. Existing O2 remains necessary when minimum actual wire size matters.
    """
    def encode(self, frame, *, action_id, observed_ns, context=()):
        start = perf_counter_ns()
        meta = dict(stream=self.stream, sequence=self.sequence + 1,
                    base=self.sequence, width=frame.width, height=frame.height,
                    mode=frame.mode, action_id=action_id,
                    observed_ns=observed_ns, context=context)
        old = self.previous
        compatible = old is not None and (old.width, old.height, old.mode) == (
            frame.width, frame.height, frame.mode)
        changed, area, visited = 0, 0, 0
        route = 'full'
        if compatible and old.pixels == frame.pixels:
            route, payload = 'unchanged', b''
        elif compatible:
            shape = (frame.height, frame.width, {'RGB': 3, 'RGBA': 4, 'L': 1}[frame.mode])
            a = np.frombuffer(old.pixels, np.uint8).reshape(shape)
            b = np.frombuffer(frame.pixels, np.uint8).reshape(shape)
            pieces, dense = [], False
            for y in range(0, frame.height, self.tile_size):
                for x in range(0, frame.width, self.tile_size):
                    tile = b[y:y+self.tile_size, x:x+self.tile_size]
                    visited += 1
                    if not np.array_equal(tile, a[y:y+self.tile_size, x:x+self.tile_size]):
                        h, w = tile.shape[:2]
                        area += h * w
                        changed += 1
                        if 4 * area > frame.width * frame.height:
                            dense = True
                            break
                        pieces.extend((TILE.pack(x, y, w, h), tile.tobytes()))
                if dense:
                    break
            if dense:
                payload = frame.pixels
            else:
                route, payload = 'tiles', b''.join(pieces)
                meta['count'] = changed
        else:
            payload = frame.pixels
        meta['kind'] = route
        wire = packet(meta, payload)
        # Serialization failure must not mutate sender state.
        self.previous, self.sequence = frame, meta['sequence']
        self.last = dict(kind=route, wire_bytes=len(wire),
                         changed_tiles=changed, visited_tiles=visited,
                         changed_count_complete=not (route == 'full' and compatible),
                         encode_ns=perf_counter_ns() - start)
        return wire
