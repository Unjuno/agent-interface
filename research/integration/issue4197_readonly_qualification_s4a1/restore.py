"""Restore pinned review evidence as data; never execute an archived program.

Trusted/quiescent publication directory and temporary parent are assumed.
This is a checksum/format verifier, not a hostile-filesystem sandbox.
"""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

HERE = Path(__file__).resolve().parent
ARCHIVE_SHA = '01cfb94763722b2927bc7736bbfc52541a2e48c39f802a2092b5928214e73f83'
MANIFEST_SHA = 'b708851bb524082ce346fcc620b1619d08473272b3c652e5a9b37cf71c8f6d96'
MAX_TAR = 2_000_000

def digest(data):
    return hashlib.sha256(data).hexdigest()

def require(value, detail):
    if not value:
        raise ValueError(detail)

def checked_name(name):
    path = PurePosixPath(name)
    require(bool(name) and not path.is_absolute(), 'invalid archive name')
    require('..' not in path.parts and '.' not in path.parts, 'relative archive component')
    require(path.as_posix() == name and '\\' not in name, 'noncanonical archive name')
    return path

def read_members(blob):
    require(len(blob) == 32108 and digest(blob) == ARCHIVE_SHA, 'archive identity')
    decoder = lzma.LZMADecompressor()
    data = decoder.decompress(blob, max_length=MAX_TAR + 1)
    require(len(data) <= MAX_TAR and decoder.eof and not decoder.unused_data, 'archive expansion')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as tf:
        members = tf.getmembers()
        require(len(members) == 91, 'archive denominator')
        records = {}
        for member in members:
            checked_name(member.name)
            require(member.isfile() and member.size <= 65536, 'member type/size')
            require(member.name not in records, 'duplicate member')
            value = tf.extractfile(member).read()
            require(len(value) == member.size, 'member length')
            records[member.name] = value
    manifest_data = records.pop('MANIFEST.json')
    require(digest(manifest_data) == MANIFEST_SHA, 'manifest identity')
    manifest = json.loads(manifest_data)
    require(len(manifest) == 90 and set(manifest) == set(records), 'manifest coverage')
    for name, value in records.items():
        require(type(manifest[name]['bytes']) is int, 'manifest length type')
        require(len(value) == manifest[name]['bytes'] and digest(value) == manifest[name]['sha256'], 'member identity: '+name)
    records['MANIFEST.json'] = manifest_data
    return records

def restore(destination, publication=HERE):
    destination = Path(destination)
    require(not destination.exists() and not destination.is_symlink(), 'destination exists')
    package = json.loads((Path(publication)/'PACKAGE.json').read_bytes())
    expected_names = [f'evidence.{number:02d}.bin' for number in range(1,10)]
    require([part['name'] for part in package['parts']] == expected_names, 'part order')
    pieces = []
    for part in package['parts']:
        data = (Path(publication)/part['name']).read_bytes()
        require(len(data) == part['bytes'] and digest(data) == part['sha256'], 'part identity')
        pieces.append(data)
    records = read_members(b''.join(pieces))
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in records.items():
        target = destination / checked_name(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
    return {'status':'PASS_DATA_ONLY_RESTORE','files':len(records),
            'manifest_entries':90,'archive_sha256':ARCHIVE_SHA,'executed_archived_code':False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',required=True,type=Path)
    args = parser.parse_args()
    print(json.dumps(restore(args.out),indent=2,sort_keys=True))
