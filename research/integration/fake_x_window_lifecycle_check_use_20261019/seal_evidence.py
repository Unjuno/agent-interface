"""Extract machine-readable receipts and seal this packet's exact bytes."""
import hashlib
import gzip
import json
from pathlib import Path

root = Path(__file__).resolve().parent
for mode in ('normal', 'optimized'):
    raw = root / f'receipt-{mode}.raw.bin'
    compressed = root / f'receipt-{mode}.raw.gz'
    if raw.exists():
        data = raw.read_bytes()
        compressed.write_bytes(gzip.compress(data, mtime=0))
        raw.unlink()
    else:
        data = gzip.decompress(compressed.read_bytes())
    text = data.decode('utf-8')
    start = text.rfind('\n{')
    if start < 0:
        raise SystemExit(f'missing JSON receipt in receipt-{mode}.raw.txt')
    receipt = json.loads(text[start + 1:])
    (root / f'receipt-{mode}.json').write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
for mode in ('normal', 'optimized'):
    raw = root / f'module-{mode}.raw.bin'
    compressed = root / f'module-{mode}.raw.gz'
    if raw.exists():
        compressed.write_bytes(gzip.compress(raw.read_bytes(), mtime=0))
        raw.unlink()
files = sorted(p for p in root.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}" for p in files]
(root / 'SHA256SUMS').write_text('\n'.join(lines) + '\n', encoding='ascii', newline='\n')
