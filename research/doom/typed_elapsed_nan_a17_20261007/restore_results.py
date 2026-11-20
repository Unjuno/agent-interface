"""Bounded data-only restorer; no study/source execution or old-result replacement."""
import base64
import binascii
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import lzma

LIMIT = 1_000_000


def restore(meta, wire, out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    if meta.get('schema') != 'typed-elapsed-results-pack-v2':
        raise ValueError('schema')
    n = meta.get('expanded_bytes')
    if type(n) is not int or not 0 < n <= LIMIT:
        raise ValueError('expansion bound')
    if len(wire) > LIMIT:
        raise ValueError('encoded bound')
    try:
        packed = base64.b64decode(''.join(wire.split()), validate=True)
    except binascii.Error as exc:
        raise ValueError('base64') from exc
    if hashlib.sha256(packed).hexdigest() != meta['compressed_sha256']:
        raise ValueError('compressed digest')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = decoder.decompress(packed, max_length=n + 1)
    if len(data) != n or not decoder.eof or decoder.unused_data:
        raise ValueError('expanded extent')
    if hashlib.sha256(data).hexdigest() != meta['expanded_sha256']:
        raise ValueError('expanded digest')
    files = json.loads(data)
    if type(files) is not dict or set(files) != set(meta['files']):
        raise ValueError('file inventory')
    validated = {}
    for name, text in files.items():
        p = PurePosixPath(name)
        if (p.is_absolute() or not p.parts or '..' in p.parts or
                p.as_posix() != name or '\\' in name or
                not (p.parts[0] in ('construction', 'results') or name == 'source_readback.json') or
                type(text) is not str):
            raise ValueError('unsafe/noncanonical path or payload')
        encoded = text.encode('utf-8')
        expected = meta['files'][name]
        if len(encoded) != expected['bytes'] or hashlib.sha256(encoded).hexdigest() != expected['sha256']:
            raise ValueError('member identity: ' + name)
        validated[name] = encoded
    out.mkdir(parents=False, exist_ok=False)
    for name, data in validated.items():
        destination = out / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(data)
    return len(validated)


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    count = restore(json.loads((root / 'PACK.json').read_text()),
                    ''.join((root / ('results.xz.b64.part%02d' % i)).read_text() for i in (1, 2, 3, 4)), Path(sys.argv[1]))
    print(json.dumps({'restored_files': count, 'executed_study': False}, sort_keys=True))
