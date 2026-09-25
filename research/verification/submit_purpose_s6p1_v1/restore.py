"""Bounded data-only restore. Never executes the retained study or overwrites paths."""
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile
import sys
HERE = Path(__file__).resolve().parent


def load_members():
    spec = json.loads((HERE / 'PACKAGE.json').read_text())
    def count(key, limit):
        value = spec[key]
        if type(value) is not int or not 0 < value <= limit:
            raise ValueError('invalid bound: ' + key)
        return value
    archive_n = count('archive_bytes', 2_000_000)
    tar_n = count('tar_bytes', 20_000_000)
    member_n = count('members', 5000)
    pieces = []
    for part in spec['parts']:
        name = part['name']
        if type(name) is not str or PurePosixPath(name).name != name:
            raise ValueError('invalid part name')
        b = base64.b64decode((HERE / name).read_bytes(), validate=True)
        if len(b) != part['bytes'] or hashlib.sha256(b).hexdigest() != part['sha256']:
            raise ValueError('part mismatch')
        pieces.append(b)
    packed = b''.join(pieces)
    if len(packed) != archive_n or hashlib.sha256(packed).hexdigest() != spec['archive_sha256']:
        raise ValueError('archive mismatch')
    dec = lzma.LZMADecompressor()
    raw = dec.decompress(packed, max_length=tar_n + 1)
    if len(raw) != tar_n or not dec.eof or dec.unused_data or hashlib.sha256(raw).hexdigest() != spec['tar_sha256']:
        raise ValueError('expanded archive mismatch')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as t:
        for entry in t.getmembers():
            name = entry.name; path = PurePosixPath(name)
            if not entry.isfile() or path.is_absolute() or '..' in path.parts or str(path) != name or name in result:
                raise ValueError('invalid archive member')
            if entry.size < 0 or entry.size > tar_n:
                raise ValueError('oversized member')
            b = t.extractfile(entry).read()
            if len(b) != entry.size:
                raise ValueError('member size mismatch')
            result[name] = b
    if len(result) != member_n or sum(map(len, result.values())) != count('member_bytes', 20_000_000):
        raise ValueError('member inventory')
    return result


def restore(out):
    # The parent is a trusted/quiescent reviewer-selected directory, not a hostile sandbox.
    out = Path(out).absolute()
    if out.exists() or out.is_symlink():
        raise ValueError('destination exists')
    members = load_members()
    out.mkdir()
    for name, data in members.items():
        dest = out / name; dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f:
            f.write(data)
    return {'files': len(members), 'member_bytes': sum(map(len, members.values())), 'executed_study': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B restore.py NEW_DIRECTORY')
    print(json.dumps(restore(sys.argv[1]), sort_keys=True))
