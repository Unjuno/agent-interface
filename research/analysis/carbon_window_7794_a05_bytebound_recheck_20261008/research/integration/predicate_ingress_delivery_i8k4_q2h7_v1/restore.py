"""Data-only lossless restoration; never execute a scientific worker."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import lzma
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
MAX_ARCHIVE = 100000
MAX_TAR = 1000000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(destination, root=ROOT):
    root, destination = Path(root), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('DESTINATION_EXISTS')
    spec = json.loads((root / 'PACKAGE.json').read_bytes())
    segments = spec['segments']
    if len(segments) != 8 or [x['name'] for x in segments] != [f'evidence.{i:02}.bin' for i in range(8)]:
        raise ValueError('SEGMENT_SET')
    pieces = []
    for item in segments:
        data = (root / item['name']).read_bytes()
        if len(data) != item['bytes'] or digest(data) != item['sha256']:
            raise ValueError('SEGMENT_IDENTITY')
        pieces.append(data)
    archive = b''.join(pieces)
    if len(archive) > MAX_ARCHIVE or len(archive) != spec['archive_bytes'] or digest(archive) != spec['archive_sha256']:
        raise ValueError('ARCHIVE_IDENTITY')
    decoder = lzma.LZMADecompressor(memlimit=200000000)
    raw = decoder.decompress(archive, max_length=MAX_TAR + 1)
    if len(raw) > MAX_TAR or len(raw) != spec['tar_bytes'] or not decoder.eof or decoder.unused_data:
        raise ValueError('ARCHIVE_EXTENT')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as stream:
        for item in stream.getmembers():
            path = PurePosixPath(item.name)
            if (not item.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != item.name or '\\' in item.name or item.name in files):
                raise ValueError('MEMBER_PATH_OR_TYPE')
            if item.name not in spec['members']:
                raise ValueError('MEMBER_SET')
            data = stream.extractfile(item).read()
            if digest(data) != spec['members'][item.name]:
                raise ValueError('MEMBER_IDENTITY')
            files[item.name] = data
    if set(files) != set(spec['members']) or len(files) != spec['member_count'] or sum(map(len, files.values())) != spec['member_bytes']:
        raise ValueError('MEMBER_EXTENT')
    for published, original in spec['readable_parity'].items():
        if (root / published).read_bytes() != files[original]:
            raise ValueError('READABLE_PARITY')
    # Trusted, quiescent parent; this is not an adversarial filesystem sandbox.
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as output:
            output.write(data)
    return {'files': len(files), 'member_bytes': sum(map(len, files.values())),
            'archive_sha256': digest(archive), 'measured_workers_started': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B restore.py NEW_DIRECTORY')
    print(json.dumps(restore(sys.argv[1]), sort_keys=True, indent=2))
