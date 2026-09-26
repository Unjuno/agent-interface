"""Restore original Issue 3996 evidence only; never execute experiment code."""
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys

PARTS = (
    (3072, '02509210853c7cd7180cb1ef4ea1ef9860dc24e4'),
    (3072, '32c5ccfed080698cbcd89ea7925bfea91ff7c505'),
    (3072, '20559f5e27fc902b420cb6addf33b82bfc49885c'),
    (3072, '284c403b3c33ae0990db5c33e7bf8a58c3ef383d'),
    (3072, '486b6acbf564e2015c1a2dcd4525353f2f373f9a'),
    (1344, '3ff3c99aac1ccf5c23bb152d5977ffb0e98e66cc'),
)
BUNDLE_SHA = '20c954cf25578ed245c06c2c93bc8a72737779036b1ae2e7e1da95554df02ae2'
RAW_SHA = 'cd2f68f1360372c21307900e27f51614dcbba676f8dc66e7c29dee43a97cc904'
AUDIT_SHA = '6846066e8572c88a9ad48c68532640000400698f3dccd406cb0dd0b3293041f0'


def restore(destination):
    source = Path(__file__).resolve().parent / 'evidence'
    pieces = []
    for index, (length, expected) in enumerate(PARTS):
        with (source / f'EVIDENCE.{index:02d}.b64').open('rb') as stream:
            part = stream.read(length + 1)
        git_sha = hashlib.sha1(b'blob ' + str(len(part)).encode() + b'\0' + part).hexdigest()
        if len(part) != length or git_sha != expected:
            raise ValueError('PART_MISMATCH:' + str(index))
        pieces.append(part)
    packed = base64.b64decode(b''.join(pieces), validate=True)
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    data = decoder.decompress(packed, max_length=218046)
    if (len(data) != 218045 or not decoder.eof or decoder.unused_data
            or hashlib.sha256(data).hexdigest() != BUNDLE_SHA):
        raise ValueError('BUNDLE_MISMATCH')
    bundle = json.loads(data)
    if bundle['schema'] != 'issue3996-retained-files-v1' or len(bundle['files']) != 70:
        raise ValueError('BUNDLE_SCHEMA')
    files = {}
    for name, text in bundle['files'].items():
        path = PurePosixPath(name)
        if (path.is_absolute() or path.as_posix() != name
                or '..' in path.parts or '\\' in name or ':' in name
                or not isinstance(text, str)):
            raise ValueError('INVALID_MEMBER')
        files[name] = text.encode('utf-8')
    for name, expected in [('formal-01/raw.json', RAW_SHA), ('formal-AUDIT.json', AUDIT_SHA)]:
        if hashlib.sha256(files[name]).hexdigest() != expected:
            raise ValueError('EVIDENCE_MISMATCH:' + name)
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as output:
            output.write(value)
    return {'decision': 'PASS_LOSSLESS_RESTORATION', 'files': len(files),
            'bundle_sha256': BUNDLE_SHA, 'raw_sha256': RAW_SHA,
            'audit_sha256': AUDIT_SHA, 'formal_executions': 0}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B unpack.py NEW_DIRECTORY')
    try:
        print(json.dumps(restore(Path(sys.argv[1])), sort_keys=True, indent=2))
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError) as exc:
        print(json.dumps({'decision': 'STOP_RESTORATION', 'error': str(exc)}))
        raise SystemExit(2)
