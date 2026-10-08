"""Verify and extract retained research bytes; never execute the experiment."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile


def unpack(destination: Path) -> dict:
    root = Path(__file__).resolve().parent
    spec = json.loads((root/'CAPSULE.json').read_bytes())
    if destination.exists():
        raise ValueError('destination already exists; refusing overwrite')
    blocks = []
    for part in spec['parts']:
        name = part['path']
        if Path(name).name != name:
            raise ValueError('invalid part name')
        content = (root/name).read_bytes()
        if len(content) != part['bytes'] or hashlib.sha256(content).hexdigest() != part['sha256']:
            raise ValueError('part integrity: '+name)
        blocks.append(base64.b64decode(content.strip(), validate=True))
    packed = b''.join(blocks)
    if len(packed) != spec['archive_bytes'] or hashlib.sha256(packed).hexdigest() != spec['archive_sha256']:
        raise ValueError('archive integrity')
    decoder = lzma.LZMADecompressor(memlimit=256*1024*1024)
    data = decoder.decompress(packed, max_length=32*1024*1024+1)
    if not decoder.eof or decoder.unused_data or len(data) != spec['tar_bytes'] or len(data)>32*1024*1024:
        raise ValueError('compressed envelope')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        for entry in archive:
            name = PurePosixPath(entry.name)
            if not entry.isfile() or name.is_absolute() or '..' in name.parts or entry.name in files:
                raise ValueError('invalid/duplicate member')
            files[entry.name] = archive.extractfile(entry).read()
    if len(files) != spec['files'] or sum(map(len, files.values())) != spec['expanded_bytes']:
        raise ValueError('member accounting')
    manifest = json.loads(files['MANIFEST.json'])['files']
    if set(manifest) != set(files)-{'MANIFEST.json'}:
        raise ValueError('manifest membership')
    for name, info in manifest.items():
        content = files[name]
        if len(content) != info['bytes'] or hashlib.sha256(content).hexdigest() != info['sha256']:
            raise ValueError('member digest: '+name)
    destination.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        output = destination/name
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(content)
    return {'status':'PASS_EXTRACTION', 'files':len(files), 'archive_sha256':spec['archive_sha256'],
            'formal_executions':0}


if __name__ == '__main__':
    print(json.dumps(unpack(Path(sys.argv[1]).resolve()), sort_keys=True))
