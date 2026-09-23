#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,sys
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=Path(__file__).resolve().parent
    spec=json.loads((root/'fixture_bundle/FIXTURE_BUNDLE.json').read_text())
    for item in spec['files']:
        data=''.join((root/'fixture_bundle/parts'/name).read_text().strip() for name in item['parts'])
        raw=base64.b64decode(data,validate=True)
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise RuntimeError('bundle mismatch '+item['path'])
        out=root/item['path'];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
        if sha(out)!=item['sha256']: raise RuntimeError('write mismatch '+item['path'])
    print('PASS materialized',len(spec['files']),'fixture binary files')
if __name__=='__main__': main()
