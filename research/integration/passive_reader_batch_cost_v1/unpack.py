"""Verify and unpack the fixed #3988 evidence; never execute its experiments."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
ARCHIVE_SHA256 = 'b2cb261b59cf9423603bead9c185f488f126e77154176de13b0337f11753a7d7'
ARCHIVE_BYTES = 28220
MEMBERS = 106
FILE_BYTES = 1671611


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(destination):
    manifest = json.loads((ROOT / 'BUNDLE.json').read_bytes())
    require(manifest['archive_sha256'] == ARCHIVE_SHA256, 'MANIFEST_ARCHIVE_HASH')
    parts = []
    require(len(manifest['parts']) == 4, 'PART_COUNT')
    for index, info in enumerate(manifest['parts'], 1):
        require(info['path'] == f'evidence.part{index:02d}.b64', 'PART_NAME')
        data = (ROOT / info['path']).read_bytes()
        require(len(data) == info['bytes'] and sha(data) == info['sha256'], 'PART_INTEGRITY')
        parts.append(data.strip())
    archive = base64.b64decode(b''.join(parts), validate=True)
    require(len(archive) == ARCHIVE_BYTES and sha(archive) == ARCHIVE_SHA256, 'ARCHIVE_INTEGRITY')
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:xz') as source:
        members = source.getmembers()
        names = [item.name for item in members]
        require(len(names) == MEMBERS and len(set(names)) == MEMBERS, 'MEMBER_COUNT')
        require(sum(item.size for item in members) == FILE_BYTES, 'EXPANDED_SIZE')
        for item in members:
            path = PurePosixPath(item.name)
            require(item.isfile() and not path.is_absolute() and '..' not in path.parts,
                    'NON_REGULAR_OR_UNSAFE_MEMBER')
        # A new directory only: no overwrites, deletion, links or code execution.
        destination.mkdir(exist_ok=False)
        for item in members:
            target = destination / item.name
            target.parent.mkdir(parents=True, exist_ok=True)
            data = source.extractfile(item).read()
            require(len(data) == item.size, 'MEMBER_LENGTH')
            with target.open('xb') as output:
                output.write(data)
    for name in ('runner.py', 'audit.py', 'reader.py', 'test_audit.py', 'PLAN.md', 'FREEZE.json'):
        require((ROOT / name).read_bytes() == (destination / name).read_bytes(), 'READABLE_SOURCE:' + name)
    return {'status': 'PASS_BUNDLE_UNPACK', 'members': MEMBERS, 'file_bytes': FILE_BYTES,
            'archive_sha256': ARCHIVE_SHA256, 'experiment_invocations': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python unpack.py NEW_OUTPUT_DIRECTORY')
    print(json.dumps(unpack(Path(sys.argv[1]).resolve()), sort_keys=True))
