#!/usr/bin/env python3
"""Restore exact frozen source and result files; does not run the primary study."""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


def restore(publication: Path, destination: Path) -> None:
    bundles = []
    seen = set()
    for manifest_name in ('SOURCE_MANIFEST.json', 'RESULT_MANIFEST.json'):
        manifest = json.loads((publication / manifest_name).read_text())
        encoded = []
        for name, meta in sorted(manifest['parts'].items()):
            if Path(name).name != name:
                raise ValueError('invalid part path')
            raw = (publication / name).read_bytes()
            if len(raw) != meta['bytes'] or hashlib.sha256(raw).hexdigest() != meta['sha256']:
                raise ValueError('part mismatch: ' + name)
            encoded.append(b''.join(raw.split()))
        data = base64.b64decode(b''.join(encoded), validate=True)
        if len(data) != manifest['bytes'] or hashlib.sha256(data).hexdigest() != manifest['sha256']:
            raise ValueError('archive mismatch')
        restored = {}
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                if not member.isfile() or path.is_absolute() or '..' in path.parts or member.name in seen:
                    raise ValueError('invalid or duplicate member')
                if member.size > 8_000_000:
                    raise ValueError('unexpected member size')
                content = archive.extractfile(member).read()
                if isinstance(manifest['members'], dict):
                    if hashlib.sha256(content).hexdigest() != manifest['members'][member.name]:
                        raise ValueError('result member mismatch')
                restored[member.name] = content
                seen.add(member.name)
        expected_count = manifest['members'] if isinstance(manifest['members'], int) else len(manifest['members'])
        if len(restored) != expected_count:
            raise ValueError('member count mismatch')
        bundles.append(restored)
    destination.mkdir(parents=True, exist_ok=False)
    for bundle in bundles:
        for name, content in bundle.items():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(content)
    freeze = json.loads((destination / 'FREEZE.json').read_text())
    for name, metadata in freeze['files'].items():
        if hashlib.sha256((destination / name).read_bytes()).hexdigest() != metadata['sha256']:
            raise ValueError('frozen file mismatch: ' + name)
    print(json.dumps({'restored_files': len(seen), 'destination': str(destination),
                      'primary_executed': False}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path, help='New directory; must not exist')
    args = parser.parse_args()
    restore(Path(__file__).resolve().parent, args.destination)
