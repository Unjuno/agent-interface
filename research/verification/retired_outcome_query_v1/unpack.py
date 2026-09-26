"""Restore the hash-pinned #4027 archive into a new directory. Never run its code."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

ARCHIVE_SHA = '40defd70f77380315c7e35ecf7ba4f7771a335de00ce1a66b1cbc1ac9f8e5a28'
MAX_TAR = 32 * 1024 * 1024

def sha(data):
    return hashlib.sha256(data).hexdigest()

def restore(source: Path, destination: Path):
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        raise ValueError('destination must be an absent absolute path')
    spec = json.loads((source / 'PACK.json').read_text())
    if spec['archive_sha256'] != ARCHIVE_SHA or len(spec['parts']) != 7:
        raise ValueError('unexpected archive identity')
    chunks = []
    for i, item in enumerate(spec['parts']):
        if item['path'] != f'parts/{i:02d}.bin':
            raise ValueError('part order/path')
        with (source / item['path']).open('rb') as f:
            data = f.read(6001)
        if len(data) != item['bytes'] or sha(data) != item['sha256']:
            raise ValueError('part integrity')
        chunks.append(data)
    data = b''.join(chunks)
    if len(data) != 38900 or sha(data) != ARCHIVE_SHA:
        raise ValueError('archive integrity')
    dec = lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw = dec.decompress(data, max_length=MAX_TAR+1)
    if len(raw) > MAX_TAR or not dec.eof or dec.unused_data:
        raise ValueError('decompression bounds')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for entry in archive:
            path = PurePosixPath(entry.name)
            if (not entry.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != entry.name or entry.name in members
                    or entry.size < 0 or entry.size > MAX_TAR):
                raise ValueError('unsafe or duplicate archive member')
            f = archive.extractfile(entry)
            if f is None:
                raise ValueError('missing member')
            blob = f.read(MAX_TAR+1)
            if len(blob) != entry.size:
                raise ValueError('member length')
            members[entry.name] = blob
    if len(members) != 173 or sum(map(len, members.values())) != 12562374:
        raise ValueError('member denominator')
    manifest = {}
    for line in members['SHA256SUMS'].decode('utf-8').splitlines():
        checksum, path = line.split('  ', 1)
        if path in manifest:
            raise ValueError('duplicate checksum member')
        manifest[path] = checksum
    if set(manifest) != set(members) - {'SHA256SUMS'}:
        raise ValueError('checksum coverage')
    if any(sha(members[path]) != checksum for path, checksum in manifest.items()):
        raise ValueError('member checksum')
    destination.mkdir(exist_ok=False)
    for name, blob in members.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(blob)
    return {'status': 'RESTORED_NOT_EXECUTED', 'members': len(members),
            'file_bytes': sum(map(len, members.values())), 'archive_sha256': ARCHIVE_SHA}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent, args.destination), sort_keys=True))
