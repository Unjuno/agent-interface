"""Verify/extract retained evidence only. Never execute the study or overwrite."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_name(name: str) -> str:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or p.as_posix() != name or '\\' in name:
        raise ValueError('unsafe/noncanonical member name')
    return name


def restore(source: Path, destination: Path) -> dict:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('destination must not exist')
    package = json.loads((source / 'PACKAGE.json').read_bytes())
    if package['schema'] != 1 or package['allocation'] != 'owned-group-reap-3982-20260922-01':
        raise ValueError('package identity')
    encoded = []
    for index, part in enumerate(package['parts']):
        if part['path'] != f'evidence-{index:02}.b64':
            raise ValueError('fragment order/identity')
        path = source / part['path']
        if path.is_symlink():
            raise ValueError('fragment symlink not permitted')
        data = path.read_bytes()
        if len(data) != part['bytes'] or digest(data) != part['sha256'] or not data.endswith(b'\n'):
            raise ValueError('fragment bytes/hash')
        encoded.append(data[:-1])
    archive = base64.b64decode(b''.join(encoded), validate=True)
    if len(archive) != package['archive_bytes'] or digest(archive) != package['archive_sha256']:
        raise ValueError('archive bytes/hash')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    tar_bytes = decoder.decompress(archive, max_length=16 * 1024 * 1024)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('archive expansion limit or trailing bytes')
    members = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r:') as tar:
        for entry in tar:
            name = checked_name(entry.name)
            if not entry.isfile() or name in members or entry.size > 8 * 1024 * 1024:
                raise ValueError('nonregular/duplicate/oversized member')
            handle = tar.extractfile(entry)
            if handle is None:
                raise ValueError('missing member content')
            members[name] = handle.read()
    manifest_bytes = members['MEMBER_MANIFEST.json']
    if digest(manifest_bytes) != package['member_manifest_sha256']:
        raise ValueError('member manifest digest')
    manifest = json.loads(manifest_bytes)
    if set(manifest) != set(members) - {'MEMBER_MANIFEST.json'}:
        raise ValueError('member set')
    for name, record in manifest.items():
        if len(members[name]) != record['bytes'] or digest(members[name]) != record['sha256']:
            raise ValueError('member bytes/hash: ' + name)
    if len(members) != package['member_count'] or sum(map(len, members.values())) != package['expanded_bytes']:
        raise ValueError('archive denominator')
    if digest(members['AUDIT.json']) != package['original_audit_sha256']:
        raise ValueError('audit binding')
    if digest(members['FREEZE.json']) != package['source_freeze_sha256']:
        raise ValueError('source freeze binding')
    # All archive contents are validated before creating anything at destination.
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in members.items():
        target = destination.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(data)
    return {'decision': 'PASS_PACKAGE_BYTES', 'members': len(members),
            'expanded_bytes': sum(map(len, members.values())),
            'archive_sha256': digest(archive), 'experiment_executed': False}


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: python unpack.py NEW_DESTINATION')
        result = restore(Path(__file__).resolve().parent, Path(sys.argv[1]))
        print(json.dumps(result, sort_keys=True, indent=2))
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError, tarfile.TarError) as error:
        print(json.dumps({'decision': 'STOP_PACKAGE', 'error': str(error)}), file=sys.stderr)
        raise SystemExit(2)
