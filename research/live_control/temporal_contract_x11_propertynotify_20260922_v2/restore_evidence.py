from __future__ import annotations
import base64, hashlib, io, json, lzma, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PACK=json.loads((ROOT/'EVIDENCE_PACK.json').read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def main(out):
    out=Path(out)
    if out.exists(): raise SystemExit('destination exists')
    chunks=[]
    for p in PACK['parts']:
        b=(ROOT/p['name']).read_bytes()
        if len(b)!=p['bytes'] or sha(b)!=p['sha256']: raise SystemExit('part mismatch '+p['name'])
        chunks.append(b)
    raw=base64.b64decode(b''.join(chunks),validate=True)
    if len(raw)!=PACK['archive_bytes'] or sha(raw)!=PACK['archive_sha256']: raise SystemExit('archive mismatch')
    tar_bytes=lzma.decompress(raw)
    out.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:') as tf:
        members=tf.getmembers()
        for m in members:
            dest=(out/m.name).resolve()
            if out.resolve() not in dest.parents and dest!=out.resolve(): raise SystemExit('unsafe path')
            if not m.isfile(): raise SystemExit('non-file member')
        tf.extractall(out,filter='data')
    manifest=json.loads((out/'EVIDENCE_MANIFEST.json').read_text())
    if len(manifest['files'])!=PACK['expanded_files']: raise SystemExit('manifest count')
    for row in manifest['files']:
        p=out/row['path']; b=p.read_bytes()
        if len(b)!=row['bytes'] or sha(b)!=row['sha256']: raise SystemExit('member mismatch '+row['path'])
    print('PASS_RESTORE',len(manifest['files']))
if __name__=='__main__':
    import sys
    if len(sys.argv)!=2: raise SystemExit('usage: restore_evidence.py OUT')
    main(sys.argv[1])
