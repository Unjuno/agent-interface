"""Verify and restore the frozen source only. Never execute an allocation."""
import base64, hashlib, json, lzma, sys
from pathlib import Path

def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out

def restore(destination):
    base = Path(__file__).resolve().parent
    m = json.loads((base / 'SOURCE.json').read_text(), object_pairs_hook=unique)
    parts = []
    for entry in m['parts']:
        name = entry['name']
        if Path(name).name != name:
            raise ValueError('part path')
        data = (base / name).read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('part integrity')
        parts.append(data.strip())
    packed = base64.b64decode(b''.join(parts), validate=True)
    if len(packed) != m['archive_bytes'] or hashlib.sha256(packed).hexdigest() != m['archive_sha256']:
        raise ValueError('archive integrity')
    dec = lzma.LZMADecompressor(memlimit=134217728)
    raw = dec.decompress(packed, max_length=200001)
    if not dec.eof or dec.unused_data or len(raw) > 200000:
        raise ValueError('expansion bound')
    members = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(members, dict) or len(members) != 12 or m['members'] != 12:
        raise ValueError('member count')
    for name, text in members.items():
        if not isinstance(name, str) or Path(name).name != name or name in ('.', '..') or not isinstance(text, str):
            raise ValueError('member shape')
    if hashlib.sha256(members['FREEZE.json'].encode()).hexdigest() != m['freeze_sha256']:
        raise ValueError('freeze integrity')
    freeze = json.loads(members['FREEZE.json'], object_pairs_hook=unique)
    if set(members) != set(freeze['files']) | {'FREEZE.json'}:
        raise ValueError('freeze member set')
    for name, digest in freeze['files'].items():
        if hashlib.sha256(members[name].encode()).hexdigest() != digest:
            raise ValueError('source integrity')
    destination = Path(destination)
    destination.mkdir(parents=False, exist_ok=False)
    for name, text in members.items():
        with (destination / name).open('xb') as stream:
            stream.write(text.encode())
    print(json.dumps({'restored': len(members), 'freeze_sha256': m['freeze_sha256'], 'allocation_executed': False}))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: unpack_source.py NEW_DIRECTORY')
    restore(sys.argv[1])
