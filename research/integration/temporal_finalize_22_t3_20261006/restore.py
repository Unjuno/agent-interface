"""Data-only, bounded restoration. Never runs the archived experiment.

Use a fresh destination inside a trusted, quiescent parent directory.
Hashes verify integrity, not authenticity or an adversarial-filesystem sandbox.
"""
from __future__ import annotations
import hashlib
import json
import lzma
import sys
from pathlib import Path, PurePosixPath


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def restore(source: Path, destination: Path) -> dict:
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    manifest = json.loads((source / 'CAPSULE.json').read_text(), object_pairs_hook=unique)
    for key, ceiling in [('archive_bytes', 1_000_000), ('expanded_bytes', 2_000_000), ('files', 1000)]:
        if type(manifest[key]) is not int or not 0 < manifest[key] <= ceiling:
            raise ValueError('invalid bounded manifest field: ' + key)
    parts = manifest['parts']
    if type(parts) is not list or len(parts) != 7:
        raise ValueError('part count')
    chunks = []
    for index, part in enumerate(parts):
        if part['name'] != f'evidence-{index:02}.xzpart':
            raise ValueError('part order/name')
        path = source / part['name']
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 4096:
            raise ValueError('part kind/size')
        data = path.read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('part integrity')
        chunks.append(data)
    archive = b''.join(chunks)
    if len(archive) != manifest['archive_bytes'] or hashlib.sha256(archive).hexdigest() != manifest['archive_sha256']:
        raise ValueError('archive integrity')
    decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
    raw = decoder.decompress(archive, max_length=manifest['expanded_bytes'] + 1)
    if not decoder.eof or decoder.unused_data or len(raw) != manifest['expanded_bytes']:
        raise ValueError('expansion bound or trailing archive')
    if hashlib.sha256(raw).hexdigest() != manifest['expanded_sha256']:
        raise ValueError('expanded integrity')
    files = json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    if type(files) is not dict or len(files) != manifest['files']:
        raise ValueError('member count')
    prepared = []
    for name, text in files.items():
        path = PurePosixPath(name)
        if (type(text) is not str or not name or '\\' in name or ':' in name or '\0' in name
                or path.is_absolute() or '..' in path.parts or str(path) != name):
            raise ValueError('unsafe member')
        prepared.append((path, text.encode('utf-8')))
    names = {str(path) for path, _ in prepared}
    if any(str(parent) in names for path, _ in prepared for parent in path.parents if str(parent) != '.'):
        raise ValueError('file/directory collision')
    destination.mkdir(parents=False, exist_ok=False)
    for path, data in prepared:
        target = destination.joinpath(*path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(data)
    return {'files': len(files), 'archive_sha256': manifest['archive_sha256'], 'executes_code': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B restore.py NEW_DIRECTORY')
    print(json.dumps(restore(Path(__file__).resolve().parent, Path(sys.argv[1])), sort_keys=True))
