import argparse, base64, hashlib, io, json, lzma, tarfile
from pathlib import Path, PurePosixPath

def sha(b): return hashlib.sha256(b).hexdigest()
def unpack(root, dest):
    root=Path(root); dest=Path(dest)
    if dest.exists(): raise ValueError('destination exists')
    parts=json.loads((root/'ARCHIVE_PARTS_02.json').read_text())
    chunks=[]
    for p in parts['parts']:
        text=(root/p['name']).read_text()
        if sha(text.encode())!=p['sha256']: raise ValueError('part identity:'+p['name'])
        chunks.append(text.strip())
    raw=base64.b64decode(''.join(chunks),validate=True)
    if len(raw)!=parts['decoded_bytes'] or sha(raw)!=parts['decoded_sha256']: raise ValueError('archive identity')
    package=json.loads((root/'PACKAGE_02.json').read_text())
    if len(raw)!=package['archive_bytes'] or sha(raw)!=package['archive_sha256']: raise ValueError('package archive identity')
    tar=lzma.decompress(raw)
    if len(tar)>5_000_000: raise ValueError('expanded tar too large')
    tf=tarfile.open(fileobj=io.BytesIO(tar),mode='r:'); infos=tf.getmembers()
    if len(infos)!=package['members']: raise ValueError('member count')
    dest.mkdir(parents=True); seen=set()
    for ti in infos:
        p=PurePosixPath(ti.name)
        if p.is_absolute() or '..' in p.parts or not ti.isfile() or ti.name in seen: raise ValueError('unsafe member')
        seen.add(ti.name); data=tf.extractfile(ti).read(); want=package['member_sha256'].get(ti.name)
        if want is None or sha(data)!=want: raise ValueError('member identity:'+ti.name)
        out=dest.joinpath(*p.parts); out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(data)
    if set(package['member_sha256'])!=seen: raise ValueError('manifest set')
    return {'members':len(seen),'bytes':sum((dest.joinpath(*PurePosixPath(n).parts)).stat().st_size for n in seen)}

def main():
    p=argparse.ArgumentParser(); p.add_argument('dest'); p.add_argument('--root',default='.'); a=p.parse_args(); print(json.dumps(unpack(a.root,a.dest),sort_keys=True))
if __name__=='__main__': main()
