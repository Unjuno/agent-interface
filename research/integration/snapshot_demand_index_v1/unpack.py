"""Verify/extract the immutable Issue 4068 evidence; never execute an experiment."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

EXPECTED_SHA = '5ccd8540226a46f3ea29616c8b1171019dd0e8badd5d7a8d7d5d3027544d88d8'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(source):
    spec = json.loads((source / 'ARCHIVE.json').read_bytes())
    require(spec['archive_sha256'] == EXPECTED_SHA, 'ARCHIVE_IDENTITY')
    require(type(spec['files']) is int and spec['files'] == 103, 'FILE_COUNT')
    require(type(spec['member_bytes']) is int and spec['member_bytes'] == 4933391,
            'MEMBER_BYTES')
    require(spec['archive_bytes'] == 36104 and len(spec['parts']) == 5,
            'ARCHIVE_BOUNDS')
    pieces = []
    for i, item in enumerate(spec['parts']):
        require(item['path'] == f'evidence.{i:02d}.bin', 'PART_ORDER')
        data = (source / item['path']).read_bytes()
        require(len(data) == item['bytes'] == (8000 if i < 4 else 4104), 'PART_SIZE')
        require(digest(data) == item['sha256'], 'PART_DIGEST')
        git_id = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
        require(git_id == item['git_blob'], 'PART_GIT_ID')
        pieces.append(data)
    packed = b''.join(pieces)
    require(len(packed) == 36104 and digest(packed) == EXPECTED_SHA, 'ARCHIVE_DIGEST')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(packed, max_length=8000001)
    require(len(raw) <= 8000000 and decoder.eof and not decoder.unused_data,
            'EXPANSION_BOUND')
    contents = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            require(item.isfile() and not path.is_absolute()
                    and '..' not in path.parts and str(path) == item.name
                    and item.name not in contents, 'MEMBER_PATH_OR_KIND')
            require(0 <= item.size <= 4933391, 'MEMBER_SIZE')
            contents[item.name] = archive.extractfile(item).read()
            require(len(contents) <= 103, 'MEMBER_COUNT')
    require(len(contents) == 103 and sum(map(len, contents.values())) == 4933391,
            'INVENTORY')
    require(spec['manifest'] == 'FILES.json', 'MANIFEST_NAME')
    manifest = json.loads(contents['FILES.json'])
    require(len(manifest) == 102, 'MANIFEST_COUNT')
    names = [item['path'] for item in manifest]
    require(len(set(names)) == 102 and set(names) == set(contents) - {'FILES.json'},
            'MANIFEST_COVERAGE')
    for item in manifest:
        data = contents[item['path']]
        require(type(item['bytes']) is int and len(data) == item['bytes']
                and digest(data) == item['sha256'], 'MEMBER_DIGEST:' + item['path'])
    return contents


def restore(source, destination):
    require(not destination.exists() and not destination.is_symlink(), 'DESTINATION_EXISTS')
    contents = verify(source)
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    return {'files': len(contents), 'member_bytes': sum(map(len, contents.values())),
            'archive_sha256': EXPECTED_SHA, 'experiment_executed': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python -B unpack.py <new-output-directory>')
    try:
        print(json.dumps(restore(Path(__file__).resolve().parent, Path(sys.argv[1])), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, lzma.LZMAError, tarfile.TarError) as error:
        print(json.dumps({'status': 'REFUSED', 'error': str(error)}), file=sys.stderr)
        raise SystemExit(2)
