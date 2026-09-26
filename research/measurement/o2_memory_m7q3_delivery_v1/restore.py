"""Restore exact retained files only. Does not run scientific or restored code."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import lzma
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def restore(source, destination):
    source, destination = Path(source), Path(destination)
    require(not destination.exists(), 'DESTINATION_EXISTS')
    meta = json.loads((source / 'CAPSULE.json').read_text())
    require(meta['schema'] == 'm7q3-complete-original-capsule-v1', 'SCHEMA')
    parts = meta['parts']
    require(len(parts) == 22, 'PART_COUNT')
    data = bytearray()
    for i, part in enumerate(parts):
        name = f'evidence/part-{i:02d}.bin'
        require(part['path'] == name, 'PART_ORDER')
        b = (source / name).read_bytes()
        require(len(b) <= 4096 and len(b) == part['bytes'], 'PART_LENGTH')
        require(sha(b) == part['sha256'], 'PART_DIGEST')
        data.extend(b)
    require(len(data) == 88088 == meta['archive_bytes'], 'ARCHIVE_LENGTH')
    require(sha(data) == meta['archive_sha256'], 'ARCHIVE_DIGEST')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(data, max_length=63467521)
    require(decoder.eof and not decoder.unused_data, 'ARCHIVE_END')
    require(len(raw) == 63467520 == meta['tar_bytes'], 'TAR_LENGTH')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            require(item.isfile() and not path.is_absolute(), 'FILE_KIND')
            require(str(path) == item.name and '..' not in path.parts, 'FILE_PATH')
            require(item.name not in files and 0 <= item.size <= 12000000, 'FILE_BOUNDS')
            require(len(files) < 457, 'FILE_COUNT')
            files[item.name] = archive.extractfile(item).read()
    require(len(files) == 457 == meta['original_files'], 'ORIGINAL_COUNT')
    require(sum(map(len, files.values())) == meta['original_bytes'], 'ORIGINAL_SIZE')
    manifest_bytes = files['SHA256SUMS.json']
    require(sha(manifest_bytes) == meta['original_manifest_sha256'], 'MANIFEST_DIGEST')
    manifest = json.loads(manifest_bytes)
    require(set(files) == set(manifest['members']) | {'SHA256SUMS.json'}, 'MEMBER_SET')
    require(manifest['member_count'] == 456, 'MANIFEST_COUNT')
    for name, entry in manifest['members'].items():
        b = files[name]
        require(len(b) == entry['bytes'] and sha(b) == entry['sha256'], 'MEMBER:' + name)
    require(sha(files['AUDIT.json']) == meta['audit_sha256'], 'AUDIT_DIGEST')
    # Caller supplies a trusted, quiescent parent. This is not a hostile-path sandbox.
    destination.mkdir(parents=True, exist_ok=False)
    for name, b in files.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as output:
            output.write(b)
    return {'status': 'RESTORED_EXACT_ORIGINAL', 'files': len(files),
            'bytes': sum(map(len, files.values())), 'measurement_workers_started': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination')
    args = parser.parse_args()
    try:
        result = restore(Path(__file__).resolve().parent, args.destination)
    except (ValueError, OSError, lzma.LZMAError, tarfile.TarError, KeyError) as exc:
        print(json.dumps({'status': 'REFUSED', 'error': str(exc)}, sort_keys=True))
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))
