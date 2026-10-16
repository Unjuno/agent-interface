#!/usr/bin/env python3
"""Verify and extract retained research bytes; never execute an experiment."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

ROOTS = {
    'research/live_control/scheduler_other_core_2547_caas_v1',
    'research/live_control/scheduler_pause_coverage_316_v1',
    'research/live_control/scheduler_pause_coverage_316_v2',
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def validate_members(raw: bytes, expected: dict) -> list[tuple[str, bytes]]:
    """Validate every member before creating the destination."""
    records = []
    names = set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        members = archive.getmembers()
        require(len(members) == expected['files'], 'member count mismatch')
        for member in members:
            path = PurePosixPath(member.name)
            require(member.isfile(), 'non-regular member')
            require(not path.is_absolute() and '..' not in path.parts,
                    'invalid member path')
            require(str(path) == member.name and len(path.parts) >= 4,
                    'noncanonical member path')
            require('/'.join(path.parts[:3]) in ROOTS, 'unowned member root')
            require(member.name not in names, 'duplicate member')
            require(0 <= member.size <= expected['raw_bytes'], 'member size')
            names.add(member.name)
            stream = archive.extractfile(member)
            require(stream is not None, 'missing member bytes')
            data = stream.read(expected['raw_bytes'] + 1)
            require(len(data) == member.size, 'truncated member')
            records.append((member.name, data))
    require(sum(len(data) for _, data in records) == expected['raw_bytes'],
            'total byte count mismatch')
    inventory = ''.join(f'{digest(data)}  {name}\n'
                        for name, data in sorted(records)).encode('utf-8')
    require(digest(inventory) == expected['inventory_sha256'],
            'exact member inventory mismatch')
    return records

def load_records(source: Path) -> tuple[list[tuple[str, bytes]], dict]:
    manifest = json.loads((source / 'MANIFEST.json').read_text())
    require(manifest['schema'] == 'pause-coverage-publication-v1', 'schema')
    chunks = []
    for part in manifest['parts']:
        name = part['path']
        require(Path(name).name == name, 'invalid part path')
        data = (source / name).read_bytes()
        require(len(data) == part['bytes'] and digest(data) == part['sha256'],
                'part integrity: ' + name)
        chunks.append(data)
    packed = b''.join(chunks)
    require(len(packed) == manifest['xz_bytes'] and
            digest(packed) == manifest['xz_sha256'], 'archive integrity')
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    raw = decoder.decompress(packed, max_length=manifest['tar_bytes'] + 1)
    require(decoder.eof and not decoder.unused_data, 'incomplete/extra stream')
    require(len(raw) == manifest['tar_bytes'] and
            digest(raw) == manifest['tar_sha256'], 'tar integrity')
    return validate_members(raw, manifest), manifest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    records, manifest = load_records(Path(__file__).resolve().parent)
    require(not args.out.exists() and not args.out.is_symlink(),
            'output already exists; never overwrite evidence')
    args.out.mkdir(parents=True, exist_ok=False)
    for name, data in records:
        dest = args.out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as handle:
            handle.write(data)
    print(json.dumps({'status': 'PASS_BYTE_RESTORE', 'files': len(records),
                      'raw_bytes': manifest['raw_bytes'],
                      'inventory_sha256': manifest['inventory_sha256'],
                      'experiment_executed': False}, sort_keys=True))

if __name__ == '__main__':
    main()
