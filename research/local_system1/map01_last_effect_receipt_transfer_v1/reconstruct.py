#!/usr/bin/env python3
import base64,gzip,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
expected={'SOURCE_BUNDLE.json':'95e8de729b63ce8b1537ea59a1a9aa77d6dacb09873340370aed3a3046ea6311','EVIDENCE.json':'7a02817d8775967729b96be2698053b920adaa8c4c4d070df23b8a25cc98408b'}
raw={}
for name,digest in expected.items():
    data=gzip.decompress(base64.b64decode((root/(name+'.gz.b64')).read_text()))
    if hashlib.sha256(data).hexdigest()!=digest: raise SystemExit('bundle hash mismatch: '+name)
    raw[name]=data
src=json.loads(raw['SOURCE_BUNDLE.json']); ev=json.loads(raw['EVIDENCE.json'])
out=Path(sys.argv[1] if len(sys.argv)>1 else root/'reconstructed'); out.mkdir(parents=True,exist_ok=True)
for n,text in src['files'].items():
    p=out/'source'/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256'][n]: raise SystemExit('source hash mismatch: '+n)
for n,text in ev['input'].items():
    p=out/'input'/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    b=p.read_bytes(); got=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    if got!=ev['input_git_blobs'][n]: raise SystemExit('input Git blob mismatch: '+n)
for n,text in ev['output'].items():
    p=out/'output'/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
print(out)
