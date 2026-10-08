"""Restore exact frozen input files only; never start the measured allocation."""
from pathlib import Path, PurePosixPath
import hashlib, io, json, sys, tarfile

HERE = Path(__file__).resolve().parent
ARCHIVE_SHA = 'e70a610316942517228f33fedecc1c3d33c5dd7391271cd349e984f955162075'

def restore(destination):
    dest = Path(destination)
    if dest.exists(): raise ValueError('destination must be absent')
    blob = b''.join((HERE / f'INPUTS.part{i:02d}.bin').read_bytes() for i in range(3))
    if len(blob) != 9188 or hashlib.sha256(blob).hexdigest() != ARCHIVE_SHA:
        raise ValueError('input archive identity')
    expected = {p: d for p, d in json.loads((HERE/'FREEZE.json').read_text())['files'].items() if p.startswith('inputs/')}
    data = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:xz') as tf:
        members = tf.getmembers()
        if len(members) != 12 or sum(m.size for m in members) != 102297:
            raise ValueError('input inventory')
        for m in members:
            p = PurePosixPath(m.name)
            if not m.isfile() or str(p) != m.name or m.name not in expected or m.name in data:
                raise ValueError('unexpected member')
            if p.is_absolute() or '..' in p.parts or m.size > 40000:
                raise ValueError('invalid member')
            raw = tf.extractfile(m).read()
            if len(raw) != m.size or hashlib.sha256(raw).hexdigest() != expected[m.name]:
                raise ValueError('input member identity')
            data[m.name] = raw
    if set(data) != set(expected): raise ValueError('missing member')
    dest.mkdir(parents=True, exist_ok=False)
    for name, raw in data.items():
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f: f.write(raw)
    return {'files':len(data),'bytes':sum(map(len,data.values())),'archive_sha256':ARCHIVE_SHA,'executed_measurement':False}

if __name__ == '__main__': print(json.dumps(restore(sys.argv[1]),sort_keys=True))
