import base64,hashlib,json,lzma,tarfile,pathlib,sys,io
R=pathlib.Path(__file__).parent; P=json.loads((R/'PACK.json').read_text())
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/predicate-cache-persist-4236-evidence')
if out.exists(): raise SystemExit('destination exists')
chunks=[]
for e in P['parts']:
 b=(R/e['name']).read_bytes()
 if hashlib.sha256(b).hexdigest()!=e['sha256']: raise SystemExit('part hash')
 chunks.append(b.decode().strip())
enc=''.join(chunks); raw=base64.b64decode(enc,validate=True)
if hashlib.sha256(raw).hexdigest()!=P['archive_sha256'] or len(raw)!=P['archive_bytes']: raise SystemExit('archive hash')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as tf:
 for m in tf.getmembers():
  if m.name.startswith('/') or '..' in pathlib.PurePosixPath(m.name).parts or not m.isfile(): raise SystemExit('unsafe member')
 tf.extractall(out)
print(out)
