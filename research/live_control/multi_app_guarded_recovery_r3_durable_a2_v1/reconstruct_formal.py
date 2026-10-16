#!/usr/bin/env python3
import base64,gzip,hashlib,io,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
b64=(HERE/'FORMAL_EVIDENCE.tar.gz.b64').read_bytes()
if hashlib.sha256(b64).hexdigest()!='ec83ec3887dc2cb8010042f520b7b31dfaeea01d69215bd647634f8e67fe3f0b': raise SystemExit('b64 hash mismatch')
gz=base64.b64decode(b64)
if hashlib.sha256(gz).hexdigest()!='22831c77130b786cb7ae55c6a298aaaa9c1c4bfcd645dffdaebacffcc8e09eff': raise SystemExit('gzip hash mismatch')
raw=gzip.decompress(gz)
out=HERE/'FORMAL_RECONSTRUCTED';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:t.extractall(out,filter='data')
expected={'BATCH_1.json':'4baf43a67512f933f4039c3b00f7d1100ba324b1bd3d6fc3a4819cd145831211','BATCH_2.json':'92df5a69e0617eba603dad8dbb928f5f7d6c979febfcacdb86ce9abeb55344b9','BATCH_3.json':'4435cec038021e9e7fddd0340a216b8930de12f614a0e35cb90dac9b58c1dd00','BATCH_4.json':'54fb26f446dfeb17239116e410ebf72f10d2ed23e020281155bf5a47f5edb83f','RESULT.json':'652f48b004cc395b1cc388d1abb8bbb13a233cdb3f5b415d8fd09006c180169d','AUDIT.json':'138f7ce2b9539686c79d8c73fc9a07d159d6810691d93a988a5f79da42a7760d'}
for n,h in expected.items():
    got=hashlib.sha256((out/n).read_bytes()).hexdigest()
    if got!=h: raise SystemExit(f'{n} hash mismatch {got}')
print('PASS')
