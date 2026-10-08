from pathlib import Path
import base64,hashlib
PARTS=['source.part00.b64','source.part01.b64','source.part02.b64','source.part03a.b64','source.part03b00.b64','source.part03b01.b64','source.part03b02.b64','source.part03b03c00.b64','source.part03b03c01.b64','source.part03b03d00.b64','source.part03b03d01.b64','source.part03b03d02.b64','source.part03b03d03.b64']
raw=base64.b64decode(''.join(Path(p).read_text() for p in PARTS))
expected='e284eddb744b8f9156c5a34629578a352fb06719bf3deaddca9076d77e8ecca2'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected: raise SystemExit(f'SHA mismatch {actual}')
Path('source.tar.xz').write_bytes(raw)
print(actual)
