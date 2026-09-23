import base64,hashlib,io,json,lzma,tarfile,sys
from pathlib import Path
root=Path(__file__).resolve().parent; out=Path(sys.argv[1])
if out.exists(): raise SystemExit('destination_exists')
parts=json.loads((root/'PARTS.json').read_text()); info=json.loads((root/'COMPACT_EVIDENCE.json').read_text()); original=json.loads((root/'EVIDENCE.json').read_text())
chunks=[]
for item in parts['parts']:
    p=root/item['path']; raw=p.read_bytes()
    if len(raw)!=item['chars'] or hashlib.sha256(raw).hexdigest()!=item['sha256']: raise SystemExit('part_integrity')
    chunks.append(raw.decode().strip())
s=''.join(chunks)
if len(s)!=parts['combined_b64_chars']: raise SystemExit('combined_b64_chars')
xz=base64.b64decode(s,validate=True)
if len(xz)!=info['xz_bytes'] or hashlib.sha256(xz).hexdigest()!=info['xz_sha256'] or info['xz_sha256']!=parts['xz_sha256']: raise SystemExit('xz_integrity')
tar=lzma.decompress(xz)
if len(tar)!=info['tar_bytes'] or hashlib.sha256(tar).hexdigest()!=info['tar_sha256']: raise SystemExit('tar_integrity')
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
    blobs={m.name:tf.extractfile(m).read() for m in tf if m.isfile()}
cm=json.loads(blobs['COMPACT_MANIFEST.json'])
obs_by={x['original_path']:x for x in cm['observers']}
def read_u(data,pos):
    n=0; shift=0
    while True:
        if pos>=len(data): raise SystemExit('varint_eof')
        b=data[pos]; pos+=1; n|=(b&127)<<shift
        if b<128:return n,pos
        shift+=7
        if shift>70: raise SystemExit('varint_overflow')
def unzig(v): return (v>>1)^-(v&1)
def restore_obs(data):
    if data[:4]!=b'OBS1': raise SystemExit('observer_magic')
    pos=4; pid,pos=read_u(data,pos); ready,pos=read_u(data,pos); count,pos=read_u(data,pos); rows=[]; prev=ready
    for i in range(count):
        z,pos=read_u(data,pos); dur,pos=read_u(data,pos); start=prev+unzig(z); end=start+dur
        r={'i':i,'start_ns':start,'end_ns':end,'duration_ns':dur}
        if i==count-1:r['final']=True
        rows.append(r); prev=end
    if pos!=len(data): raise SystemExit('observer_trailing')
    return json.dumps({'pid':pid,'ready_ns':ready,'rows':rows},sort_keys=True,separators=(',',':')).encode()
out.mkdir(parents=True)
try:
    for item in original['members']:
        path=item['path']; dst=out/path; dst.parent.mkdir(parents=True,exist_ok=True)
        if path in obs_by: data=restore_obs(blobs[obs_by[path]['compact_path']])
        else:
            key='exact/'+path
            if key not in blobs: raise SystemExit('missing_exact_member')
            data=blobs[key]
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']: raise SystemExit('restored_member_integrity')
        dst.write_bytes(data)
except Exception:
    import shutil; shutil.rmtree(out,ignore_errors=True); raise
print(json.dumps({'restored':len(original['members']),'bytes':sum(x['bytes'] for x in original['members']),'xz_sha256':info['xz_sha256']},sort_keys=True))
