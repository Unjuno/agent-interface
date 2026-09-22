#!/usr/bin/env python3
import argparse, base64, hashlib, io, json, tarfile
from pathlib import Path, PurePosixPath
HERE=Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out'); a=ap.parse_args(); out=Path(a.out).resolve()
    if out.exists(): raise SystemExit('destination exists')
    pack=json.loads((HERE/'PACK.json').read_text())
    raw_parts=[]
    for part in pack['parts']:
        txt=(HERE/'parts'/part['name']).read_bytes()
        if len(txt)!=part['text_size'] or sha(txt)!=part['text_sha256']: raise SystemExit('part text mismatch '+part['name'])
        raw=base64.b64decode(txt.strip(),validate=True)
        if len(raw)!=part['decoded_size'] or sha(raw)!=part['decoded_sha256']: raise SystemExit('part decoded mismatch '+part['name'])
        raw_parts.append(raw)
    arc=b''.join(raw_parts)
    if len(arc)!=pack['archive_size'] or sha(arc)!=pack['archive_sha256']: raise SystemExit('archive mismatch')
    out.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(arc),mode='r:xz') as tf:
        members=tf.getmembers()
        for m in members:
            pp=PurePosixPath(m.name)
            if pp.is_absolute() or '..' in pp.parts or not m.isfile(): raise SystemExit('unsafe member '+m.name)
        tf.extractall(out,filter='data')
    idx=json.loads((out/'EVIDENCE_INDEX.json').read_text())
    if idx['count']!=pack['expanded_count'] or idx['total_bytes']!=pack['expanded_bytes']: raise SystemExit('index denominator mismatch')
    for rel,meta in idx['files'].items():
        p=out/rel
        if not p.is_file(): raise SystemExit('missing '+rel)
        b=p.read_bytes()
        if len(b)!=meta['size'] or sha(b)!=meta['sha256']: raise SystemExit('member mismatch '+rel)
    print(json.dumps({'status':'PASS_LOSSLESS_UNPACK','files':idx['count'],'bytes':idx['total_bytes'],'archive_sha256':pack['archive_sha256']},sort_keys=True))
if __name__=='__main__': main()
