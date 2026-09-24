"""Restore the immutable #4323 geometry study; never execute archived code.

The publication directory and destination parent must be trusted, quiescent local
paths. This is a bounded evidence restorer, not an adversarial filesystem sandbox.
"""
from __future__ import annotations
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

HERE = Path(__file__).resolve().parent
MAX_ARCHIVE = 1_000_000
MAX_TAR = 32_000_000
MAX_FILES = 600
MAX_MEMBER = 2_000_000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_name(value: str) -> str:
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise ValueError('invalid member name')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or '.' in value.split('/') or str(p) != value:
        raise ValueError('noncanonical relative member name')
    return value


def restore(destination: Path, publication: Path = HERE) -> dict:
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('destination must be new')
    meta = json.loads((publication / 'CAPSULE.json').read_bytes())
    if meta['format'] != 'geometry-evidence-xz-tar-v1':
        raise ValueError('capsule format')
    if not 0 < meta['archive_bytes'] <= MAX_ARCHIVE or not 0 < meta['tar_bytes'] <= MAX_TAR:
        raise ValueError('archive bound')
    chunks = []
    seen = set()
    for item in meta['parts']:
        name = relative_name(item['path'])
        if name in seen:
            raise ValueError('duplicate part')
        seen.add(name)
        path = publication / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE:
            raise ValueError('part file')
        data = path.read_bytes()
        if len(data) != item['bytes'] or digest(data) != item['sha256']:
            raise ValueError('part integrity')
        chunks.append(data)
    packed = b''.join(chunks)
    if len(packed) != meta['archive_bytes'] or digest(packed) != meta['archive_sha256']:
        raise ValueError('archive integrity')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(packed, max_length=meta['tar_bytes'] + 1)
    if len(raw) != meta['tar_bytes'] or not decoder.eof or decoder.unused_data:
        raise ValueError('decompression bound or trailing data')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for item in archive:
            name = relative_name(item.name)
            if not item.isreg() or name in members or not 0 <= item.size <= MAX_MEMBER:
                raise ValueError('nonregular/duplicate/oversize member')
            if len(members) >= MAX_FILES:
                raise ValueError('member count bound')
            stream = archive.extractfile(item)
            if stream is None:
                raise ValueError('missing member bytes')
            data = stream.read(MAX_MEMBER + 1)
            if len(data) != item.size:
                raise ValueError('member size')
            members[name] = data
    if len(members) != meta['files'] or sum(map(len, members.values())) != meta['member_bytes']:
        raise ValueError('denominator')
    manifest_bytes = members['MANIFEST.json']
    if digest(manifest_bytes) != meta['original_manifest_sha256']:
        raise ValueError('original manifest hash')
    manifest = json.loads(manifest_bytes)['files']
    if set(manifest) != set(members) - {'MANIFEST.json'}:
        raise ValueError('original member set')
    for name, item in manifest.items():
        data = members[name]
        if len(data) != item['bytes'] or digest(data) != item['sha256']:
            raise ValueError('original member integrity: ' + name)
    # Check every member before creating any destination file.
    for name in members:
        for parent in PurePosixPath(name).parents:
            if str(parent) in members:
                raise ValueError('file/directory collision')
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in members.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(data)
    return {'status': 'PASS_LOSSLESS_RESTORE', 'files': len(members),
            'member_bytes': meta['member_bytes'], 'gui_runs': 0, 'scientific_reruns': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -B restore.py NEW_DESTINATION')
    print(json.dumps(restore(Path(sys.argv[1])), indent=2, sort_keys=True))
