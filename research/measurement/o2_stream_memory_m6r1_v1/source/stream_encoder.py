"""Research-only streaming tile materialization, not a runtime/default change."""
import json
from pathlib import Path
import sys
from time import perf_counter_ns
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'upstream/research/observation_tiles'))
from tile_transport import Encoder, Decoder, Frame, PREFIX, TILE, packet, np


class StreamingEncoder(Encoder):
    """Keep both alternatives and the canonical tie rule; stream only tile data."""
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
                channels = {'RGB': 3, 'RGBA': 4, 'L': 1}[frame.mode]
                shape = (frame.height, frame.width, channels)
                a = np.frombuffer(old.pixels, np.uint8).reshape(shape)
                b = np.frombuffer(frame.pixels, np.uint8).reshape(shape)
                compressor = zlib.compressobj(1, zlib.DEFLATED, 15, 8,
                                               zlib.Z_DEFAULT_STRATEGY)
                compressed = bytearray()
                size = self.tile_size
                for y in range(0, frame.height, size):
                    for x in range(0, frame.width, size):
                        tile = b[y:y+size, x:x+size]
                        if not np.array_equal(tile, a[y:y+size, x:x+size]):
                            h, w = tile.shape[:2]
                            compressed.extend(compressor.compress(TILE.pack(x, y, w, h)))
                            compressed.extend(compressor.compress(np.ascontiguousarray(tile).tobytes()))
                            changed += 1
                compressed.extend(compressor.flush(zlib.Z_FINISH))
                tile_meta = dict(meta, kind='tiles', count=changed)
                header = json.dumps(tile_meta, separators=(',', ':'), sort_keys=True).encode()
                candidate = PREFIX.pack(b'AIT1', len(header)) + header + bytes(compressed)
                if len(candidate) < len(wire):
                    wire, meta = candidate, tile_meta
        # No externally visible encoder state changes until every operation succeeds.
        self.previous, self.sequence = frame, seq
        self.last = dict(kind=meta['kind'], wire_bytes=len(wire),
                         changed_tiles=changed, encode_ns=perf_counter_ns()-start)
        return wire
