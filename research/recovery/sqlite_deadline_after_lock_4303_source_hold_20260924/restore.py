"""Restore verified regular files into a new directory; never execute a study."""
import base64
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent
prefix, destination = sys.argv[1], Path(sys.argv[2])
manifest = json.loads((root / (prefix + '.json')).read_text())
parts = []
for item in manifest['chunks']:
    data = (root / item['name']).read_bytes()
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise ValueError('part mismatch: ' + item['name'])
    parts.append(data)
archive = base64.b64decode(b''.join(parts).replace(b'\n', b''), validate=True)
if len(archive) != manifest['archive_bytes'] or hashlib.sha256(archive).hexdigest() != manifest['archive_sha256']:
    raise ValueError('archive mismatch')
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:xz') as tf:
    members = tf.getmembers()
    if len(members) != len(manifest['files']) or {m.name for m in members} != set(manifest['files']):
        raise ValueError('member set mismatch')
    destination.mkdir(parents=True, exist_ok=False)
    base = destination.resolve()
    for member in members:
        path = (base / member.name).resolve()
        if not member.isfile() or not path.is_relative_to(base) or path == base:
            raise ValueError('unsafe member')
        data = tf.extractfile(member).read()
        if hashlib.sha256(data).hexdigest() != manifest['files'][member.name]:
            raise ValueError('member digest mismatch: ' + member.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(data)
print(json.dumps({'restored_files': len(members), 'archive_sha256': manifest['archive_sha256']}, sort_keys=True))
