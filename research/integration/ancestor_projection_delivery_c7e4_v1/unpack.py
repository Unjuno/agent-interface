"""Data-only, bounded restoration of the retained #4317 evidence.

The destination parent is trusted. No study source is executed by this module.
"""
from __future__ import annotations
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile

MAX_COMPRESSED = 200_000
MAX_TAR = 4_000_000
MAX_FILES = 500


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(name: str) -> Path:
    if type(name) is not str or not name or '\\' in name or ':' in name:
        raise ValueError('noncanonical path')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p) != name:
        raise ValueError('noncanonical path')
    return Path(*p.parts)


def integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid integer')
    return value


def hexhash(value: object) -> str:
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('invalid sha256')
    return value


def unique(pairs: list) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON member')
        out[key] = value
    return out


def load_members(source: Path) -> dict[str, bytes]:
    meta = json.loads((source / 'EVIDENCE_MANIFEST.json').read_text(), object_pairs_hook=unique)
    if meta['format'] != 'xz-ustar-parts-v1':
        raise ValueError('format mismatch')
    size = integer(meta['archive_bytes'], 1, MAX_COMPRESSED)
    tar_size = integer(meta['tar_bytes'], 1, MAX_TAR)
    count = integer(meta['files'], 1, MAX_FILES)
    member_bytes = integer(meta['member_bytes'], 0, MAX_TAR)
    parts = meta['parts']
    if type(parts) is not list or not 1 <= len(parts) <= 64:
        raise ValueError('invalid part count')
    pieces = []
    names = set()
    total = 0
    for part in parts:
        name = part['path']
        rel = relative(name)
        if name in names or rel.parts[0] != 'capsule':
            raise ValueError('duplicate or misplaced part')
        names.add(name)
        n = integer(part['bytes'], 1, MAX_COMPRESSED)
        total += n
        if total > size:
            raise ValueError('excess part bytes')
        path = source / rel
        if path.is_symlink() or not path.is_file() or path.stat().st_size != n:
            raise ValueError('missing or invalid part')
        data = path.read_bytes()
        if digest(data) != hexhash(part['sha256']):
            raise ValueError('part digest mismatch')
        pieces.append(data)
    packed = b''.join(pieces)
    if len(packed) != size or digest(packed) != hexhash(meta['archive_sha256']):
        raise ValueError('archive mismatch')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=128_000_000)
    expanded = decoder.decompress(packed, max_length=tar_size + 1)
    if len(expanded) != tar_size or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid or excessive expansion')
    members = {}
    aggregate = 0
    with tarfile.open(fileobj=io.BytesIO(expanded), mode='r:') as archive:
        for member in archive:
            relative(member.name)
            if not member.isfile() or member.name in members or len(members) >= count:
                raise ValueError('nonregular or duplicate member')
            aggregate += integer(member.size, 0, member_bytes)
            if aggregate > member_bytes:
                raise ValueError('excess member bytes')
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError('missing member bytes')
            data = stream.read(member.size + 1)
            if len(data) != member.size:
                raise ValueError('member size mismatch')
            members[member.name] = data
    if len(members) != count or aggregate != member_bytes:
        raise ValueError('member inventory mismatch')
    return members


def restore(source: Path, destination: Path) -> dict:
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination exists')
    members = load_members(source)
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in members.items():
        path = destination / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {'files': len(members), 'member_bytes': sum(map(len, members.values())), 'executed_source': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -B unpack.py NEW_DESTINATION')
    print(json.dumps(restore(Path(__file__).resolve().parent, Path(sys.argv[1])), sort_keys=True))
