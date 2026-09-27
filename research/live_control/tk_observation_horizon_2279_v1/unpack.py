"""Restore bounded evidence bytes only. Never runs a worker, display or model."""
import base64
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import sys

HERE = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out

def restore(destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('destination must not exist')
    manifest = json.loads((HERE/'EVIDENCE.json').read_text(), object_pairs_hook=unique)
    texts = []
    for part in manifest['parts']:
        path = PurePosixPath(part['path'])
        if len(path.parts) != 1 or not path.name.startswith('evidence.part'):
            raise ValueError('invalid part name')
        data = (HERE/path.name).read_bytes()
        if digest(data) != part['sha256']:
            raise ValueError('part digest mismatch')
        texts.append(data.decode('ascii').strip())
    compressed = base64.b64decode(''.join(texts), validate=True)
    if len(compressed) > 1_000_000 or len(compressed) != manifest['compressed_bytes']:
        raise ValueError('compressed size mismatch')
    if digest(compressed) != manifest['compressed_sha256']:
        raise ValueError('compressed digest mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw = decoder.decompress(compressed, max_length=2_000_001)
    if len(raw)>2_000_000 or not decoder.eof or decoder.unused_data:
        raise ValueError('expanded size or trailing data')
    if len(raw)!=manifest['expanded_bytes'] or digest(raw)!=manifest['expanded_sha256']:
        raise ValueError('expanded digest mismatch')
    files = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(files, dict) or len(files)>100 or set(files)!=set(manifest['members']):
        raise ValueError('member inventory mismatch')
    verified = {}
    for name, text in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or not path.parts or '..' in path.parts or '\\' in name:
            raise ValueError('invalid member path')
        if str(path)!=name or not isinstance(text,str):
            raise ValueError('noncanonical member')
        data=text.encode('utf-8'); expected=manifest['members'][name]
        if len(data)!=expected['bytes'] or digest(data)!=expected['sha256']:
            raise ValueError('member digest mismatch')
        verified[name]=data
    destination.mkdir(parents=True, exist_ok=False)
    for name,data in verified.items():
        path=destination/name
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as handle:
            handle.write(data)
    return {'restored_files':len(verified),'expanded_sha256':digest(raw)}

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit('usage: python -B unpack.py ABSENT_DESTINATION')
    print(json.dumps(restore(sys.argv[1]),sort_keys=True))
