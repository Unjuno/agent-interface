from __future__ import annotations
import base64, hashlib, json, lzma, tarfile, tempfile, io, pathlib, subprocess, sys
HERE=pathlib.Path(__file__).resolve().parent
META=json.loads((HERE/'PUBLICATION.json').read_text())
parts=[]
for row in META['parts']:
    p=HERE/'capsule_parts'/row['name']
    data=p.read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    parts.append(data.decode().strip())
xz=base64.b64decode(''.join(parts),validate=True)
assert len(xz)==META['capsule']['bytes'] and hashlib.sha256(xz).hexdigest()==META['capsule']['sha256']
with tempfile.TemporaryDirectory(prefix='cyclic-grounding-review-') as td:
    dest=pathlib.Path(td)
    raw=lzma.decompress(xz)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
        members=tf.getmembers()
        assert len(members)==META['capsule']['members']
        for m in members:
            assert m.isfile() and not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts
        tf.extractall(dest, filter='data')
    proc=subprocess.run([sys.executable,'-I','-S','-B',str(dest/'source/audit.py'),str(dest/'evaluation/RAW.jsonl'),str(dest)],cwd=dest,text=True,capture_output=True)
    if proc.returncode!=0: raise SystemExit(proc.stderr or proc.stdout)
    observed=json.loads(proc.stdout)
    expected=json.loads((dest/'AUDIT.json').read_text())
    assert observed==expected
    proc2=subprocess.run([sys.executable,'-I','-S','-B',str(dest/'source/controls.py'),str(dest/'evaluation/RAW.jsonl'),str(dest)],cwd=dest,text=True,capture_output=True)
    if proc2.returncode!=0: raise SystemExit(proc2.stderr or proc2.stdout)
    controls=json.loads(proc2.stdout)
    expected_controls=json.loads((dest/'CONTROLS.json').read_text())
    assert controls==expected_controls
    print(json.dumps({'decision':'PASS_READONLY_RECONSTRUCTION','audit_checks':observed.get('checks'),'control_count':len(controls.get('controls',[])),'scientific_reruns':0},sort_keys=True))
