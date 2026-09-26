"""Verify and unpack retained bytes only; never execute a GUI allocation."""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import lzma


def main():
    here = Path(__file__).resolve().parent
    envelope = json.loads((here / 'evidence.json').read_text())
    pieces = []
    for part in envelope['parts']:
        name = part['path']
        if Path(name).name != name:
            raise ValueError('invalid evidence part path')
        raw = (here / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != part['sha256']:
            raise ValueError('evidence part hash mismatch: ' + name)
        pieces.append(raw.strip())
    data = base64.b64decode(b''.join(pieces), validate=True)
    if hashlib.sha256(data).hexdigest() != envelope['compressed_sha256']:
        raise ValueError('compressed evidence hash mismatch')
    decoded = lzma.decompress(data)
    if len(decoded) != envelope['decoded_bytes'] or hashlib.sha256(decoded).hexdigest() != envelope['decoded_sha256']:
        raise ValueError('decoded evidence hash mismatch')
    files = json.loads(decoded)
    if len(files) != envelope['file_count']:
        raise ValueError('file denominator mismatch')
    destination = Path(sys.argv[1]) if len(sys.argv) == 2 else here / 'retained'
    if destination.exists():
        raise FileExistsError('refusing to replace retained output')
    verified = {}
    for name, item in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name:
            raise ValueError('unsafe archive member')
        raw = item['text'].encode('utf-8')
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('member hash mismatch: ' + name)
        verified[name] = raw
    destination.mkdir(parents=True)
    for name, raw in verified.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as f:
            f.write(raw)
    print(json.dumps({'result': 'PASS_LOSSLESS_UNPACK', 'files': len(files),
                      'decoded_sha256': envelope['decoded_sha256']}, sort_keys=True))


if __name__ == '__main__':
    main()
