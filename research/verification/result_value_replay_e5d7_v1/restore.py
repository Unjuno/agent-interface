"""Restore checksum-bound regular evidence files into a NEW trusted directory.

Data only: never invokes a scientific receiver or reruns the experiment.
The publication and destination parent must be trusted and quiescent.
"""
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

MAX_ARCHIVE = 1 << 20
MAX_TAR = 16 << 20
MAX_MEMBERS = 2000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(publication, destination):
    publication, destination = Path(publication), Path(destination)
    meta = json.loads((publication / 'EVIDENCE.json').read_text())
    if destination.exists():
        raise ValueError('destination must be new')
    pieces = []
    seen_parts = set()
    for item in meta['parts']:
        name = item['file']
        if Path(name).name != name or name in seen_parts:
            raise ValueError('invalid part name')
        seen_parts.add(name)
        data = (publication / name).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if len(data) != item['bytes'] or sha(data) != item['sha256'] or blob != item['git_blob']:
            raise ValueError('part identity mismatch:' + name)
        pieces.append(data)
    packed = b''.join(pieces)
    if len(packed) > MAX_ARCHIVE or len(packed) != meta['archive_bytes'] or sha(packed) != meta['archive_sha256']:
        raise ValueError('archive identity mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128 << 20)
    plain = decoder.decompress(packed, max_length=MAX_TAR + 1)
    if len(plain) > MAX_TAR or not decoder.eof or decoder.unused_data:
        raise ValueError('archive exceeds bounded single-stream format')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(plain), mode='r:') as tar:
        for member in tar:
            name = member.name
            path = PurePosixPath(name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or str(path) != name or '\\' in name or name in files
                    or len(files) >= MAX_MEMBERS or member.size > MAX_TAR):
                raise ValueError('noncanonical regular member')
            stream = tar.extractfile(member)
            data = stream.read()
            if len(data) != member.size:
                raise ValueError('member length mismatch')
            files[name] = data
    if len(files) != meta['members'] or sum(map(len, files.values())) != meta['member_bytes']:
        raise ValueError('member denominator mismatch')
    manifest = json.loads(files['RAW_MANIFEST.json'])
    if set(manifest) != set(files) - {'RAW_MANIFEST.json'}:
        raise ValueError('raw manifest membership mismatch')
    for name, item in manifest.items():
        if len(files[name]) != item['bytes'] or sha(files[name]) != item['sha256']:
            raise ValueError('raw member mismatch:' + name)
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    return {'members': len(files), 'verified_manifest_entries': len(manifest),
            'member_bytes': sum(map(len, files.values())), 'archive_sha256': sha(packed)}


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('destination', type=Path)
    a = ap.parse_args()
    print(json.dumps(unpack(Path(__file__).resolve().parent, a.destination), indent=2, sort_keys=True))
