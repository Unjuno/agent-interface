#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, lzma, tarfile

HERE = Path(__file__).resolve().parent
META = json.loads((HERE / 'EVIDENCE_ARCHIVE.json').read_text())

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser(description='Restore retained focus/keymap evidence without executing the experiment.')
    ap.add_argument('out', type=Path)
    a=ap.parse_args()
    if a.out.exists():
        raise SystemExit('destination already exists')
    chunks=[]
    for part in META['parts']:
        p=HERE/part['name']; b=p.read_bytes()
        if len(b)!=part['bytes'] or sha256(b)!=part['sha256']:
            raise SystemExit(f'part mismatch: {p.name}')
        chunks.append(b)
    data=b''.join(chunks)
    arc=META['archive']
    if len(data)!=arc['bytes'] or sha256(data)!=arc['sha256']:
        raise SystemExit('archive mismatch')
    raw=lzma.decompress(data)
    a.out.mkdir(parents=True)
    tmp=a.out.parent/(a.out.name+'.tar')
    try:
        tmp.write_bytes(raw)
        with tarfile.open(tmp,'r:') as tf:
            members=tf.getmembers()
            files=[m for m in members if m.isfile()]
            if len(files)!=arc['member_files'] or sum(m.size for m in files)!=arc['expanded_file_bytes']:
                raise SystemExit('member denominator mismatch')
            for m in members:
                if m.name.startswith('/') or '..' in Path(m.name).parts or not (m.isfile() or m.isdir()):
                    raise SystemExit(f'unsafe member: {m.name}')
            tf.extractall(a.out, filter='data')
    finally:
        tmp.unlink(missing_ok=True)
    print(json.dumps({'status':'PASS_RESTORE','files':arc['member_files'],'archive_sha256':arc['sha256']}, sort_keys=True))
if __name__=='__main__': main()
