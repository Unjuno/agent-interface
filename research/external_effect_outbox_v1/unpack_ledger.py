"""Losslessly unpack the small GitHub measurement ledger and verify its identity."""
import gzip,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
raw=gzip.decompress((root/'OBSERVED_LEDGER.json.gz').read_bytes())
expected='251ef606b38eeb7cec9ec95514c1f8f4ec3d2ae6445f7c18b4a776655eb9d60d'
if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('ledger checksum mismatch')
p=root/'OBSERVED_LEDGER.json'
if p.exists() and p.read_bytes()!=raw: raise FileExistsError('refusing to replace different ledger')
if not p.exists(): p.write_bytes(raw)
print('verified observed ledger:',len(raw),'bytes')
