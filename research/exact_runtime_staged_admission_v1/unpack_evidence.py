#!/usr/bin/env python3
"""Reassemble and hash-check the four retained binary parts before extraction."""
import hashlib, io, tarfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent
EXPECTED = 'bee985d71bf7776ac33c5f9c52be918d58db461fadc1a96a1e987ef77b531cab'
raw = b''.join((ROOT / 'evidence_parts' / f'part-{i:03d}').read_bytes() for i in range(4))
if hashlib.sha256(raw).hexdigest() != EXPECTED:
    raise ValueError('retained evidence archive hash mismatch')
for name in ('run-01', 'boundary-01'):
    if (ROOT / 'results' / name).exists():
        raise FileExistsError('will not overwrite retained or reproduced results: ' + name)
with tarfile.open(fileobj=io.BytesIO(raw), mode='r:xz') as archive:
    archive.extractall(ROOT, filter='data')
print('Archive verified and extracted; run python audit.py results/run-01')
