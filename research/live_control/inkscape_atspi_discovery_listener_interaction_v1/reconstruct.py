#!/usr/bin/env python3
import base64,hashlib,tarfile
from pathlib import Path
r=Path(__file__).resolve().parent
text=''.join(''.join(p.read_text().split()) for p in sorted(r.glob('evidence.part*.b64')))
b=base64.b64decode(text,validate=True)
assert len(b)==28773
assert hashlib.sha256(b).hexdigest()=="c3d5272349e317ae70278545990f8b23f698d6555d595d5bbefe5225a620b68f"
p=r/'evidence.tar.gz';p.write_bytes(b)
o=r/'reconstructed';o.mkdir(exist_ok=True)
with tarfile.open(p,'r:gz') as tf: tf.extractall(o,filter='data')
print({"ok":True,"parts":len(list(r.glob('evidence.part*.b64'))),"bytes":len(b),"sha256":"c3d5272349e317ae70278545990f8b23f698d6555d595d5bbefe5225a620b68f"})
