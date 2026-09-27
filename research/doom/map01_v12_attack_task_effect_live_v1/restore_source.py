from pathlib import Path
import hashlib,tarfile,json
here=Path(__file__).resolve().parent
raw=(here/'SOURCE.tar.xz').read_bytes()
expected='b6ae5a7854e8b07d3c0fa0f42830fd4754b5f85d6c752e38e893ffb7d8e084fd'
assert hashlib.sha256(raw).hexdigest()==expected
out=here/'restored-source';out.mkdir(exist_ok=False)
with tarfile.open(here/'SOURCE.tar.xz',mode='r:xz') as tf:tf.extractall(out,filter='data')
print(json.dumps({'sha256':expected,'members':sorted(p.name for p in out.iterdir())}))
