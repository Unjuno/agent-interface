#!/usr/bin/env python3
import base64,hashlib,json,pathlib,sys,zlib
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: restore_formal.py FRESH_DIR')
    out=pathlib.Path(sys.argv[1]); out.mkdir(exist_ok=False)
    pkg=json.loads((ROOT/'PACKAGE.json').read_text()); meta=json.loads((ROOT/'EVIDENCE_MANIFEST.json').read_text())
    pieces=[]
    for spec in pkg['parts']:
        b=(ROOT/spec['name']).read_bytes()
        if len(b)!=spec['bytes'] or hashlib.sha256(b).hexdigest()!=spec['sha256']: raise SystemExit('part mismatch:'+spec['name'])
        pieces.append(b)
    combined=b''.join(pieces)
    if len(combined)!=pkg['combined_bytes'] or hashlib.sha256(combined).hexdigest()!=pkg['combined_sha256']: raise SystemExit('combined mismatch')
    raw=zlib.decompress(base64.b64decode(combined.strip(),validate=True))
    if hashlib.sha256(raw).hexdigest()!=meta['payload_sha256']: raise SystemExit('payload hash mismatch')
    obj=json.loads(raw)
    for name,s in obj['files'].items():
        b=base64.b64decode(s,validate=True); spec=meta['files'][name]
        if hashlib.sha256(b).hexdigest()!=spec['sha256'] or len(b)!=spec['bytes']: raise SystemExit('member mismatch:'+name)
        (out/name).write_bytes(b)
    if set(p.name for p in out.iterdir())!=set(meta['files']): raise SystemExit('member set mismatch')
if __name__=='__main__': main()
