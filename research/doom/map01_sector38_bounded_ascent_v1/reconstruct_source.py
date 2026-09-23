from pathlib import Path
import base64,hashlib
PARTS=['source.part00.b64', 'source.part01.b64', 'source.part02.b64', 'source.part03.b64', 'source.part04.b64', 'tail.part00.b64', 'tail.part01.b64', 'tail.part02.b64', 'tail.part03.b64']
raw=base64.b64decode(''.join(Path(p).read_text().strip() for p in PARTS))
expected='565f5767520d0aef222351f818c590f378d092a836839877494d4e6f54e9cef6'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'SHA mismatch {actual}')
Path('source.tar.xz').write_bytes(raw)
print(actual)
