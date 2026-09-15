"""Opt-in AIT1 encoder v2: same v1 wire policy, one cold/repeat comparison.

Trusted ordered local transport only. No input authority, new decoder, default
promotion, minimum-wire-size promise, or live GUI/model efficacy claim.
"""
from pathlib import Path
import sys
from time import perf_counter_ns
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research' / 'observation_tiles'))
from tile_transport import Encoder, Decoder, Frame, TILE, packet


class ConditionalEncoder(Encoder):
    def __init__(self, stream: str, tile_size: int = 64):
        if type(tile_size) is not int or tile_size <= 0:
            raise ValueError('tile_size must be a positive integer')
        super().__init__(stream, strategy='O1', tile_size=tile_size)

    def encode(self, frame: Frame, *, action_id: str, observed_ns: int,
               context=()) -> bytes:
        start = perf_counter_ns()
        old = self.previous
        compatible = old is not None and (old.width, old.height, old.mode) == (
            frame.width, frame.height, frame.mode)
        seq, size = self.sequence + 1, self.tile_size
        meta = dict(stream=self.stream, sequence=seq, base=self.sequence,
                    width=frame.width, height=frame.height, mode=frame.mode,
                    action_id=action_id, observed_ns=observed_ns, context=context)
        changed = 0
        if not compatible:
            meta['kind'], payload, route = 'full', frame.pixels, 'cold'
        elif old.pixels == frame.pixels:
            meta['kind'], payload, route = 'unchanged', b'', 'repeat'
        else:
            channels = {'RGB': 3, 'RGBA': 4, 'L': 1}[frame.mode]
            shape = (frame.height, frame.width, channels)
            a = np.frombuffer(old.pixels, np.uint8).reshape(shape)
            b = np.frombuffer(frame.pixels, np.uint8).reshape(shape)
            total = ((frame.width + size - 1) // size) * ((frame.height + size - 1) // size)
            pieces, dense = [], False
            for y in range(0, frame.height, size):
                for x in range(0, frame.width, size):
                    tile = b[y:y+size, x:x+size]
                    if not np.array_equal(tile, a[y:y+size, x:x+size]):
                        changed += 1
                        if 4 * changed > total:
                            dense = True
                            break
                        h, w = tile.shape[:2]
                        pieces.extend((TILE.pack(x, y, w, h), tile.tobytes()))
                if dense:
                    break
            if dense:
                meta['kind'], payload, route = 'full', frame.pixels, 'dense_full'
            else:
                meta.update(kind='tiles', count=changed)
                payload, route = b''.join(pieces), 'sparse_tiles'
        wire = packet(meta, payload)
        # Nothing changes before serialization succeeds, including telemetry.
        self.previous, self.sequence = frame, seq
        self.last = dict(kind=meta['kind'], wire_bytes=len(wire),
                         changed_tiles_lower_bound=changed, route=route,
                         encode_ns=perf_counter_ns()-start)
        return wire
