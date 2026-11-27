import errno, hashlib, json, os
from pathlib import Path
p = Path('/probe/sentinel.bin')
actual = p.read_bytes()
assert actual == b'wslc-readonly-probe', {'bytes': actual.hex()}
try:
    p.write_bytes(b'must-not-write')
except OSError as exc:
    assert exc.errno == errno.EROFS, {'errno': exc.errno, 'message': str(exc)}
    write_rejected = True
else:
    write_rejected = False
assert write_rejected, 'read-only mount accepted a write'
print(json.dumps({'probe':'PASS','python':os.sys.version.split()[0],'bytes_sha256':hashlib.sha256(actual).hexdigest(),'write_rejected_errno':'EROFS','network':'disabled by WSLc argument'},sort_keys=True))
