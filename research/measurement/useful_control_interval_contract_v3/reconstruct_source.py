import base64,hashlib,json
from pathlib import Path
m=json.loads(Path('SOURCE_ARCHIVE.json').read_text()); b=base64.b64decode(''.join(Path(x['name']).read_text() for x in m['parts'])); assert hashlib.sha256(b).hexdigest()==m['archive_sha256']; Path('source.tar.xz').write_bytes(b); print('PASS',len(b),m['archive_sha256'])
