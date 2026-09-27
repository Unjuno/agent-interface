"""Bounded data-only restoration. Does not execute the retained experiment."""
import base64, hashlib, json, lzma, sys
from pathlib import Path, PurePosixPath

def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result

def restore(destination):
    base = Path(__file__).resolve().parent
    m = json.loads((base / 'EVIDENCE.json').read_text(), object_pairs_hook=unique)
    pieces = []
    for item in m['parts']:
        name = item['name']
        if Path(name).name != name:
            raise ValueError('part path')
        data = (base / name).read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('part integrity')
        pieces.append(data.strip())
    packed = base64.b64decode(b''.join(pieces), validate=True)
    if len(packed) != m['archive_bytes'] or hashlib.sha256(packed).hexdigest() != m['archive_sha256']:
        raise ValueError('archive integrity')
    decoder = lzma.LZMADecompressor(memlimit=134217728)
    raw = decoder.decompress(packed, max_length=2000001)
    if not decoder.eof or decoder.unused_data or len(raw) > 2000000 or len(raw) != m['expanded_bytes']:
        raise ValueError('expansion bound')
    files = json.loads(raw, object_pairs_hook=unique)
    if type(files) is not dict or len(files) != 215 or m['members'] != 215:
        raise ValueError('member count')
    for name, text in files.items():
        path = PurePosixPath(name)
        if not name or path.is_absolute() or '..' in path.parts or str(path) != name or '\\' in name or not isinstance(text, str):
            raise ValueError('member path/type')
    inventory = json.loads(files['RAW_MANIFEST.json'], object_pairs_hook=unique)
    if set(files) != set(inventory) | {'RAW_MANIFEST.json'}:
        raise ValueError('inventory set')
    for name, digest in inventory.items():
        if hashlib.sha256(files[name].encode()).hexdigest() != digest:
            raise ValueError('member integrity')
    if sum(len(t.encode()) for t in files.values()) != m['member_bytes']:
        raise ValueError('member bytes')
    destination = Path(destination)
    destination.mkdir(parents=False, exist_ok=False)
    for name, text in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(text.encode())
    print(json.dumps({'restored': len(files), 'archive_sha256': m['archive_sha256'], 'allocation_executed': False}))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: unpack_evidence.py NEW_DIRECTORY')
    restore(sys.argv[1])
