#!/usr/bin/env python3
"""Restore the exact retained formal data; no experiment or native execution."""
import base64, hashlib, lzma
from pathlib import Path

PARTS = {
    'raw.part1.b64': '7d0708e94112702001910bbfa27d566fa1677f0c',
    'raw.part2.b64': 'a9134d4d8596fd0c4f2c73b3cfaba2bc3e4f8273',
    'raw.part3.b64': '57f851253e29ffe27fcbeae6ae441b3a7d812843',
}
RAW_SHA = 'fb99faceca9715587bba3ec2b11cd2b5dcf8cde3b92c7559a6fd05da1e9b9e6f'
XZ_SHA = 'dca88f86fb0b670768b5cc46464934e6ab01765d4370837a2ba07a89c5f38afe'

def restore(root):
    chunks = []
    for name, expected in PARTS.items():
        data = (root / name).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != expected:
            raise ValueError('retained part identity mismatch: ' + name)
        chunks.append(data.strip())
    packed = base64.b64decode(b''.join(chunks), validate=True)
    if len(packed) != 20448 or hashlib.sha256(packed).hexdigest() != XZ_SHA:
        raise ValueError('XZ identity mismatch')
    raw = lzma.decompress(packed)
    if len(raw) != 202432 or hashlib.sha256(raw).hexdigest() != RAW_SHA:
        raise ValueError('raw identity mismatch')
    (root / 'formal').mkdir(exist_ok=True)
    for name, data in [('raw.json', raw), ('raw.json.xz', packed)]:
        path = root / 'formal' / name
        if path.exists():
            if path.read_bytes() != data:
                raise ValueError('refuse to overwrite different data: ' + str(path))
        else:
            with path.open('xb') as f:
                f.write(data)
    print('Restored 202432 exact raw bytes; no acquisition executed.')
    return raw

if __name__ == '__main__':
    restore(Path(__file__).resolve().parent)
