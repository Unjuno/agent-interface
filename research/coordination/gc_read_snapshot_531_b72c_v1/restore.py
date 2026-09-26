"""Restore saved b72c primary evidence; never execute a scientific allocation.

The destination and its parent are trusted and quiescent. This is an integrity
checker for this fixed publication, not a sandbox for hostile filesystems.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

ARCHIVE_SHA256 = '074fde64ac7c6d28ec16e31fe32b69dc1391613e9039b49b45bb8a9da2eb0f87'
MANIFEST_SHA256 = '7acb2e5b84ba718170570edb5671ea0b7cd231b00a19b963608e0f09453b21d4'
EXCLUDED = 'PREDECESSOR_A61E.tar.xz'
EXCLUDED_SHA256 = 'fc406d0cbdf58fc46dc6fd0f7620bb3315c9d29ac0ec3fba0313745e4a7b6a65'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def decode(root: Path) -> dict[str, bytes]:
    """Validate the complete capsule in memory before any destination writes."""
    meta = json.loads((root / 'CAPSULE.json').read_text(encoding='utf-8'))
    require(meta['schema'] == 'b72c-primary-capsule-v1', 'SCHEMA')
    require(type(meta['file_count']) is int and meta['file_count'] == 917, 'FILE_COUNT')
    require(meta['archive_bytes'] == 80776 and meta['tar_bytes'] == 10158080, 'EXTENT')
    require(meta['archive_sha256'] == ARCHIVE_SHA256, 'ARCHIVE_IDENTITY')
    require(meta['original_manifest_sha256'] == MANIFEST_SHA256, 'MANIFEST_IDENTITY')
    require(meta['excluded_ancestor'] == {'path': EXCLUDED, 'bytes': 104924,
                                        'sha256': EXCLUDED_SHA256}, 'EXCLUSION')
    require([p['name'] for p in meta['parts']] ==
            [f'capsule-{i:02d}.bin' for i in range(7)], 'PART_ORDER')
    chunks = []
    for i, part in enumerate(meta['parts']):
        size = 12288 if i < 6 else 7048
        with (root / part['name']).open('rb') as stream:
            chunk = stream.read(size + 1)
        require(type(part['bytes']) is int and part['bytes'] == size == len(chunk), 'PART_SIZE')
        require(sha(chunk) == part['sha256'], 'PART_HASH')
        chunks.append(chunk)
    compressed = b''.join(chunks)
    require(sha(compressed) == ARCHIVE_SHA256, 'ARCHIVE_HASH')
    decoder = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
    raw = decoder.decompress(compressed, max_length=10158081)
    require(decoder.eof and not decoder.unused_data and len(raw) == 10158080, 'EXPANSION')
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for item in archive:
            name = item.name
            path = PurePosixPath(name)
            require(item.isfile() and not path.is_absolute() and '..' not in path.parts
                    and str(path) == name and '\\' not in name and name not in files,
                    'MEMBER_PATH_OR_KIND')
            require(len(files) < 917 and 0 <= item.size <= 3000000, 'MEMBER_LIMIT')
            stream = archive.extractfile(item)
            require(stream is not None, 'MEMBER_MISSING')
            files[name] = stream.read()
    require(len(files) == 917 and sum(map(len, files.values())) == 9602807, 'MEMBERS')
    require(sha(files['MANIFEST.json']) == MANIFEST_SHA256, 'ORIGINAL_MANIFEST_HASH')
    original = json.loads(files['MANIFEST.json'])
    require(original['file_count'] == 917, 'ORIGINAL_COUNT')
    expected = original['files']
    require(expected[EXCLUDED] == {'bytes': 104924, 'sha256': EXCLUDED_SHA256}, 'ANCESTOR_ID')
    require(set(files) == (set(expected) - {EXCLUDED}) | {'MANIFEST.json'}, 'INVENTORY')
    for name, data in files.items():
        if name == 'MANIFEST.json':
            continue
        require(len(data) == expected[name]['bytes'] and sha(data) == expected[name]['sha256'],
                'ORIGINAL_MEMBER_HASH:' + name)
    for name in ('actor.py', 'audit.py', 'REPORT.md', 'PREREG.md', 'AUDIT.json', 'FREEZE.json'):
        require((root / name).read_bytes() == files[name], 'READABLE_SOURCE_PARITY:' + name)
    return files


def restore(root: Path, destination: Path) -> dict[str, object]:
    require(not destination.exists() and not destination.is_symlink(), 'DESTINATION_EXISTS')
    files = decode(root)
    destination.mkdir(parents=False, exist_ok=False)
    for name, data in files.items():
        output = destination / name
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(data)
    return {'restored_files': len(files), 'original_manifest_entries_verified': 916,
            'excluded_ancestor': EXCLUDED, 'scientific_processes_started': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).resolve().parent, args.out), sort_keys=True))


if __name__ == '__main__':
    main()
