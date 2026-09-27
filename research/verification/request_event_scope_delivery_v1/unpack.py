"""Restore byte-bound evidence only; never import or run retained study code.

Use a new output directory under a trusted, existing parent. Source and output
parents must not be concurrently modified. Hashes prove integrity, not origin.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import lzma
import tarfile
from pathlib import Path, PurePosixPath

MAX_ARCHIVE = 1_000_000
MAX_TAR = 8_000_000
MAX_FILES = 512
PREFIX = 'research/verification/request_effect_scope_34_20260922_v1/'

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def safe_path(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\0' in name:
        raise ValueError('invalid member name')
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')) or str(p) != name:
        raise ValueError('non-canonical member path')
    return p

def integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid integer bound')
    return value

def load_members(source: Path) -> list[tuple[str, bytes]]:
    manifest_path = source / 'PACK.meta.b64'
    if manifest_path.stat().st_size != 6929 or manifest_path.is_symlink():
        raise ValueError('encoded manifest size/type mismatch')
    encoded = manifest_path.read_bytes()
    if sha(encoded) != 'b9c8b4030fedfa64837efd6eeaf8c1ef025c52333662d469e9299369eca1ba4d':
        raise ValueError('encoded manifest hash mismatch')
    packed_manifest = base64.b64decode(encoded.rstrip(b'\n'), validate=True)
    md = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    manifest = md.decompress(packed_manifest, max_length=200_001)
    if (len(manifest) != 27176 or not md.eof or md.unused_data or
            sha(manifest) != '650fee94ec02b8287e83705a923a53201683d021309a9d1b2a2d0f6c69535ca0'):
        raise ValueError('manifest byte mismatch')
    m = json.loads(manifest)
    if type(m.get('schema')) is not int or m['schema'] != 1:
        raise ValueError('unknown manifest schema')
    archive_size = integer(m['archive_bytes'], 1, MAX_ARCHIVE)
    tar_size = integer(m['tar_bytes'], 1, MAX_TAR)
    count = integer(m['file_count'], 1, MAX_FILES)
    total = integer(m['file_bytes'], 1, MAX_TAR)
    if type(m['parts']) is not list or not 1 <= len(m['parts']) <= 64:
        raise ValueError('invalid parts')
    chunks = []
    seen_parts = set()
    cumulative = 0
    for entry in m['parts']:
        name = str(safe_path(entry['path']))
        if '/' in name or name in seen_parts:
            raise ValueError('duplicate or nested part')
        seen_parts.add(name)
        n = integer(entry['bytes'], 1, MAX_ARCHIVE)
        part = source / name
        if part.is_symlink() or part.stat().st_size != n:
            raise ValueError('part size/type mismatch')
        data = part.read_bytes()
        if sha(data) != entry['sha256']:
            raise ValueError('part hash mismatch')
        if not data.endswith(b'\n') or b'\n' in data[:-1]:
            raise ValueError('part framing mismatch')
        decoded = base64.b64decode(data[:-1], validate=True)
        if len(decoded) != integer(entry['decoded_bytes'], 1, MAX_ARCHIVE):
            raise ValueError('decoded size mismatch')
        cumulative += len(decoded)
        if cumulative > archive_size:
            raise ValueError('archive overflow')
        chunks.append(decoded)
    packed = b''.join(chunks)
    if len(packed) != archive_size or sha(packed) != m['archive_sha256']:
        raise ValueError('archive mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(packed, max_length=tar_size + 1)
    if (len(raw) != tar_size or not decoder.eof or decoder.unused_data or
            sha(raw) != m['tar_sha256']):
        raise ValueError('expanded archive mismatch')
    if type(m['members']) is not list or len(m['members']) != count:
        raise ValueError('manifest cardinality mismatch')
    expected = {}
    for entry in m['members']:
        name = str(safe_path(entry['path']))
        if not name.startswith(PREFIX) or name in expected:
            raise ValueError('wrong scope or duplicate member')
        integer(entry['bytes'], 0, MAX_TAR)
        expected[name] = entry
    result = []
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for item in archive:
            name = str(safe_path(item.name))
            if not item.isfile() or item.linkname or item.pax_headers or name in seen or name not in expected:
                raise ValueError('unexpected archive member/type')
            spec = expected[name]
            if item.size != spec['bytes']:
                raise ValueError('member size mismatch')
            handle = archive.extractfile(item)
            if handle is None:
                raise ValueError('missing member data')
            data = handle.read()
            if len(data) != spec['bytes'] or sha(data) != spec['sha256']:
                raise ValueError('member digest mismatch')
            result.append((name, data))
            seen.add(name)
    if len(result) != count or seen != set(expected) or sum(len(b) for _, b in result) != total:
        raise ValueError('member inventory mismatch')
    return result

def restore(source: Path, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise ValueError('output already exists')
    parent = output.parent.resolve(strict=True)
    destination = parent / output.name
    members = load_members(source)
    destination.mkdir(exist_ok=False)
    for name, data in members:
        path = destination.joinpath(*PurePosixPath(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(data)
    return {'files': len(members), 'bytes': sum(len(b) for _, b in members),
            'output': str(destination), 'study_executed': False}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent, args.output), sort_keys=True))

if __name__ == '__main__':
    main()
