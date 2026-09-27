"""Restore retained data only. Never import or execute experiment modules."""
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import sys


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def integer(value, limit):
    if type(value) is not int or not 0 <= value <= limit:
        raise ValueError('invalid size')
    return value


def checked(data, size, digest):
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('byte identity mismatch')
    return data


def restore(root, destination):
    root, destination = Path(root), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination must be absent')
    raw_manifest = (root / 'CAPSULE.json').read_bytes()
    if len(raw_manifest) > 32768:
        raise ValueError('manifest too large')
    meta = json.loads(raw_manifest, object_pairs_hook=unique)
    if meta['schema'] != 'retained-utf8-map-xz-v1':
        raise ValueError('unknown schema')
    size = integer(meta['compressed_bytes'], 1000000)
    expanded_size = integer(meta['expanded_bytes'], 2000000)
    count = integer(meta['file_count'], 1000)
    total = integer(meta['file_bytes'], 2000000)
    parts = meta['parts']
    if not isinstance(parts, list) or not 1 <= len(parts) <= 32:
        raise ValueError('invalid part count')
    chunks = []
    for index, part in enumerate(parts, 1):
        if part['name'] != f'evidence.part{index:02d}.xz':
            raise ValueError('invalid part order/name')
        n = integer(part['bytes'], 65536)
        with (root / part['name']).open('rb') as source:
            data = source.read(n + 1)
        chunks.append(checked(data, n, part['sha256']))
    compressed = checked(b''.join(chunks), size, meta['compressed_sha256'])
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    expanded = decoder.decompress(compressed, max_length=expanded_size + 1)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('incomplete or extra compressed stream')
    checked(expanded, expanded_size, meta['expanded_sha256'])
    files = json.loads(expanded.decode('utf8'), object_pairs_hook=unique)
    if not isinstance(files, dict) or len(files) != count:
        raise ValueError('wrong file count')
    data_files = {}
    for name, text in files.items():
        if (not isinstance(name, str) or not name or len(name) > 512
                or not re.fullmatch(r'[A-Za-z0-9_./-]+', name)
                or not isinstance(text, str)):
            raise ValueError('invalid member')
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name:
            raise ValueError('invalid member path')
        if any(str(parent) in files for parent in path.parents if str(parent) != '.'):
            raise ValueError('file/directory collision')
        data_files[name] = text.encode('utf8')
    if sum(map(len, data_files.values())) != total:
        raise ValueError('wrong member bytes')
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in sorted(data_files.items()):
        target = destination.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as out:
            out.write(data)
    return {'files': count, 'file_bytes': total,
            'capsule_sha256': meta['compressed_sha256'], 'experiment_executed': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -B restore.py ABSENT_OUTPUT_DIRECTORY')
    print(json.dumps(restore(Path(__file__).resolve().parent, sys.argv[1]), sort_keys=True))
