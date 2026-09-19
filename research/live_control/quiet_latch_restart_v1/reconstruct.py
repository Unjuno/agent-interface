"""Restore verified evidence bytes only. Never starts a benchmark or input."""
from pathlib import Path, PurePosixPath
import base64, hashlib, json, lzma, sys

HERE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def put(root, name, data):
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('unsafe archive path')
    p = root.joinpath(*rel.parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(data)

def main(output):
    output.mkdir(parents=True, exist_ok=False)
    manifests = json.loads((HERE / 'manifest.json').read_text())
    counts = {}
    for name, spec in manifests.items():
        chunks = []
        for part in spec['parts']:
            data = (HERE / part['file']).read_bytes()
            actual = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
            if len(data) != part['bytes'] or digest(data) != part['sha256'] or actual != part['git_blob']:
                raise ValueError('part integrity mismatch: ' + part['file'])
            chunks.append(data)
        compressed = b''.join(chunks)
        if len(compressed) != spec['bytes'] or digest(compressed) != spec['sha256']:
            raise ValueError('archive integrity mismatch')
        obj = json.loads(lzma.decompress(compressed, memlimit=128*1024*1024))
        if name == 'evidence.json.xz':
            for path, h in obj['files'].items():
                encoding, content = obj['blobs'][h]
                if encoding == 'utf8':
                    data = content.encode('utf-8')
                elif encoding == 'base64':
                    data = base64.b64decode(content, validate=True)
                else:
                    raise ValueError('unknown encoding')
                if digest(data) != h:
                    raise ValueError('original file hash mismatch: ' + path)
                put(output, path, data)
            counts[name] = len(obj['files'])
        elif name == 'prior_audits.json.xz':
            for path, text in obj.items():
                put(output / 'prior_audits', path, text.encode('utf-8'))
            counts[name] = len(obj)
        else:
            raise ValueError('unknown archive')
    print(json.dumps({'restored': counts, 'benchmark_executed': False}))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python reconstruct.py NEW_OUTPUT_DIRECTORY')
    main(Path(sys.argv[1]))
