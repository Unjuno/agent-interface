from __future__ import annotations
import base64, hashlib, io, json, lzma, pathlib, sys, tarfile
R=pathlib.Path(__file__).resolve().parent
M=json.loads((R/'CAPSULE.json').read_text())
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/live-typed-negative-outcome-v1')
if out.exists(): raise SystemExit('destination exists')
comp=base64.b64decode((R/M['archive_file']).read_text().strip(),validate=True)
if len(comp)!=M['archive_size'] or hashlib.sha256(comp).hexdigest()!=M['archive_sha256']: raise SystemExit('archive mismatch')
raw=lzma.decompress(comp)
if len(raw)!=M['tar_size'] or hashlib.sha256(raw).hexdigest()!=M['tar_sha256']: raise SystemExit('tar mismatch')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
    members=[m for m in tf.getmembers() if m.isfile()]
    if len(members)!=M['member_count']: raise SystemExit('member count')
    for m in members:
        p=pathlib.PurePosixPath(m.name)
        if p.is_absolute() or '..' in p.parts: raise SystemExit('unsafe path')
        data=tf.extractfile(m).read(); dst=out.joinpath(*p.parts); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(data)
print('PASS_RESTORE',M['member_count'],M['archive_sha256'])
