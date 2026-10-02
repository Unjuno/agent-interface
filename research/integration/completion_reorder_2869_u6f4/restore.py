"""Restore a hash-bound UTF-8 JSON capsule into a new directory; never execute it."""
from pathlib import Path, PurePosixPath
import base64, hashlib, json, lzma, sys

def sha(b):
    return hashlib.sha256(b).hexdigest()

def restore(manifest_path, destination):
    mpath = Path(manifest_path)
    m = json.loads(mpath.read_text())
    dest = Path(destination)
    if dest.exists():
        raise ValueError('destination must not exist')
    encoded = []
    for part in m['parts']:
        name = part['name']
        if PurePosixPath(name).name != name or '\\' in name:
            raise ValueError('unsafe capsule part')
        b = (mpath.parent / name).read_bytes()
        if len(b) != part['bytes'] or sha(b) != part['sha256']:
            raise ValueError('capsule part mismatch: ' + name)
        encoded.append(b.strip())
    packed = base64.b64decode(b''.join(encoded), validate=True)
    if len(packed) != m['xz_bytes'] or sha(packed) != m['xz_sha256']:
        raise ValueError('capsule digest mismatch')
    if not 0 <= m['json_bytes'] <= 50000000:
        raise ValueError('expansion limit')
    dec = lzma.LZMADecompressor(memlimit=268435456)
    raw = dec.decompress(packed, max_length=m['json_bytes'] + 1)
    if len(raw) != m['json_bytes'] or not dec.eof or dec.unused_data:
        raise ValueError('expansion mismatch')
    def unique(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise ValueError('duplicate JSON key')
            obj[k] = v
        return obj
    files = json.loads(raw, object_pairs_hook=unique)
    if set(files) != set(m['files']):
        raise ValueError('file inventory mismatch')
    checked = {}
    for name, text in files.items():
        p = PurePosixPath(name)
        if p.is_absolute() or not p.parts or any(x in ('..', '.') for x in p.parts) or '\\' in name:
            raise ValueError('unsafe member')
        if str(p) != name or not isinstance(text, str):
            raise ValueError('invalid member')
        b = text.encode('utf-8')
        if len(b) != m['files'][name]['bytes'] or sha(b) != m['files'][name]['sha256']:
            raise ValueError('member mismatch: ' + name)
        checked[name] = b
    dest.mkdir(parents=True, exist_ok=False)
    for name, b in checked.items():
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(b)
    return {'files': len(checked), 'xz_sha256': sha(packed), 'executed': False}

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: python -B restore.py MANIFEST.json NEW_DIRECTORY')
    print(json.dumps(restore(sys.argv[1], sys.argv[2]), sort_keys=True))
