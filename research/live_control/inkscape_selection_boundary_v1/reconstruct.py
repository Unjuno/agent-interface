"""Verify and restore retained evidence only; never starts a GUI or benchmark."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path, PurePosixPath


def safe_name(name: str) -> str:
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError(f'unsafe archive path: {name!r}')
    return str(p)


def restore(target: Path) -> None:
    home = Path(__file__).resolve().parent
    metadata = json.loads((home / 'manifest.json').read_text())
    archive = metadata['archive']
    blocks = []
    for part in archive['parts']:
        data = (home / safe_name(part['path'])).read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError(f"part digest mismatch: {part['path']}")
        blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        if blob != part['git_blob']:
            raise ValueError(f"Git object identity mismatch: {part['path']}")
        blocks.append(data)
    data = b''.join(blocks)
    if len(data) != archive['bytes'] or hashlib.sha256(data).hexdigest() != archive['sha256']:
        raise ValueError('archive identity mismatch')
    target.mkdir(parents=True, exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as tf:
        seen = set()
        for member in tf.getmembers():
            name = safe_name(member.name)
            if name in seen or not (member.isfile() or member.isdir()):
                raise ValueError('duplicate or unsupported archive entry')
            seen.add(name)
        tf.extractall(target, filter='data')
    manifest = json.loads((target / 'COMPACT_MANIFEST.json').read_text())
    for name, digest in manifest['files'].items():
        if hashlib.sha256((target / safe_name(name)).read_bytes()).hexdigest() != digest:
            raise ValueError(f'file digest mismatch: {name}')
    if len(manifest['files']) != archive['files_bound_by_compact_manifest']:
        raise ValueError('manifest count mismatch')
    print(json.dumps({'status': 'PASS_RECONSTRUCTION', 'files_verified': len(manifest['files']),
                      'output': str(target), 'gui_started': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    restore(parser.parse_args().output)
