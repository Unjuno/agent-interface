from pathlib import Path
import base64,hashlib
parts=''.join(''.join(Path(p).read_text().split()) for p in sorted(str(x) for x in Path('.').glob('source.part*.b64')))
b=base64.b64decode(parts)
assert hashlib.sha256(b).hexdigest()=='b3e9ff5d8343ed9915581fbbff9433a058d6457665a41caaf7441155e4b9e98e'
Path('source.tar.xz').write_bytes(b)
print(len(b),hashlib.sha256(b).hexdigest())
