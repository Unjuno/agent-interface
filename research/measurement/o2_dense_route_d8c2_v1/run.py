"""One immutable six-condition timing batch. Only generated local image data."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import zlib
from codec import Encoder, DenseEncoder, Decoder
from fixtures import SIZES, SCENES, frames

HERE = Path(__file__).resolve().parent

def digest(b):
    return hashlib.sha256(b).hexdigest()

def packed(b):
    return {'bytes': len(b), 'sha256': digest(b), 'zlib_b64': base64.b64encode(zlib.compress(b, 9)).decode()}

def verify_freeze():
    for p, expected in json.loads((HERE/'FREEZE.json').read_text())['files'].items():
        if digest((HERE/p).read_bytes()) != expected:
            raise ValueError('source/input changed: '+p)

def run(out, index):
    if out.exists():
        raise FileExistsError(out)
    verify_freeze()
    env = json.loads((HERE/'ENVIRONMENT.json').read_text())
    os.sched_setaffinity(0, {env['selected_cpu']})
    width, height = SIZES[index]
    result = dict(allocation='o2-dense-d8c2-20260925', batch=index,
                  pid=os.getpid(), affinity=sorted(os.sched_getaffinity(0)),
                  utc=datetime.now(timezone.utc).isoformat(), conditions=[], complete=False,
                  freeze_sha256=digest((HERE/'FREEZE.json').read_bytes()))
    out.parent.mkdir(parents=True, exist_ok=True)
    # Reserve output BEFORE any measured encode. Preserve partial records on failure.
    with out.open('x') as file:
        file.write(json.dumps(result))
    try:
        for si, scene in enumerate(SCENES):
            before, after = frames(width, height, scene)
            cid = f'd8c2-{index}-{si}'
            row = dict(id=cid, scene=scene, width=width, height=height,
                       before=packed(before.pixels), after=packed(after.pixels),
                       packets={}, warmups=[], samples=[])
            result['conditions'].append(row)
            for iteration in range(-2, 15):
                order = ['canonical', 'dense'] if (iteration+si+index)%2==0 else ['dense', 'canonical']
                pair = dict(iteration=iteration, order=order, arms={})
                for name in order:
                    cls = Encoder if name == 'canonical' else DenseEncoder
                    enc = cls(cid, 'O2', 64)
                    first = enc.encode(before, action_id='base', observed_ns=100, context=('synthetic',))
                    w0 = time.perf_counter_ns()
                    c0 = time.process_time_ns()
                    wire = enc.encode(after, action_id='update', observed_ns=200, context=('synthetic',))
                    c1 = time.process_time_ns()
                    w1 = time.perf_counter_ns()
                    # All correctness, compression for retention and hashing is outside timer.
                    dec = Decoder(cid)
                    assert dec.accept(first).pixels == before.pixels
                    assert dec.accept(wire).pixels == after.pixels
                    pair['arms'][name] = dict(wall_start=w0, wall_end=w1, cpu_start=c0, cpu_end=c1,
                                              initial_sha256=digest(first), update_sha256=digest(wire),
                                              kind=enc.last['kind'], changed_tiles=enc.last['changed_tiles'],
                                              sequence=enc.sequence)
                    if name not in row['packets']:
                        row['packets'][name] = dict(initial=packed(first), update=packed(wire))
                    else:
                        assert digest(wire) == row['packets'][name]['update']['sha256']
                        assert digest(first) == row['packets'][name]['initial']['sha256']
                (row['warmups'] if iteration < 0 else row['samples']).append(pair)
            out.write_text(json.dumps(result, separators=(',', ':'))+'\n')
        verify_freeze()
        result['complete'] = True
    except BaseException:
        result['exception'] = traceback.format_exc()
        raise
    finally:
        result['end_utc'] = datetime.now(timezone.utc).isoformat()
        out.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    return result

if __name__ == '__main__':
    run(Path(sys.argv[1]), int(sys.argv[2]))
