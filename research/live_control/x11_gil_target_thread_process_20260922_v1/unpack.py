"""Verify and extract retained #3954 evidence. Never starts a live experiment."""
import argparse
import base64
import hashlib
import io
import json
import tarfile
from pathlib import Path, PurePosixPath

BUNDLE_SHA256 = '3d0ea8172d6e6777da51e42a5f3c088135763e8462d63323b6e55058ba8ac6a6'
ROOT = Path(__file__).resolve().parent


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def reconstruct(root):
    plan = json.loads((root / 'parts.json').read_text())
    require(plan['bundle_sha256'] == BUNDLE_SHA256, 'bundle identity')
    require([p['path'] for p in plan['parts']] ==
            [f'evidence.part{i:02d}.b64' for i in range(1, 8)], 'part order')
    chunks = []
    for p in plan['parts']:
        data = (root / p['path']).read_bytes()
        require(len(data) == p['bytes'] and sha(data) == p['sha256'], p['path'])
        blob = b'blob ' + str(len(data)).encode() + b'\0' + data
        require(hashlib.sha1(blob).hexdigest() == p['git_blob'], 'Git blob identity')
        chunks.append(data.strip())
    bundle = base64.b64decode(b''.join(chunks), validate=True)
    require(len(bundle) == plan['bundle_bytes'] and sha(bundle) == BUNDLE_SHA256,
            'decoded bundle identity')
    with tarfile.open(fileobj=io.BytesIO(bundle), mode='r:xz') as archive:
        members = archive.getmembers()
        require(sum(m.size for m in members) <= 32 * 1024 * 1024, 'size limit')
        names = [m.name for m in members]
        require(len(names) == len(set(names)), 'duplicate archive member')
        files = {}
        for member in members:
            name = PurePosixPath(member.name)
            require(member.isfile() and not name.is_absolute() and
                    '..' not in name.parts and name.as_posix() == member.name,
                    'unsafe archive member')
            files[member.name] = archive.extractfile(member).read()
    manifest = json.loads(files['BUNDLE_MANIFEST.json'])
    require(set(files) == set(manifest) | {'BUNDLE_MANIFEST.json'}, 'member set')
    for name, expected in manifest.items():
        require(len(files[name]) == expected['bytes'] and
                sha(files[name]) == expected['sha256'], 'member digest:' + name)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='Must not already exist')
    args = parser.parse_args()
    files = reconstruct(ROOT)
    args.destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = args.destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(json.dumps({'result': 'PASS_BUNDLE_IDENTITY', 'files': len(files),
                      'bundle_sha256': BUNDLE_SHA256}, sort_keys=True))


if __name__ == '__main__':
    main()
