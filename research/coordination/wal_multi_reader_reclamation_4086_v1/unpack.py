from pathlib import Path
import base64,hashlib,json,tarfile,io,sys
root=Path(__file__).resolve().parent; out=Path(sys.argv[1]).resolve(); pack=json.loads((root/'PACKAGE.json').read_text())
if out.exists(): raise SystemExit('destination exists')
text=''.join((root/x['path']).read_text().strip() for x in pack['parts']); raw=base64.b64decode(text,validate=True)
if hashlib.sha256(raw).hexdigest()!=pack['archive_sha256']: raise SystemExit('archive hash')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as t:
 for m in t.getmembers():
  if not m.isfile() or m.name.startswith('/') or '..' in Path(m.name).parts: raise SystemExit('unsafe member')
  p=out/m.name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(t.extractfile(m).read())
print(pack['archive_sha256'])
