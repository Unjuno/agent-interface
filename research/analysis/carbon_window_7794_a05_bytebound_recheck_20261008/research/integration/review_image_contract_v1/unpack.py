from __future__ import annotations
import base64, hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath

PREFIX = PurePosixPath('research/integration/review_image_contract_v1')
FILE_COUNT = 556
EXPANDED_FILE_BYTES = 833770

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit('usage: unpack.py NEW_DIRECTORY')
    here=Path(__file__).resolve().parent
    pack=json.loads((here/'PACK.json').read_text())
    chunks=[]
    for item in pack['capsule']['parts']:
        p=here/item['path']
        raw=base64.b64decode(p.read_text().strip(), validate=True)
        if len(raw)!=item['decoded_bytes'] or hashlib.sha256(raw).hexdigest()!=item['decoded_sha256']:
            raise SystemExit('part integrity mismatch: '+item['path'])
        chunks.append(raw)
    data=b''.join(chunks)
    if len(data)!=pack['capsule']['decoded_bytes'] or hashlib.sha256(data).hexdigest()!=pack['capsule']['sha256']:
        raise SystemExit('capsule integrity mismatch')
    out=Path(sys.argv[1])
    if out.exists(): raise SystemExit('destination already exists')
    out.mkdir(parents=True)
    capsule=out/'_capsule.tar.xz'
    capsule.write_bytes(data)
    files=expanded=0
    with tarfile.open(capsule,'r:xz') as tf:
        members=tf.getmembers()
        for m in members:
            p=PurePosixPath(m.name)
            if p.is_absolute() or '..' in p.parts or not p.is_relative_to(PREFIX): raise SystemExit('unsafe member path')
            if not (m.isdir() or m.isfile()): raise SystemExit('unsupported member type')
            if m.isfile(): files+=1; expanded+=m.size
        if files!=FILE_COUNT or expanded!=EXPANDED_FILE_BYTES: raise SystemExit('capsule inventory mismatch')
        for m in members:
            target=out.joinpath(*PurePosixPath(m.name).parts)
            if m.isdir(): target.mkdir(parents=True,exist_ok=True); continue
            target.parent.mkdir(parents=True,exist_ok=True)
            f=tf.extractfile(m)
            if f is None: raise SystemExit('missing member bytes')
            target.write_bytes(f.read())
    capsule.unlink()
    return 0
if __name__=='__main__': raise SystemExit(main())
