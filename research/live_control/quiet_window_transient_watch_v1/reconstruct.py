"""Verify and unpack retained study data. Does not run GUI or benchmark code."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import lzma
from pathlib import Path


def safe_path(root: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'Unsafe relative path: {name!r}')
    return root / path


def checked(data: bytes, spec: dict, name: str) -> bytes:
    if len(data) != spec['bytes']:
        raise ValueError(f'Byte count mismatch: {name}')
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError(f'SHA-256 mismatch: {name}')
    return data


def load_archive(root: Path, name: str, spec: dict) -> dict:
    chunks = []
    for part in spec['parts']:
        data = checked(safe_path(root, part['file']).read_bytes(), part, part['file'])
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != part['git_blob']:
            raise ValueError(f'Git blob mismatch: {part["file"]}')
        chunks.append(data)
    data = checked(b''.join(chunks), spec, name)
    return json.loads(lzma.decompress(data).decode('utf-8'))


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='A new, non-existing directory')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text())
    evidence = load_archive(root, 'evidence.json.xz', manifest['evidence.json.xz'])
    sources = load_archive(root, 'sources.json.xz', manifest['sources.json.xz'])
    if evidence.get('format') != 'quiet-window-complete-evidence-v1':
        raise ValueError('Unexpected evidence format')
    if len(evidence['raw_cases']) != 48:
        raise ValueError('Incomplete measured allocation')
    # Check before creating output; never silently overwrite existing evidence.
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    study = args.output / 'study'
    for name, content in sources.items():
        path = safe_path(study, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    measured = args.output / 'measured-01'
    for row in evidence['raw_cases']:
        dump(safe_path(measured, row['name'] + '/raw.json'), row)
    for name, encoded in evidence['pixels_zlib_base64'].items():
        path = safe_path(measured / 'pixels', name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(encoded, validate=True))
    for name in ('environment', 'audit', 'result'):
        dump(measured / (name + '.json'), evidence[name])
    for name, expected in evidence['audit']['raw_hashes'].items():
        if hashlib.sha256(safe_path(measured, name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Original raw-file hash mismatch: {name}')
    prereg = json.loads((study / 'prereg.json').read_text())
    for name, expected in prereg['source_sha256'].items():
        if hashlib.sha256(safe_path(study, name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Frozen source hash mismatch: {name}')
    print('PASS: archives, original raw files, and frozen source hashes verified.')
    print('Offline audit (no GUI/model):')
    print(f'python {study / "audit.py"} {measured} {study}')


if __name__ == '__main__':
    main()
