"""Restore Issue 3989's retained UTF-8 evidence; never execute a study.

Use a fresh destination beneath a trusted, privately owned local directory.
This checks bounded content integrity, not publisher authenticity or durability.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath

XZ_SHA = '9b466fba115ab8fa322b5fd216c60e546fc8acc22c937cd169ed8aeb80a50aec'
JSON_SHA = '35e0a8db5078702c7ae3eab1c2ce303f5572e494a985201b8641f7573a511b7f'
XZ_BYTES, JSON_BYTES, FILE_BYTES, MEMBERS = 47900, 564773, 522570, 173
ROOTS = (
    'research/integration/event_reader_restart_boundary_20260922_v1/',
    'research/integration/event_reader_restart_checkpoint_bounded_20260922_v2/',
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def read_bounded(path: Path, limit: int) -> bytes:
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('READ_BOUND_EXCEEDED')
    return data


def validate_members(data: object) -> dict[str, bytes]:
    if type(data) is not dict or len(data) != MEMBERS:
        raise ValueError('MEMBER_COUNT')
    checked = {}
    for name, text in data.items():
        if not isinstance(name, str) or not isinstance(text, str):
            raise ValueError('MEMBER_TYPE')
        parts = name.split('/')
        if (not name.startswith(ROOTS) or '\\' in name or '\x00' in name
                or any(p in ('', '.', '..') for p in parts)
                or PurePosixPath(name).is_absolute()):
            raise ValueError('MEMBER_PATH')
        checked[name] = text.encode('utf-8')
    for name in checked:
        if any(str(parent) in checked for parent in PurePosixPath(name).parents):
            raise ValueError('FILE_DIRECTORY_COLLISION')
    if sum(map(len, checked.values())) != FILE_BYTES:
        raise ValueError('UNPACKED_BYTE_COUNT')
    return checked


def load(source: Path) -> dict[str, bytes]:
    manifest = json.loads(read_bounded(source / 'MANIFEST.json', 8192),
                          object_pairs_hook=unique)
    if (manifest.get('schema') != 'retrospective-evidence-publication-v1'
            or manifest.get('issue') != 3989
            or manifest.get('compressed_sha256') != XZ_SHA
            or manifest.get('json_sha256') != JSON_SHA
            or manifest.get('compressed_bytes') != XZ_BYTES
            or manifest.get('json_bytes') != JSON_BYTES
            or manifest.get('members') != MEMBERS
            or manifest.get('unpacked_bytes') != FILE_BYTES):
        raise ValueError('MANIFEST_IDENTITY')
    parts = manifest['parts']
    if type(parts) is not list or len(parts) != 8:
        raise ValueError('PART_COUNT')
    encoded = []
    for index, part in enumerate(parts, 1):
        name = f'evidence.{index:02d}.b64'
        if part['name'] != name:
            raise ValueError('PART_ORDER_OR_NAME')
        raw = read_bounded(source / name, 9001)
        git_id = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if (len(raw) != part['bytes'] or sha(raw) != part['sha256']
                or git_id != part['git_blob'] or not raw.endswith(b'\n')):
            raise ValueError('PART_IDENTITY')
        encoded.append(raw[:-1])
    compressed = base64.b64decode(b''.join(encoded), validate=True)
    if len(compressed) != XZ_BYTES or sha(compressed) != XZ_SHA:
        raise ValueError('COMPRESSED_IDENTITY')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=128 * 1024**2)
    raw_json = decoder.decompress(compressed, max_length=JSON_BYTES + 1)
    if (not decoder.eof or decoder.unused_data or len(raw_json) != JSON_BYTES
            or sha(raw_json) != JSON_SHA):
        raise ValueError('JSON_IDENTITY_OR_BOUND')
    return validate_members(json.loads(raw_json, object_pairs_hook=unique))


def restore(source: Path, destination: Path) -> dict:
    # Validate everything before creating the output. Never overwrite old evidence.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('DESTINATION_EXISTS')
    members = load(source)
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name, raw in members.items():
        target = destination.joinpath(*name.split('/'))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
    return {'status': 'RESTORED', 'members': len(members),
            'bytes': sum(map(len, members.values())), 'experiments_executed': 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        result = restore(Path(__file__).resolve().parent, args.destination)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, lzma.LZMAError) as error:
        print(json.dumps({'status': 'STOP_RESTORE', 'error': str(error)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
