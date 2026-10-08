"""Verify retained archive bytes only; never import or execute archived probes."""
import hashlib
import json
from pathlib import Path
import tarfile


def verify(root):
    manifest = json.loads((root / 'MANIFEST.json').read_text())
    archive_path = root / 'evidence.tar.xz'
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('archive digest mismatch')
    expected = {row['path']: row for row in manifest['members']}
    if len(expected) != len(manifest['members']):
        raise ValueError('duplicate manifest member')
    with tarfile.open(archive_path, 'r:xz') as archive:
        members = archive.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise ValueError('archive member set mismatch')
        for member in members:
            if not member.isfile() or member.name.startswith('/') or '..' in Path(member.name).parts:
                raise ValueError('unsafe archive member')
            data = archive.extractfile(member).read()
            row = expected[member.name]
            if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('member mismatch: ' + member.name)
    return {'byte_integrity': 'PASS', 'members': len(expected), 'probe_executed': False}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
