#!/usr/bin/env python3
import base64,gzip,hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
expected={
 "SOURCE_BUNDLE.json":"757a028f0a2ef2dd54844c0bc523f0666ab6728646d3beb985a397b7b10694ea",
 "EVIDENCE.json":"1477571eedee87eff43de2ed2eee0842bbb5813f458ecad20b356620af52fdd2"}
for name in expected:
    raw=gzip.decompress(base64.b64decode((root/(name+".gz.b64")).read_text()))
    if hashlib.sha256(raw).hexdigest()!=expected[name]: raise SystemExit(f"bundle hash mismatch: {name}")
    (root/name).write_bytes(raw)
bundle=json.loads((root/'SOURCE_BUNDLE.json').read_text())
out=Path(sys.argv[1] if len(sys.argv)>1 else root/'reconstructed')
out.mkdir(parents=True,exist_ok=True)
for name,text in bundle['files'].items():
    p=out/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
    got=hashlib.sha256(p.read_bytes()).hexdigest()
    if got!=bundle['sha256'][name]: raise SystemExit(f"source hash mismatch: {name}")
print(out)
