"""Bounded data-only restoration. Does not execute any archived source."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import lzma
import re
import sys
import tarfile

ARCHIVE_SHA = '029067b9a1e4bcb8a6fac3f210b33d542a06fc301091decbfea3bc75abb7cae7'
MANIFEST_SHA = '5f1cfc11d316e3d402a28c103cda7e7f83fc29326da0bf47da26f2e16fb69636'
ARCHIVE_BYTES, TAR_BYTES, FILE_BYTES, FILE_COUNT = 95988, 8192000, 7691784, 633


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name and '\x00' not in name, 'bad name')
    p = PurePosixPath(name)
    require(not p.is_absolute() and all(x not in ('', '.', '..') for x in p.parts)
            and str(p) == name, 'unsafe path')
    return p


def read_bounded(path, size):
    require(not path.is_symlink() and path.is_file(), 'not regular file')
    with path.open('rb') as f:
        data = f.read(size + 1)
    require(len(data) == size, 'file size')
    return data


def decode(source):
    source = Path(source)
    manifest_path = source / 'PACK.json'
    require(not manifest_path.is_symlink() and manifest_path.is_file(), 'not regular pack')
    with manifest_path.open('rb') as f:
        raw_manifest = f.read(16384)
    require(len(raw_manifest) < 16384, 'pack size')
    pack = json.loads(raw_manifest)
    for key, value in [('archive_bytes', ARCHIVE_BYTES), ('tar_bytes', TAR_BYTES),
                       ('file_bytes', FILE_BYTES), ('file_count', FILE_COUNT)]:
        require(type(pack.get(key)) is int and pack[key] == value, key)
    require(pack.get('format') == 'tar.xz' and pack.get('archive_sha256') == ARCHIVE_SHA
            and pack.get('sha256sums_sha256') == MANIFEST_SHA, 'pack identity')
    require(isinstance(pack.get('parts'), list) and len(pack['parts']) == 12, 'parts count')
    parts = []
    for index, spec in enumerate(pack['parts'], 1):
        expected = f'part-{index:02d}.bin'
        require(spec.get('file') == expected, 'part order/name')
        size = 8192 if index < 12 else 5876
        require(type(spec.get('size')) is int and spec['size'] == size, 'part size')
        data = read_bounded(source / expected, size)
        require(digest(data) == spec.get('sha256'), 'part digest')
        git_id = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        require(git_id == spec.get('git_blob'), 'part git identity')
        parts.append(data)
    archive = b''.join(parts)
    require(len(archive) == ARCHIVE_BYTES and digest(archive) == ARCHIVE_SHA, 'archive identity')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(archive, max_length=TAR_BYTES + 1)
    require(len(raw) == TAR_BYTES and decoder.eof and not decoder.unused_data, 'expansion bound')
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tf:
        for member in tf:
            name = str(safe_name(member.name))
            require(member.isfile() and not member.issym() and not member.islnk(), 'member kind')
            require(name not in result and len(result) < FILE_COUNT, 'duplicate/count')
            require(0 <= member.size <= FILE_BYTES, 'member size')
            f = tf.extractfile(member)
            require(f is not None, 'member absent')
            value = f.read(member.size + 1)
            require(len(value) == member.size, 'member short read')
            result[name] = value
    require(len(result) == FILE_COUNT and sum(map(len, result.values())) == FILE_BYTES, 'inventory')
    require(digest(result.get('SHA256SUMS', b'')) == MANIFEST_SHA, 'original manifest identity')
    seen = set()
    for line in result['SHA256SUMS'].decode('utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  (.+)', line)
        require(match is not None, 'manifest line')
        sha, name = match.groups()
        safe_name(name)
        require(name not in seen and name in result and name != 'SHA256SUMS', 'manifest member')
        require(digest(result[name]) == sha, 'member hash')
        seen.add(name)
    require(seen == set(result) - {'SHA256SUMS'}, 'manifest coverage')
    return result


def restore(source, destination):
    destination = Path(destination)
    require(not destination.exists() and not destination.is_symlink(), 'existing destination')
    data = decode(source)  # Validate all bytes and names before creating output.
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in data.items():
        path = destination.joinpath(*PurePosixPath(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(value)
    return data


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -B unpack.py NEW_PRIVATE_DIRECTORY')
    restored = restore(Path(__file__).resolve().parent, sys.argv[1])
    print(json.dumps({'files': len(restored), 'file_bytes': sum(map(len, restored.values())),
                      'archive_sha256': ARCHIVE_SHA, 'executed_archived_code': False}, sort_keys=True))
