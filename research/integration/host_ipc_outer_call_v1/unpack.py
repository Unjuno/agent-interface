"""Restore the retained #4081 evidence. Never run an experiment or overwrite output.

Trust the publication directory and destination parent; concurrent mutation of
those directories is outside this offline extraction contract.
"""
from __future__ import annotations

import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

MAX_PACK = 20000
MAX_PART = 6000
MAX_XZ = 95408
MAX_TAR = 1269760
MAX_FILES = 822
MAX_CONTENT = 669923


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def bounded(path: Path, maximum: int) -> bytes:
    require(path.is_file() and not path.is_symlink(), 'not a regular publication file')
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, 'file size limit')
    return data


def restore(source: Path, output: Path) -> dict:
    require(not output.exists() and not output.is_symlink(), 'destination already exists')
    pack = strict(bounded(source / 'PACK.json', MAX_PACK))
    for key, expected in [('version', 1), ('xz_size', MAX_XZ), ('tar_size', MAX_TAR),
                          ('members', MAX_FILES), ('content_size', MAX_CONTENT)]:
        require(type(pack.get(key)) is int and pack[key] == expected, 'invalid ' + key)
    require(type(pack.get('parts')) is list and len(pack['parts']) == 16, 'part count')
    pieces = []
    for index, part in enumerate(pack['parts']):
        require(type(part) is dict, 'part object')
        name = 'evidence-%02d.part' % index
        size = MAX_PART if index < 15 else 5408
        require(part.get('name') == name, 'part order/name')
        require(type(part.get('size')) is int and part['size'] == size, 'part size')
        raw = bounded(source / name, size)
        require(len(raw) == size and sha(raw) == part.get('sha256'), 'part integrity')
        pieces.append(raw)
    compressed = b''.join(pieces)
    require(len(compressed) == MAX_XZ and sha(compressed) == pack.get('xz_sha256'), 'XZ integrity')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=256 * 1024 * 1024)
    tar_bytes = decoder.decompress(compressed, max_length=MAX_TAR + 1)
    require(len(tar_bytes) == MAX_TAR and decoder.eof and not decoder.unused_data, 'XZ extent')
    require(sha(tar_bytes) == pack.get('tar_sha256'), 'TAR integrity')
    files = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r:') as archive:
        for member in archive:
            require(len(files) < MAX_FILES, 'member count limit')
            name = member.name
            path = PurePosixPath(name)
            require(member.isfile() and not member.issym() and not member.islnk(), 'member type')
            require(name and not path.is_absolute() and path.as_posix() == name
                    and all(p not in ('..', '.') for p in path.parts)
                    and '\\' not in name and ':' not in name and name not in files, 'member name')
            require(0 <= member.size <= MAX_CONTENT - total, 'content limit')
            stream = archive.extractfile(member)
            require(stream is not None, 'missing member stream')
            with stream:
                data = stream.read(member.size + 1)
            require(len(data) == member.size, 'member extent')
            files[name] = data
            total += len(data)
    require(len(files) == MAX_FILES and total == MAX_CONTENT, 'archive denominator')
    require(sha(files['MANIFEST.json']) == pack.get('manifest_sha256'), 'manifest identity')
    manifest = strict(files['MANIFEST.json'])
    require(type(manifest) is dict and set(manifest) == set(files) - {'MANIFEST.json'}, 'manifest coverage')
    for name, digest in manifest.items():
        require(sha(files[name]) == digest, 'member digest: ' + name)
    # Reject file/directory prefix collisions before making the output directory.
    for name in files:
        require(all(p.as_posix() not in files for p in PurePosixPath(name).parents), 'path collision')
    output.mkdir(parents=False, exist_ok=False)
    for name, data in files.items():
        target = output.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    return {'restored_files': len(files), 'original_bytes': total,
            'xz_sha256': sha(compressed), 'experiments_executed': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B unpack.py <new-output-directory>')
    try:
        result = restore(Path(__file__).resolve().parent, Path(sys.argv[1]))
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError, tarfile.TarError) as error:
        raise SystemExit('STOP_EVIDENCE_RESTORE: ' + str(error)) from error
    print(json.dumps(result, sort_keys=True))
