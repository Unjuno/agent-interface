"""Restore retained bytes for offline audit only; never runs GUI or native binaries."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def restore(out):
    base = Path(__file__).resolve().parent
    m = json.loads((base/'EVIDENCE.json').read_text())
    chunks = []
    for part in m['parts']:
        data = (base/part['path']).read_bytes()
        if len(data) != part['bytes'] or sha(data) != part['sha256']:
            raise ValueError('archive part mismatch')
        chunks.append(data)
    data = b''.join(chunks)
    if len(data) != m['archive_bytes'] or sha(data) != m['archive_sha256']:
        raise ValueError('archive mismatch')
    decoder = lzma.LZMADecompressor()
    raw = decoder.decompress(data, max_length=2_000_000)
    if not decoder.eof or decoder.unused_data:
        raise ValueError('archive expansion bound/trailing bytes')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tar:
        members = tar.getmembers()
        names = set()
        total = 0
        for item in members:
            path = PurePosixPath(item.name)
            if not item.isfile() or path.is_absolute() or '..' in path.parts or str(path) != item.name or item.name in names:
                raise ValueError('invalid archive member')
            if item.size < 0 or item.size > 1_000_000:
                raise ValueError('member size bound')
            names.add(item.name)
            total += item.size
        if len(names) != m['files'] or total != m['uncompressed_file_bytes']:
            raise ValueError('member denominator mismatch')
        out.mkdir(parents=True, exist_ok=False)
        for item in members:
            dest = out/item.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write(tar.extractfile(item).read())
    freeze_bytes = (base/'FREEZE.json').read_bytes()
    if sha(freeze_bytes) != m['freeze_sha256']:
        raise ValueError('freeze mismatch')
    (out/'FREEZE.json').write_bytes(freeze_bytes)
    frozen = json.loads(freeze_bytes)
    for name, digest in frozen['sources'].items():
        dest = out/name
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write((base/name).read_bytes())
        if sha(dest.read_bytes()) != digest:
            raise ValueError('frozen source mismatch: '+name)
    for i, digest in m['formal_raw_sha256'].items():
        if sha((out/f'formal/batch-{i}/raw.json').read_bytes()) != digest:
            raise ValueError('formal raw mismatch')
    if sha((out/'AUDIT.json').read_bytes()) != m['audit_sha256']:
        raise ValueError('audit mismatch')
    print(json.dumps({'restored_files':len(names),'frozen_sources':len(frozen['sources']),
                      'archive_sha256':m['archive_sha256'],'runs_executed':0},sort_keys=True))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    restore(p.parse_args().out)
