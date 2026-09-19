from pathlib import Path
import base64,hashlib,json,tarfile,io
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
s=json.loads((ROOT/'SUCCESSOR_MAP.json').read_text())
b64=b''.join((ROOT/x['name']).read_bytes() for x in m['chunks'])
raw=base64.b64decode(b64,validate=True)
assert hashlib.sha256(raw).hexdigest()==m['archive_sha256']
tmp=ROOT/'_parent_source';tmp.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf: tf.extractall(tmp)
for name,sha in s['parent_source'].items():
    assert hashlib.sha256((tmp/name).read_bytes()).hexdigest()==sha
out=ROOT/'reconstructed_successor';out.mkdir(exist_ok=True)
for name in ('runner.py','audit.py','fixture.py'):
    data=(tmp/name).read_text()
    for p in s['patches']:
        if p['file']==name:
            assert p['old'] in data, (name,p['old'])
            data=data.replace(p['old'],p['new'])
    (out/name).write_text(data)
    b=(out/name).read_bytes()
    exp=s['result_source'][name]
    assert len(b)==exp['bytes'], (name,len(b),exp['bytes'])
    assert hashlib.sha256(b).hexdigest()==exp['sha256'], name
print(json.dumps({'ok':True,'result_source':s['result_source']},sort_keys=True))
