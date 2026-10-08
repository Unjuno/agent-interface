"""Read-only restore/verification for #2802 allocation02. Never invokes run_batch.py or case.py."""
from pathlib import Path
import hashlib, io, json, lzma, subprocess, sys, tarfile
ROOT=Path(__file__).resolve().parent
CAP=json.loads((ROOT/'CAPSULE.json').read_text())
raw=(ROOT/'EVIDENCE.tar.xz').read_bytes()
if len(raw)!=CAP['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=CAP['archive_sha256']: raise SystemExit('archive identity')
tar=lzma.decompress(raw)
if len(tar)!=CAP['tar_bytes'] or hashlib.sha256(tar).hexdigest()!=CAP['tar_sha256']: raise SystemExit('tar identity')
out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'restored'
if out.exists(): raise SystemExit('destination exists')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
    members=tf.getmembers(); files=[m for m in members if m.isfile()]
    if len(files)!=CAP['member_files'] or sum(m.size for m in files)!=CAP['member_bytes']: raise SystemExit('member denominator')
    for m in members:
        p=Path(m.name)
        if m.issym() or m.islnk() or p.is_absolute() or '..' in p.parts: raise SystemExit('unsafe member')
    for m in files:
        target=out/m.name; target.parent.mkdir(parents=True,exist_ok=True)
        with tf.extractfile(m) as src, target.open('wb') as dst: dst.write(src.read())
checks={'FREEZE.json':'f8a5b6f5b5e09baf5e5cf0d8392f12ac7951957c29bedf5202d1976dda5803c8','formal-02/RUN.json':'dccaf122c990ff492d5a90af6c5312db88c6776229408f110276c05de0aa07bb','AUDIT.json':'75a1e585cfbe4d81abfaa2fe1587eef17419a63d42e137202c7cb011b2acc748','AUDIT_CONTROLS.json':'b21586376aae34f245f5977fc0f04c8cefa70a77e46414b67aa9ecc167e15d25'}
for name,want in checks.items():
    if hashlib.sha256((out/name).read_bytes()).hexdigest()!=want: raise SystemExit('retained hash '+name)
p=subprocess.run([sys.executable,'-B',str(out/'audit.py'),str(out/'formal-02'),'--controls'],capture_output=True,text=True)
if p.returncode!=0: raise SystemExit('audit failed: '+p.stderr)
audit=json.loads(p.stdout)
if audit.get('scientific_decision')!='PASS_X11_TIMESTAMP_ORDER_BOUNDARY_SCOPED' or audit.get('errors')!=[] or not all(audit.get('corruption_controls',{}).values()): raise SystemExit('audit decision')
u=subprocess.run([sys.executable,'-B','-m','unittest','-v','test_policies'],cwd=out,capture_output=True,text=True)
if u.returncode!=0: raise SystemExit('units failed: '+u.stderr)
print(json.dumps({'status':'PASS_RESTORE','files':len(files),'audit':audit['scientific_decision']},sort_keys=True))
