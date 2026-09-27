"""Restore exact original Issue 3938 raw/audit bytes; never run an experiment."""
import base64
import hashlib
import json
import lzma
from pathlib import Path
import sys

PARTS = {
    'RAW.00.b64': '0c73d296bb24ae8740d241558e0d54a7b711e1d1',
    'RAW.01.b64': 'c5fd2a36c5b214c29df66c08c939685b5aa2ecaf',
    'RAW.02.b64': 'fdc5bf0693668175672e423c9aacdb9ad38aac87',
    'AUDIT.b64': 'aa16d54d2160d418717c840e66868a6f6161ce74',
}
EXPECTED = {
    'raw.json': (288509, 'eef12b6de49f12f34cc86dca0dcea0d66986ed739d9cfc3adf640c966b6a403a'),
    'AUDIT.json': (8138, 'b1625376ee177f8654f6053d8768117f4fcafe6169eefa5e62da9cec9dbe3766'),
}
SOURCES = {
    'run.py': 'e0a6f298031b5e4b4c1a1d1bb0a7522efc8fafdfbffaf3ea9729eabcd7265a57',
    'audit.py': '8a055b620746697b1043b33d060bb43aac0d1aa33235938f61f1e5121b37cbd7',
    'PLAN.md': '06d637441d9f779c79a987a99374fc8d14f749db2873d29a15f6e8008d14260a',
    'FREEZE.json': '019d94036b94b59844d582c73e5485d94e0cd64a339a2bc59ac78611ffe1ebc0',
}


def restore(destination: Path) -> dict:
    source = Path(__file__).resolve().parent
    for name, expected in SOURCES.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError('SOURCE_MISMATCH:' + name)
    parts = {}
    for name, expected in PARTS.items():
        data = (source / 'published' / name).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != expected:
            raise ValueError('PART_MISMATCH:' + name)
        parts[name] = data
    decoded = {}
    for name, names in [('raw.json', ['RAW.00.b64', 'RAW.01.b64', 'RAW.02.b64']),
                        ('AUDIT.json', ['AUDIT.b64'])]:
        packed = base64.b64decode(b''.join(parts[n] for n in names), validate=True)
        decoder = lzma.LZMADecompressor(memlimit=134217728)
        size, expected = EXPECTED[name]
        data = decoder.decompress(packed, max_length=size + 1)
        if (len(data) != size or not decoder.eof or decoder.unused_data
                or hashlib.sha256(data).hexdigest() != expected):
            raise ValueError('DECODED_MISMATCH:' + name)
        decoded[name] = data
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in decoded.items():
        with (destination / name).open('xb') as output:
            output.write(data)
    return {'decision': 'PASS_EXACT_BYTE_RESTORATION', 'files': EXPECTED,
            'formal_executions': 0, 'destination': str(destination)}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -S -B restore_evidence.py NEW_DIRECTORY')
    try:
        print(json.dumps(restore(Path(sys.argv[1])), sort_keys=True, indent=2))
    except (OSError, ValueError, lzma.LZMAError) as exc:
        print(json.dumps({'decision': 'STOP_RESTORATION', 'error': str(exc)}))
        raise SystemExit(2)
