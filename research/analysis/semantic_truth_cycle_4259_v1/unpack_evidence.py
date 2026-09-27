import base64,hashlib,io,json,pathlib,sys,tarfile
R=pathlib.Path(__file__).parent
P=json.loads((R/'PACK.json').read_text())
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/semantic-truth-cycle-4279')
if out.exists(): raise SystemExit('destination exists')
part=(R/P['part']['name']).read_bytes()
if len(part)!=P['base64_bytes'] or hashlib.sha256(part).hexdigest()!=P['base64_sha256']: raise SystemExit('part hash')
raw=base64.b64decode(part,validate=True)
if len(raw)!=P['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=P['archive_sha256']: raise SystemExit('archive hash')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as tf:
    members=tf.getmembers()
    files=[m for m in members if m.isfile()]
    if len(files)!=P['members'] or sum(m.size for m in files)!=P['member_bytes']: raise SystemExit('manifest')
    for m in members:
        q=pathlib.PurePosixPath(m.name)
        if m.name.startswith('/') or '..' in q.parts or not (m.isfile() or m.isdir()): raise SystemExit('unsafe member')
    tf.extractall(out)
print(out)
