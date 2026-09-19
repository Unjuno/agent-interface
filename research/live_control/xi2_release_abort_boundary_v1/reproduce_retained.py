"""Reconstruct and audit retained FAILED evidence; never emits GUI input.
Requires Python 3.12+ and Pillow. Run from this publication directory.
"""
from __future__ import annotations
import argparse, hashlib, io, json, subprocess, sys, tarfile
from pathlib import Path
EXPECTED_BYTES=32680
EXPECTED_SHA256='36341fd243267095c3243f6d19597d38227948549fabef36e3d4052f0796c143'

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--archive',type=Path);a=ap.parse_args();here=Path(__file__).resolve().parent
    if a.archive:
        raw=a.archive.read_bytes()
    else:
        parts=[here/f'formal-replay.part{i:02d}.bin' for i in range(8)]
        if not all(p.is_file() for p in parts):raise SystemExit('missing replay parts')
        raw=b''.join(p.read_bytes() for p in parts)
    if len(raw)!=EXPECTED_BYTES or sha(raw)!=EXPECTED_SHA256:raise SystemExit('archive digest/size mismatch')
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as tar:
        for member in tar.getmembers():
            path=Path(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts:
                raise SystemExit('unsafe archive member')
        tar.extractall(out,filter='data')
    manifest=json.loads((out/'REPLAY_MANIFEST.json').read_text())
    for name,record in manifest.items():
        data=(out/name).read_bytes()
        if len(data)!=record['bytes'] or sha(data)!=record['sha256']:
            raise SystemExit('manifest mismatch:'+name)
    audit=subprocess.run([sys.executable,str(out/'source/audit.py'),'--root',str(out/'formal'),
        '--plan',str(out/'source/plan.json'),'--freeze',str(out/'source/FREEZE.json'),
        '--out',str(out/'REPLAY_AUDIT.json')],capture_output=True,text=True,timeout=30)
    if audit.returncode!=1:raise SystemExit('frozen failure return code changed:'+audit.stderr)
    if (out/'REPLAY_AUDIT.json').read_bytes()!=(out/'audit-result.json').read_bytes():
        raise SystemExit('frozen FAILED audit not reproduced byte-exactly')
    diagnostic=subprocess.run([sys.executable,str(out/'diagnose_prefix.py'),'--root',str(out),
        '--out',str(out/'REPLAY_DIAGNOSTIC.json')],capture_output=True,text=True,timeout=30)
    if diagnostic.returncode!=0:raise SystemExit('posthoc diagnostic failed:'+diagnostic.stderr)
    if (out/'REPLAY_DIAGNOSTIC.json').read_bytes()!=(out/'DIAGNOSTIC.json').read_bytes():
        raise SystemExit('posthoc diagnostic not reproduced byte-exactly')
    result={'archive_sha256':EXPECTED_SHA256,'manifest_files_verified':len(manifest),
        'frozen_audit_reproduced_byte_exact':True,'frozen_audit_decision':'FAIL_INTEGRITY_OR_CONTROL',
        'posthoc_diagnostic_reproduced_byte_exact':True,'experiment_disposition':'STOPPED_CONTROL_FAILURE',
        'live_cases_executed_by_reconstruction':0}
    (out/'REPLAY_CHECK.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
