from pathlib import Path
import base64,hashlib,json,tarfile,io
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
b64=b''.join((ROOT/x['name']).read_bytes() for x in m['chunks'])
assert len(b64)==m['base64_chars']
assert hashlib.sha256(b64).hexdigest()==m['base64_sha256']
raw=base64.b64decode(b64,validate=True)
assert len(raw)==m['archive_bytes']
assert hashlib.sha256(raw).hexdigest()==m['archive_sha256']
out=ROOT/'reconstructed_source';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf: tf.extractall(out)
for n,v in m['files'].items():
    b=(out/n).read_bytes()
    assert len(b)==v['bytes']
    assert hashlib.sha256(b).hexdigest()==v['sha256']
print(json.dumps({'ok':True,'files':m['files']},sort_keys=True))
