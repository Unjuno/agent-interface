"""Verify/extract retained evidence only; never runs a formal experiment."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'MANIFEST.json').read_text())
    archive = manifest['archive']
    pieces = []
    for part in archive['parts']:
        data = (root / part['path']).read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('Archive part identity mismatch: ' + part['path'])
        pieces.append(data)
    data = b''.join(pieces)
    if len(data) != archive['bytes'] or hashlib.sha256(data).hexdigest() != archive['sha256']:
        raise ValueError('Full archive identity mismatch')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as bundle:
        members = bundle.getmembers()
        names = [member.name for member in members]
        if len(members) != archive['file_count'] or len(set(names)) != len(names):
            raise ValueError('Archive member cardinality mismatch')
        for member in members:
            p = PurePosixPath(member.name)
            if not member.isfile() or p.is_absolute() or '..' in p.parts or p.parts[0] not in {'allocation01', 'allocation02'}:
                raise ValueError('Unsafe archive member: ' + member.name)
        # Validate all named critical bytes before creating the output directory.
        for name, expected in manifest['files'].items():
            stream = bundle.extractfile(name)
            if stream is None:
                raise ValueError('Missing evidence: ' + name)
            content = stream.read()
            if len(content) != expected['bytes'] or hashlib.sha256(content).hexdigest() != expected['sha256']:
                raise ValueError('Evidence identity mismatch: ' + name)
        args.out.mkdir(parents=True, exist_ok=False)
        bundle.extractall(args.out, filter='data')
    print(json.dumps({'archive_sha256': archive['sha256'], 'files': len(members),
                      'critical_files_verified': len(manifest['files']),
                      'result': 'PASS_BYTE_RETENTION_ONLY',
                      'allocation01': manifest['allocations']['allocation01'],
                      'allocation02': manifest['allocations']['allocation02']}))


if __name__ == '__main__':
    main()
