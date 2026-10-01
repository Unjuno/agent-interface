from pathlib import Path
import base64,gzip,hashlib,sys
s=''.join(Path(f'result.part{i:02d}.b64').read_text() for i in range(2))
raw=gzip.decompress(base64.b64decode(s))
expected='0a14134584579fffd253cb2c218cce11ed971ed726a5762035fc77b9f0162dc7'
assert hashlib.sha256(raw).hexdigest()==expected
out=Path(sys.argv[1] if len(sys.argv)>1 else 'FORMAL_RESULT.reconstructed.json'); out.write_bytes(raw)
print(expected)
