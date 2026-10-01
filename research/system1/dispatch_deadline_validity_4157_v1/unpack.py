#!/usr/bin/env python3
import argparse, base64, hashlib, json, pathlib, zlib

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out'); a=ap.parse_args()
    root=pathlib.Path(a.out)
    if root.exists(): raise SystemExit('destination exists')
    pack=json.loads(pathlib.Path('PACK.json').read_text())
    enc=pathlib.Path('EVIDENCE.b64').read_text().strip()
    raw=zlib.decompress(base64.b64decode(enc))
    if hashlib.sha256(raw).hexdigest()!=pack['decoded_sha256']: raise SystemExit('decoded hash mismatch')
    obj=json.loads(raw)
    if len(obj)!=pack['files']: raise SystemExit('file count mismatch')
    root.mkdir()
    for rel, entry in obj.items():
        p=pathlib.PurePosixPath(rel)
        if p.is_absolute() or '..' in p.parts: raise SystemExit('unsafe path')
        data=base64.b64decode(entry['b64'])
        if hashlib.sha256(data).hexdigest()!=entry['sha256']: raise SystemExit('member hash mismatch')
        q=root/pathlib.Path(*p.parts); q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(data)
    print(json.dumps({'files':len(obj),'decoded_sha256':pack['decoded_sha256']},sort_keys=True))
if __name__=='__main__': main()
