"""Bounded, data-only restoration of the exact retained pilot. No experiment runs."""
import base64
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
PREFIX = 'research/integration/resume_json_ingress_c7e4_v3/'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def unpack(destination, package=ROOT):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination must be new')
    m = json.loads((package / 'CAPSULE.json').read_text(encoding='utf-8'))
    if (m['archive_bytes'], m['tar_bytes'], m['member_files'], m['member_bytes'], m['prefix']) != (96472, 2580480, 558, 2191841, PREFIX):
        raise ValueError('unexpected fixed envelope')
    if [p['path'] for p in m['parts']] != [f'capsule/part-{i:02}.b64' for i in range(16)]:
        raise ValueError('part inventory')
    texts = []
    for p in m['parts']:
        f = package / p['path']
        if f.is_symlink() or not f.is_file() or f.stat().st_size != p['bytes']:
            raise ValueError('part type/length')
        b = f.read_bytes()
        if digest(b) != p['sha256']:
            raise ValueError('part digest')
        texts.append(b)
    compressed = base64.b64decode(b''.join(texts), validate=True)
    if len(compressed) != m['archive_bytes'] or digest(compressed) != m['archive_sha256']:
        raise ValueError('archive identity')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(compressed, max_length=m['tar_bytes'] + 1)
    if len(raw) != m['tar_bytes'] or not decoder.eof or decoder.unused_data:
        raise ValueError('archive expansion')
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            name = member.name
            p = PurePosixPath(name)
            if (not member.isfile() or p.is_absolute() or '..' in p.parts
                    or not name.startswith(PREFIX) or name in files
                    or p.as_posix() != name or '\\' in name):
                raise ValueError('unsafe/duplicate member')
            if not 0 <= member.size <= 1_000_000:
                raise ValueError('member size')
            if len(files) >= m['member_files']:
                raise ValueError('member count')
            f = archive.extractfile(member)
            if f is None:
                raise ValueError('missing member')
            b = f.read(member.size + 1)
            if len(b) != member.size:
                raise ValueError('member length')
            files[name] = b
    if len(files) != m['member_files'] or sum(map(len, files.values())) != m['member_bytes']:
        raise ValueError('member totals')
    manifest = files[PREFIX + 'SHA256SUMS']
    if digest(manifest) != m['original_manifest_sha256']:
        raise ValueError('original manifest')
    expected = {}
    for line in manifest.decode('utf-8').splitlines():
        h, name = line.split('  ', 1)
        path = PREFIX + name
        if path in expected or path not in files or digest(files[path]) != h:
            raise ValueError('original member identity')
        expected[path] = h
    if set(expected) != set(files) - {PREFIX + 'SHA256SUMS'}:
        raise ValueError('original inventory')
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(data)
    return destination / PREFIX

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python -B unpack.py NEW_DIRECTORY')
    print(unpack(sys.argv[1]))
