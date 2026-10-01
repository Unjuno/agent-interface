"""Bounded data loading only; never execute recovered code."""
import base64
import hashlib
import json
from pathlib import Path
import zlib

LIMIT = 4_000_000


def load_packed(path, metadata):
    path = Path(path)
    text = (''.join(p.read_text().strip() for p in sorted(path.glob('*.txt')))
            if path.is_dir() else path.read_text().strip())
    packed = base64.b64decode(text, validate=True)
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, LIMIT + 1)
    if len(raw) > LIMIT or decoder.unconsumed_tail or not decoder.eof or decoder.unused_data:
        raise ValueError('invalid or oversized compressed data')
    if len(raw) != metadata['bytes'] or hashlib.sha256(raw).hexdigest() != metadata['sha256']:
        raise ValueError('data identity mismatch')
    return json.loads(raw)


def inputs(root):
    return load_packed(root / 'input_parts', json.loads((root / 'INPUTS.json').read_text()))
