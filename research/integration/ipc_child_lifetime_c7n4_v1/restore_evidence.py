"""Restore retained evidence bytes only; never execute archived code."""
from __future__ import annotations
import base64,hashlib,json,sys,zipfile
from pathlib import Path, PurePosixPath
HERE=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def safe(n):
    p=PurePosixPath(n)
    return bool(n) and not p.is_absolute() and '..' not in p.parts and str(p)==n and '\\' not in n
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: restore_evidence.py DEST')
    dst=Path(sys.argv[1])
    if dst.exists(): raise SystemExit('destination exists')
    m=json.loads((HERE/'ARCHIVE.json').read_text())
    chunks=[]
    for x in m['parts']:
        p=HERE/x['path']; s=p.read_text('ascii')
        if len(s)!=x['chars'] or sha(s.encode())!=x['sha256']: raise SystemExit('part mismatch')
        chunks.append(s)
    raw=base64.b64decode(''.join(chunks),validate=True)
    if len(raw)!=m['zip_bytes'] or sha(raw)!=m['zip_sha256']: raise SystemExit('zip mismatch')
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist()
        if len(infos)!=m['members'] or sum(i.file_size for i in infos)!=m['expanded_bytes']: raise SystemExit('member count/bytes')
        if any((not safe(i.filename)) or i.is_dir() for i in infos): raise SystemExit('unsafe member')
        dst.mkdir(parents=True)
        for i in infos:
            out=dst/i.filename; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(z.read(i))
    print(json.dumps({'restored_files':m['members'],'restored_bytes':m['expanded_bytes'],'zip_sha256':m['zip_sha256'],'scientific_runs':0},sort_keys=True))
if __name__=='__main__': main()
