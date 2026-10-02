"""Data-only, bounded capsule restoration into a NEW trusted directory."""
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

LIMIT = 64 * 1024 * 1024


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('invalid member name')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p) != name:
        raise ValueError('nonrelative member name')
    return p


def restore(manifest_path, destination):
    mp = Path(manifest_path)
    m = json.loads(mp.read_text())
    dst = Path(destination)
    if dst.exists():
        raise FileExistsError(dst)
    chunks = []
    for part in m['parts']:
        name = safe_name(part['path'])
        data = (mp.parent / str(name)).read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('part mismatch: ' + str(name))
        chunks.append(data.strip())
    archive = base64.b64decode(b''.join(chunks), validate=True)
    if len(archive) != m['archive_bytes'] or hashlib.sha256(archive).hexdigest() != m['archive_sha256']:
        raise ValueError('archive mismatch')
    with lzma.open(io.BytesIO(archive)) as stream:
        expanded = stream.read(LIMIT + 1)
    if len(expanded) > LIMIT:
        raise ValueError('expansion limit')
    # Archive hash binds an optional internal index for full-evidence capsules.
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as tf:
        members = tf.getmembers()
        if len(members) > 3000:
            raise ValueError('member count limit')
        names = [t.name for t in members]
        if len(set(names)) != len(names):
            raise ValueError('duplicate member')
        for t in members:
            safe_name(t.name)
            if not t.isfile() or t.size < 0 or t.size > LIMIT:
                raise ValueError('nonregular or oversized member')
        expected = m.get('members')
        if expected is None:
            index = tf.extractfile('CAPSULE_INDEX.json').read()
            if hashlib.sha256(index).hexdigest() != m['index_sha256']:
                raise ValueError('index mismatch')
            expected = json.loads(index)
            expected['CAPSULE_INDEX.json'] = m['index_sha256']
        if set(names) != set(expected):
            raise ValueError('member set mismatch')
        payloads = {}
        for t in members:
            data = tf.extractfile(t).read()
            if len(data) != t.size or hashlib.sha256(data).hexdigest() != expected[t.name]:
                raise ValueError('member mismatch: ' + t.name)
            payloads[t.name] = data
    dst.mkdir(parents=False, exist_ok=False)
    for name, data in payloads.items():
        path = dst / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(data)
    return {'files': len(payloads), 'archive_sha256': m['archive_sha256']}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: unpack.py MANIFEST NEW_DESTINATION')
    print(json.dumps(restore(sys.argv[1], sys.argv[2]), sort_keys=True))
