"""Bounded, data-only reconstruction; never imports or executes archived code."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(source, destination):
    source, destination = Path(source), Path(destination)
    m = json.loads((source / 'CAPSULE.json').read_text())
    if m.get('schema') != 'k7m2-evidence-capsule-v1':
        raise ValueError('SCHEMA')
    limits = {'members': 1000, 'file_bytes': 10000000, 'tar_bytes': 12000000, 'xz_bytes': 1000000}
    for key, limit in limits.items():
        if type(m[key]) is not int or not 0 < m[key] <= limit:
            raise ValueError('BOUND:' + key)
    if destination.exists() or destination.is_symlink():
        raise ValueError('DESTINATION_EXISTS')
    if not isinstance(m['parts'], list) or not 1 <= len(m['parts']) <= 100:
        raise ValueError('PART_COUNT')
    blocks = []
    for i, part in enumerate(m['parts']):
        if part['file'] != f'evidence-{i:02d}.xz.part':
            raise ValueError('PART_ORDER')
        if type(part['size']) is not int or not 0 < part['size'] <= 100000:
            raise ValueError('PART_BOUND')
        with (source / part['file']).open('rb') as f:
            data = f.read(part['size'] + 1)
        if len(data) != part['size'] or digest(data) != part['sha256']:
            raise ValueError('PART_DIGEST')
        blocks.append(data)
    packed = b''.join(blocks)
    if len(packed) != m['xz_bytes'] or digest(packed) != m['xz_sha256']:
        raise ValueError('ARCHIVE_DIGEST')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    data = decoder.decompress(packed, max_length=m['tar_bytes'] + 1)
    if not decoder.eof or decoder.unused_data or len(data) != m['tar_bytes'] or digest(data) != m['tar_sha256']:
        raise ValueError('EXPANDED_DIGEST_OR_BOUND')
    entries = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        for member in archive:
            p = PurePosixPath(member.name)
            if (not member.isfile() or not member.name or p.is_absolute()
                    or '..' in p.parts or '\\' in member.name or '\x00' in member.name
                    or str(p) != member.name or member.name in entries
                    or not 0 <= member.size <= m['file_bytes']):
                raise ValueError('UNSAFE_MEMBER')
            payload = archive.extractfile(member).read(member.size + 1)
            if len(payload) != member.size:
                raise ValueError('MEMBER_SIZE')
            entries[member.name] = payload
            if len(entries) > m['members']:
                raise ValueError('MEMBER_COUNT')
    if len(entries) != m['members'] or sum(map(len, entries.values())) != m['file_bytes']:
        raise ValueError('MEMBER_TOTAL')
    destination.mkdir(parents=True, exist_ok=False)
    for name, payload in entries.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as out:
            out.write(payload)
    return {'files': len(entries), 'bytes': m['file_bytes'], 'xz_sha256': m['xz_sha256'], 'pass': True}


if __name__ == '__main__':
    print(json.dumps(restore(Path(__file__).resolve().parent, sys.argv[1]), sort_keys=True, indent=2))
