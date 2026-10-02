"""Restore a checksummed UTF-8 file map; never executes restored programs."""
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys


def restore(manifest_path, destination):
    manifest_path, destination = Path(manifest_path), Path(destination)
    if destination.exists():
        raise ValueError('destination already exists')
    m = json.loads(manifest_path.read_text())
    payload = bytearray()
    for part in m['parts']:
        name = PurePosixPath(part['name'])
        if len(name.parts) != 1:
            raise ValueError('part path')
        b = (manifest_path.parent / name.name).read_bytes()
        if hashlib.sha256(b).hexdigest() != part['sha256']:
            raise ValueError('part digest')
        payload.extend(base64.b64decode(b, validate=True))
    if len(payload) != m['compressed_bytes'] or hashlib.sha256(payload).hexdigest() != m['compressed_sha256']:
        raise ValueError('capsule digest/size')
    limit = m['expanded_bytes']
    if type(limit) is not int or not 0 < limit < 20_000_000:
        raise ValueError('expansion bound')
    dec = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = dec.decompress(bytes(payload), max_length=limit + 1)
    if len(raw) != limit or not dec.eof or dec.unused_data or hashlib.sha256(raw).hexdigest() != m['expanded_sha256']:
        raise ValueError('expanded digest/size')
    files = json.loads(raw)
    if set(files) != set(m['files']):
        raise ValueError('member names')
    for name, text in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name or not path.parts or type(text) is not str:
            raise ValueError('member path/type')
        if hashlib.sha256(text.encode()).hexdigest() != m['files'][name]:
            raise ValueError('member digest')
    destination.mkdir(parents=True, exist_ok=False)
    for name, text in files.items():
        path = destination.joinpath(*PurePosixPath(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())
    return {'files': len(files), 'bytes': sum(len(s.encode()) for s in files.values())}


if __name__ == '__main__':
    print(json.dumps(restore(sys.argv[1], sys.argv[2]), sort_keys=True))
