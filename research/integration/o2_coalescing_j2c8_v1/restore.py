"""Bounded data-only restoration. Never executes archived files."""
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile


def restore(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError('destination exists')
    spec = json.loads((source / 'PACK.json').read_text())
    chunks = []
    for entry in spec['parts']:
        name = entry['name']
        if PurePosixPath(name).name != name:
            raise ValueError('part path')
        b = (source / name).read_bytes()
        if len(b) != entry['size'] or hashlib.sha256(b).hexdigest() != entry['sha256']:
            raise ValueError('part integrity')
        chunks.append(b)
    packed = b''.join(chunks)
    if len(packed) > 100000 or hashlib.sha256(packed).hexdigest() != spec['packed_sha256']:
        raise ValueError('archive integrity')
    decoder = lzma.LZMADecompressor()
    raw = decoder.decompress(packed, max_length=2000001)
    if len(raw)>2000000 or not decoder.eof or decoder.unused_data:
        raise ValueError('expansion limit or trailing data')
    if hashlib.sha256(raw).hexdigest() != spec['expanded_sha256']:
        raise ValueError('expanded integrity')
    data = json.loads(raw)
    if len(data) != spec['files'] or sum(len(v.encode()) for v in data.values()) != spec['member_bytes']:
        raise ValueError('inventory')
    for name, content in data.items():
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or str(p)!=name or '\\' in name or not isinstance(content,str):
            raise ValueError('member path or type')
    manifest = json.loads(data['RAW_MANIFEST.json'])
    if set(manifest) != set(data)-{'RAW_MANIFEST.json'}:
        raise ValueError('manifest inventory')
    for name, digest in manifest.items():
        if hashlib.sha256(data[name].encode()).hexdigest() != digest:
            raise ValueError('member integrity')
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='j2c8-restore-',dir=destination.parent))
    try:
        for name, content in data.items():
            p=staging/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content.encode())
        if destination.exists():
            raise ValueError('destination appeared')
        staging.rename(destination)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    return spec['files']


if __name__=='__main__':
    print(restore(Path(__file__).resolve().parent,Path(sys.argv[1])))
