#!/usr/bin/env python3
"""Offline publication verification. Never runs the consumed formal allocation."""
from pathlib import Path
import hashlib, json, subprocess, sys, tarfile, tempfile

HERE=Path(__file__).resolve().parent
META=json.loads((HERE/'EVIDENCE_ARCHIVE.json').read_text())
RESULT=json.loads((HERE/'RESULT.json').read_text())

def sha256(p):
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def run(args,cwd=None):
    cp=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=30)
    if cp.returncode!=0:
        raise SystemExit(f"command failed rc={cp.returncode}: {args}\nstdout={cp.stdout}\nstderr={cp.stderr}")
    return cp.stdout

def main():
    arc=HERE/'EVIDENCE.tar.gz'
    if arc.stat().st_size!=META['bytes'] or sha256(arc)!=META['sha256']:
        raise SystemExit('archive identity mismatch')
    with tempfile.TemporaryDirectory(prefix='deadline-4157-review-') as d:
        out=Path(d)/'evidence'; out.mkdir()
        with tarfile.open(arc,'r:gz') as tf:
            members=tf.getmembers(); files=[m for m in members if m.isfile()]
            if len(files)!=META['member_files'] or sum(m.size for m in files)!=META['expanded_file_bytes']:
                raise SystemExit('archive denominator mismatch')
            if [m.name for m in files] != META['members']:
                raise SystemExit('archive member order/path mismatch')
            for m in members:
                if m.name.startswith('/') or '..' in Path(m.name).parts or not (m.isfile() or m.isdir()):
                    raise SystemExit(f'unsafe archive member: {m.name}')
            tf.extractall(out,filter='data')
        raw=out/'formal-01'/'RAW.json'
        if sha256(raw)!=RESULT['raw_sha256']:
            raise SystemExit('raw hash mismatch')
        audit=run([sys.executable,'-S','-B',str(HERE/'audit.py'),str(raw)])
        audit_obj=json.loads(audit)
        if audit_obj['status']!='PASS_DEADLINE_VALIDITY_SCOPED' or audit_obj['errors']:
            raise SystemExit('audit disagreement')
        controls=run([sys.executable,'-S','-B',str(HERE/'test_audit.py'),str(raw)])
        controls_obj=json.loads(controls)
        if controls_obj['status']!='PASS_COPIED_EVIDENCE_CONTROLS' or controls_obj['count']!=10:
            raise SystemExit('control disagreement')
        unit=subprocess.run([sys.executable,'-S','-B','-m','unittest','-v','test_policy'],cwd=HERE,capture_output=True,text=True,timeout=20)
        if unit.returncode!=0:
            raise SystemExit('unit tests failed: '+unit.stderr)
        print(json.dumps({'status':'PASS_PUBLICATION_VERIFY','cases':audit_obj['cases'],'checks':audit_obj['checks'],'mutation_controls':controls_obj['count'],'unit_methods':8,'formal_reruns':0},sort_keys=True))
if __name__=='__main__': main()
