"""Restore retained research bytes only; never load the native binary or run a study."""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import json
import lzma
import sys

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def restore(out):
    meta = json.loads((HERE / 'CAPSULE.json').read_text(encoding='utf-8'))
    if meta['format'] != 'xz-json-file-map-v1' or meta['files'] != 309:
        raise ValueError('unsupported capsule')
    if not 0 < meta['compressed_bytes'] <= 1048576:
        raise ValueError('compressed bound')
    if not 0 < meta['decoded_bytes'] <= 2097152:
        raise ValueError('decoded bound')
    chunks = []
    for index, part in enumerate(meta['parts']):
        if part['name'] != f'EVIDENCE.part{index:02d}' or part['bytes'] > 6000:
            raise ValueError('part identity/bound')
        path = HERE / part['name']
        if path.is_symlink() or path.stat().st_size != part['bytes']:
            raise ValueError('part size/type')
        data = path.read_bytes()
        if sha(data) != part['sha256']:
            raise ValueError('part digest')
        chunks.append(data)
    packed = b''.join(chunks)
    if len(packed) != meta['compressed_bytes'] or sha(packed) != meta['compressed_sha256']:
        raise ValueError('capsule digest/size')
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    raw = decoder.decompress(packed, max_length=meta['decoded_bytes'] + 1)
    if not decoder.eof or decoder.unused_data or len(raw) != meta['decoded_bytes']:
        raise ValueError('decoded extent')
    if sha(raw) != meta['decoded_sha256']:
        raise ValueError('decoded digest')
    rows = json.loads(raw)
    if not isinstance(rows, list) or len(rows) != meta['files']:
        raise ValueError('file count')
    files = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 3 or not all(isinstance(x, str) for x in row):
            raise ValueError('row schema')
        name, encoding, text = row
        path = PurePosixPath(name)
        if not name or path.is_absolute() or str(path) != name or '..' in path.parts or '\\' in name:
            raise ValueError('member path')
        if name in files:
            raise ValueError('duplicate member')
        if encoding == 'utf8':
            data = text.encode('utf-8')
        elif encoding == 'base64':
            data = base64.b64decode(text, validate=True)
        else:
            raise ValueError('member encoding')
        files[name] = data
    if sum(map(len, files.values())) != meta['member_bytes']:
        raise ValueError('member extent')
    for name in files:
        if any(str(parent) in files for parent in PurePosixPath(name).parents if str(parent) != '.'):
            raise ValueError('file/directory collision')
    # All validation precedes writing. A fresh destination is required.
    out.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    return {'status': 'RESTORED_BYTES_ONLY', 'files': len(files),
            'member_bytes': sum(map(len, files.values())), 'formal_reruns': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -B unpack.py ABSENT_DIRECTORY')
    print(json.dumps(restore(Path(sys.argv[1])), sort_keys=True))
