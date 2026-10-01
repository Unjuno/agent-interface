"""Restore retained research bytes; never import or execute an allocation.

Use a fresh destination under a trusted parent. Source and destination must not
be mutated concurrently. Digests establish byte integrity, not authenticity.
"""
from __future__ import annotations

import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import struct
import sys

MAX_PACK = 1_048_576
MAX_EXPANDED = 4_194_304
MAX_FILES = 1000


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def integer(value: object, limit: int) -> int:
    require(type(value) is int and 0 <= value <= limit, 'invalid bounded integer')
    return value


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded(path: Path, limit: int) -> bytes:
    require(path.is_file() and not path.is_symlink(), 'source is not a regular file')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, 'source size exceeds cap')
    return data


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field')
        result[key] = value
    return result


def load_members(source: Path) -> dict[str, bytes]:
    manifest = json.loads(read_bounded(source / 'PACK.json', 65536),
                          object_pairs_hook=unique_object)
    require(isinstance(manifest, dict), 'manifest must be an object')
    require(manifest.get('format') == 'length-prefixed-file-map-xz-v1', 'unknown format')
    parts = manifest['parts']
    require(type(parts) is list and 1 <= len(parts) <= 99, 'invalid part count')
    chunks = []
    total = 0
    for index, part in enumerate(parts, 1):
        require(type(part) is dict, 'invalid part entry')
        require(part['name'] == f'evidence.part{index:02d}', 'part order or name mismatch')
        size = integer(part['bytes'], MAX_PACK)
        total += size
        require(total <= MAX_PACK, 'compressed size exceeds cap')
        chunk = read_bounded(source / part['name'], size)
        require(len(chunk) == size and digest(chunk) == part['sha256'], 'part integrity mismatch')
        git_id = hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + chunk).hexdigest()
        require(git_id == part['git_blob'], 'Git blob mismatch')
        chunks.append(chunk)
    packed = b''.join(chunks)
    require(len(packed) == integer(manifest['compressed_bytes'], MAX_PACK), 'compressed length mismatch')
    require(digest(packed) == manifest['compressed_sha256'], 'compressed digest mismatch')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=134_217_728)
    expanded = decoder.decompress(packed, max_length=MAX_EXPANDED + 1)
    require(len(expanded) <= MAX_EXPANDED and decoder.eof and not decoder.unused_data,
            'truncated, oversized or trailing compressed data')
    require(len(expanded) == integer(manifest['expanded_bytes'], MAX_EXPANDED), 'expanded length mismatch')
    require(digest(expanded) == manifest['expanded_sha256'], 'expanded digest mismatch')
    require(len(expanded) >= 4, 'missing header')
    header_size = struct.unpack('>I', expanded[:4])[0]
    require(0 < header_size <= 131072 and 4 + header_size <= len(expanded), 'invalid header size')
    index = json.loads(expanded[4:4 + header_size])
    require(type(index) is list and len(index) == integer(manifest['file_count'], MAX_FILES),
            'file count mismatch')
    offset = 4 + header_size
    members = {}
    for entry in index:
        require(type(entry) is list and len(entry) == 2, 'invalid member entry')
        name, size = entry
        require(type(name) is str and 0 < len(name) <= 1024, 'invalid member name')
        path = PurePosixPath(name)
        require(not path.is_absolute() and path.as_posix() == name and
                all(p not in ('', '.', '..') for p in name.split('/')) and
                '\\' not in name and ':' not in name and '\0' not in name,
                'unsafe member name')
        require(name not in members, 'duplicate member')
        size = integer(size, MAX_EXPANDED)
        require(offset + size <= len(expanded), 'truncated member')
        members[name] = expanded[offset:offset + size]
        offset += size
    require(offset == len(expanded), 'trailing member bytes')
    require(sum(map(len, members.values())) == integer(manifest['file_bytes'], MAX_EXPANDED),
            'member byte count mismatch')
    for name in members:
        require(all(str(parent) not in members for parent in PurePosixPath(name).parents
                    if str(parent) != '.'), 'file/directory prefix collision')
    require('SHA256SUMS' in members and 'AUDIT.json' in members, 'missing original manifest or audit')
    checked = set()
    for line in members['SHA256SUMS'].decode('utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        require(match is not None, 'malformed original checksum line')
        expected, name = match.groups()
        require(name in members and name not in checked and name != 'SHA256SUMS',
                'invalid original checksum member')
        require(digest(members[name]) == expected, 'original member digest mismatch')
        checked.add(name)
    require(checked == set(members) - {'SHA256SUMS'}, 'original checksum coverage mismatch')
    require(digest(members['AUDIT.json']) == manifest['original_audit_sha256'], 'original audit mismatch')
    return members


def restore(source: Path, destination: Path) -> int:
    require(not destination.exists() and not destination.is_symlink(), 'destination already exists')
    members = load_members(source)
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in members.items():
        target = destination.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    print(json.dumps({'restored_files': len(members),
                      'restored_bytes': sum(map(len, members.values())),
                      'executed_allocations': 0}, sort_keys=True))
    return len(members)


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 2, 'usage: python -B unpack.py FRESH_DESTINATION')
        restore(Path(__file__).resolve().parent, Path(sys.argv[1]))
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError) as error:
        print(f'RESTORE_REFUSED: {error}', file=sys.stderr)
        raise SystemExit(2)
