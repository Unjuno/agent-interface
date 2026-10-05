#!/usr/bin/env python3
"""Verify all package files against SHA256SUMS (except the manifest itself)."""
import hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
rows=(HERE/'SHA256SUMS').read_text(encoding='utf-8').splitlines()
seen=set()
for row in rows:
    digest,name=row.split('  ',1)
    assert name not in seen,name
    seen.add(name)
    path=HERE/name
    assert path.is_file(),name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
actual={p.relative_to(HERE).as_posix() for p in HERE.rglob('*') if p.is_file() and p.name!='SHA256SUMS'}
assert seen==actual,(sorted(seen-actual),sorted(actual-seen))
print(f'PACKAGE_MANIFEST_PASS {len(seen)}')
