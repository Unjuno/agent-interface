"""Postformal packaging helper; checks retained bytes, never reruns the experiment."""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(len(sys.argv) == 2, 'usage: python -B unpack.py NEW_OUTPUT_DIRECTORY')
    manifest = json.loads((HERE / 'EVIDENCE.json').read_text())
    require(manifest['schema'] == 'reader3941-packed-evidence-v1', 'manifest schema')
    require([p['path'] for p in manifest['parts']] ==
            [f'evidence/packed.{i:02d}' for i in range(8)], 'part paths/order')
    chunks = []
    for part in manifest['parts']:
        data = (HERE / part['path']).read_bytes()
        require(len(data) == part['size'] <= 6000, 'part length')
        require(hashlib.sha256(data).hexdigest() == part['sha256'], 'part sha256')
        git_object = f'blob {len(data)}\0'.encode() + data
        require(hashlib.sha1(git_object).hexdigest() == part['blob'], 'part Git identity')
        chunks.append(data)
    packed = b''.join(chunks)
    require(len(packed) == manifest['xz_size'] == 46136, 'archive length')
    require(hashlib.sha256(packed).hexdigest() == manifest['xz_sha256'], 'archive sha256')
    decoder = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
    raw_tar = decoder.decompress(packed, max_length=4976641)
    require(decoder.eof and not decoder.unused_data, 'archive completeness')
    require(len(raw_tar) == manifest['tar_size'] == 4976640, 'tar length')
    with tarfile.open(fileobj=io.BytesIO(raw_tar), mode='r:') as archive:
        members = archive.getmembers()
        require(len(members) == manifest['files'] == 346, 'member count')
        names = set()
        for member in members:
            p = PurePosixPath(member.name)
            require(member.isfile() and not p.is_absolute() and
                    '..' not in p.parts and '\\' not in member.name, 'unsafe member')
            require(member.name not in names and 0 <= member.size <= 1000000, 'member bound')
            names.add(member.name)
        out = Path(sys.argv[1]).resolve()
        out.mkdir(parents=True, exist_ok=False)
        archive.extractall(out, members=members, filter='data')
    print(json.dumps({'files': len(members), 'xz_sha256': manifest['xz_sha256'],
                      'output': str(out), 'experiment_rerun': False}, sort_keys=True))


if __name__ == '__main__':
    main()
