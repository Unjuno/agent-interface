"""Validate and restore retained research data; never runs an experiment."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile


def restore(source: Path, destination: Path) -> dict:
    source = source.resolve()
    if destination.exists():
        raise ValueError('DESTINATION_EXISTS')
    meta = json.loads((source / 'PACKAGE.json').read_text())
    if type(meta['archive_bytes']) is not int or not 0 < meta['archive_bytes'] <= 2_000_000:
        raise ValueError('ARCHIVE_BOUND')
    chunks = []
    for part in meta['parts']:
        rel = PurePosixPath(part['file'])
        if rel.is_absolute() or '..' in rel.parts or rel.parts[0] != 'parts':
            raise ValueError('PART_PATH')
        data = (source / str(rel)).read_bytes()
        if len(data) != part['bytes'] or hashlib.sha256(data).hexdigest() != part['sha256']:
            raise ValueError('PART_INTEGRITY')
        chunks.append(data)
    packed = b''.join(chunks)
    if len(packed) != meta['archive_bytes'] or hashlib.sha256(packed).hexdigest() != meta['archive_sha256']:
        raise ValueError('ARCHIVE_INTEGRITY')
    decoder = lzma.LZMADecompressor()
    decoded = decoder.decompress(packed, max_length=20_000_001)
    if len(decoded) > 20_000_000 or not decoder.eof or decoder.unused_data or len(decoded) != meta['tar_bytes']:
        raise ValueError('DECOMPRESSION_BOUND')
    with tarfile.open(fileobj=io.BytesIO(decoded), mode='r:') as archive:
        members = archive.getmembers()
        names = set()
        for member in members:
            rel = PurePosixPath(member.name)
            if (not member.isfile() or rel.is_absolute() or '..' in rel.parts
                    or '\\' in member.name or member.name in names or not rel.parts):
                raise ValueError('MEMBER_PATH_OR_TYPE')
            names.add(member.name)
        if len(members) != meta['file_count'] or sum(m.size for m in members) != meta['member_bytes']:
            raise ValueError('MEMBER_DENOMINATOR')
        destination.mkdir(parents=True, exist_ok=False)
        for member in members:
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.extractfile(member).read()
            if len(data) != member.size:
                raise ValueError('MEMBER_BYTES')
            with target.open('xb') as stream:
                stream.write(data)
    return {'restored_files': len(members), 'member_bytes': meta['member_bytes'], 'experiment_executed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).parent, args.destination), sort_keys=True))
