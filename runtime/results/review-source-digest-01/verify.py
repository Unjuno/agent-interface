import hashlib, json, tarfile
from pathlib import Path
root = Path(__file__).parent
expected = json.loads((root / 'manifest.json').read_text())['files']
with tarfile.open(root / 'raw.tar.gz') as archive:
    members = archive.getmembers()
    if len(members) != len(expected) or {m.name for m in members} != {r['path'] for r in expected}:
        raise ValueError('member set mismatch')
    for row in expected:
        member = archive.getmember(row['path'])
        if not member.isfile():
            raise ValueError('non-file member')
        data = archive.extractfile(member).read()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('member digest mismatch')
print('PASS: archived member bytes and digests')
