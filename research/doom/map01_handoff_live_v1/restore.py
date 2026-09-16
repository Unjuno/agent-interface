"""Restore retained source and JSON only. Never launches a live experiment."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

SOURCE_SHA = '9859fd21e6c89a4f11c00856e1f0e75df82f9f8a4a43ceac0ea8df6a2e51b7e8'
RECORD_XZ_SHA = 'ff6e737995c480a3da9adafec8f4533d8325f028a031056d62bfd40c0d9879cf'
RECORD_SHA = '07aefbbaf95333c84fbe0b0c9c4952486a6a70285538f76ebafd425fb048b3f1'
DISPATCH_SHA = 'c1a6c5c515557481081d19e799ee5471c93945b860983b6075a74fe520e223e5'


def checked(data: bytes, expected: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('retained digest mismatch')
    return data


def safe_name(name: str) -> str:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise ValueError('unsafe retained path')
    return str(p)


def restore(output: Path, package: Path) -> dict:
    if output.exists():
        raise FileExistsError('refuse existing output; retained results are immutable')
    source = checked(base64.b64decode((package / 'source.tar.gz.b64').read_bytes().strip(), validate=True), SOURCE_SHA)
    record_xz = checked(base64.b64decode((package / 'raw-json.json.xz.b64').read_bytes().strip(), validate=True), RECORD_XZ_SHA)
    raw = checked(lzma.decompress(record_xz), RECORD_SHA)
    records = json.loads(raw)['files']
    if len(records) != 96 or any(not isinstance(v, str) for v in records.values()):
        raise ValueError('unexpected record inventory')
    payload = {}
    with tarfile.open(fileobj=io.BytesIO(source), mode='r:gz') as archive:
        for member in archive:
            if not member.isfile():
                raise ValueError('source archive must contain ordinary files only')
            name = 'source/' + safe_name(member.name)
            if name in payload:
                raise ValueError('duplicate source path')
            payload[name] = archive.extractfile(member).read()
    if len(payload) != 9:
        raise ValueError('unexpected source inventory')
    payload['source/dispatch_one.py'] = checked((package / 'dispatch_one.py').read_bytes(), DISPATCH_SHA)
    for name, text in records.items():
        payload['formal/' + safe_name(name)] = text.encode('utf-8')
    prereg = json.loads(payload['source/prereg.json'])
    for name, digest in prereg['source_sha256'].items():
        checked(payload['source/' + safe_name(name)], digest)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in payload.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    return {'state': 'SOURCE_AND_JSON_RESTORED', 'source_files': 10, 'json_records': 96,
            'png_files': 0, 'full_audit': 'PNG_REQUIRED_USE_FULL_EVIDENCE_ARCHIVE',
            'live_experiments_executed': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(restore(args.output, Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, OSError, KeyError, tarfile.TarError, lzma.LZMAError) as error:
        parser.exit(1, f'restore refused: {error}\n')
