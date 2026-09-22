#!/usr/bin/env python3
import argparse, base64, hashlib, json, lzma, os, tarfile
from pathlib import Path

MAX_ARCHIVE = 4_000_000
MAX_EXPANDED = 20_000_000

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out',type=Path); a=ap.parse_args()
    if a.out.exists(): raise SystemExit('destination exists')
    root=Path(__file__).resolve().parent
    meta=json.loads((root/'EVIDENCE_MANIFEST.json').read_text())
    data=b''.join(base64.b64decode(b''.join((root/p).read_bytes().split()),validate=True) for p in meta['parts'])
    if len(data)>MAX_ARCHIVE or len(data)!=meta['archive_bytes'] or hashlib.sha256(data).hexdigest()!=meta['archive_sha256']:
        raise SystemExit('archive integrity failure')
    raw=lzma.decompress(data,format=lzma.FORMAT_XZ,memlimit=256*1024*1024)
    if len(raw)>MAX_EXPANDED or len(raw)!=meta['tar_bytes'] or hashlib.sha256(raw).hexdigest()!=meta['tar_sha256']:
        raise SystemExit('tar integrity failure')
    a.out.mkdir(parents=True)
    import io
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
        members=tf.getmembers()
        if len(members)!=meta['members']: raise SystemExit('member count mismatch')
        for m in members:
            p=Path(m.name)
            if m.issym() or m.islnk() or p.is_absolute() or '..' in p.parts: raise SystemExit('unsafe member')
        tf.extractall(a.out,filter='data')
    manifest=json.loads((a.out/'EVIDENCE_FILES.json').read_text())
    for rel,want in manifest['sha256'].items():
        p=a.out/rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=want: raise SystemExit('member hash mismatch: '+rel)
    print(json.dumps({'status':'PASS_RESTORE','members':meta['members'],'archive_sha256':meta['archive_sha256']},sort_keys=True))
if __name__=='__main__': main()
