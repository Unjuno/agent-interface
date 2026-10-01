"""Restore retained data only. Never execute a study or replace an existing path."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

ROOT = Path(__file__).resolve().parent

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def relative(name: str) -> PurePosixPath:
    if not isinstance(name, str) or '\\' in name:
        raise ValueError('invalid relative path')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name or not path.parts:
        raise ValueError('noncanonical relative path')
    return path

def members(raw: bytes, count: int, total: int) -> list[tuple[str, bytes]]:
    found: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for item in archive:
            relative(item.name)
            if not item.isfile() or item.name in seen or item.size < 0:
                raise ValueError('nonregular or duplicate member')
            seen.add(item.name)
            stream = archive.extractfile(item)
            if stream is None:
                raise ValueError('unreadable member')
            data = stream.read()
            if len(data) != item.size:
                raise ValueError('short member')
            found.append((item.name, data))
    if len(found) != count or sum(len(data) for _, data in found) != total:
        raise ValueError('member inventory mismatch')
    return found

def restore(base: Path, destination: Path) -> Path:
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination must not exist')
    manifest = json.loads((base/'MANIFEST.json').read_bytes())
    if manifest['schema'] != 'r9k4-delivery-v1':
        raise ValueError('unknown manifest schema')
    for name, maximum in [('archive_bytes', 200000), ('tar_bytes', 2000000),
                          ('member_bytes', 1000000), ('member_files', 1000)]:
        value = manifest[name]
        if type(value) is not int or not 0 < value <= maximum:
            raise ValueError('invalid manifest bound')
    chunks = []
    paths = set()
    for part in manifest['parts']:
        path = relative(part['path'])
        if str(path) in paths:
            raise ValueError('duplicate part')
        paths.add(str(path))
        file = base/path
        if file.is_symlink():
            raise ValueError('part must not be a symlink')
        data = file.read_bytes()
        if len(data) != part['bytes'] or digest(data) != part['sha256']:
            raise ValueError('part integrity mismatch')
        chunks.append(data)
    encoded = b''.join(chunks)
    if len(encoded) != manifest['archive_bytes'] or digest(encoded) != manifest['archive_sha256']:
        raise ValueError('archive integrity mismatch')
    decoder = lzma.LZMADecompressor(memlimit=256000000)
    raw = decoder.decompress(encoded, max_length=manifest['tar_bytes']+1)
    if len(raw) != manifest['tar_bytes'] or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid bounded expansion')
    entries = members(raw, manifest['member_files'], manifest['member_bytes'])
    by_name = dict(entries)
    if digest(by_name['SHA256SUMS.json']) != manifest['original_manifest_sha256']:
        raise ValueError('original manifest identity mismatch')
    for readable, original in manifest['readable_copies'].items():
        relative(readable)
        relative(original)
        if (base/readable).read_bytes() != by_name[original]:
            raise ValueError('readable source copy differs')
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in entries:
        output = destination/relative(name)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(data)
    return destination

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    result = restore(ROOT, args.destination)
    print(json.dumps({'restored': str(result), 'scientific_actor_reruns': 0}, sort_keys=True))

if __name__ == '__main__':
    main()
