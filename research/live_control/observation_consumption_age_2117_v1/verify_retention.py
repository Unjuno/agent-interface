"""Read-only integrity check; never executes retained native binary or a live run."""
import base64
import hashlib
import json
from pathlib import Path
import zlib

root = Path(__file__).resolve().parent
freeze = json.loads((root / 'FREEZE.json').read_text())
checks = {}
for name, expected in freeze['files'].items():
    path = root / name
    if name == 'native.so':
        data = zlib.decompress(base64.b64decode((root / 'native.so.zlib.b64').read_bytes()))
    elif name == 'construction.json.zlib.b64':
        data = b''.join((root / f'{name}.part{i:02d}').read_bytes() for i in range(1, 5))
    else:
        data = path.read_bytes()
    checks[name] = hashlib.sha256(data).hexdigest() == expected
raw = zlib.decompress(base64.b64decode((root / 'raw.jsonl.zlib.b64').read_bytes()))
audit = json.loads((root / 'AUDIT.json').read_text())
checks['raw_sha256'] = hashlib.sha256(raw).hexdigest() == audit['raw_sha256']
checks['raw_bytes'] = len(raw) == audit['raw_bytes']
checks['freeze_git_blob'] = hashlib.sha1(b'blob ' + str(len(f := (root / 'FREEZE.json').read_bytes())).encode() + b'\0' + f).hexdigest() == '8d7628e47b0fdd5e83b52ad1a88479cf2ed6e204'
print(json.dumps({'all_exact': all(checks.values()), 'checks': checks}, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 2)
