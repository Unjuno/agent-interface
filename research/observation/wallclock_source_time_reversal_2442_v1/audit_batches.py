"""Pre-frozen batch-envelope verifier; invokes the independent raw auditor on a lossless aggregate view."""
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
COUNTS=(9,9,8,8)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected_names():
    out=[]
    for age in (75,100,150,200):
      for post in (-1,1):
       for phase in (0,33,66):out.append(f'REV{age}-D{post}-P{phase}')
    for post in (-1,1):
      out += [f'CONST-D{post}',f'DELAY-D{post}',f'HOLD-D{post}',f'ACCEL-D{post}',f'DOUBLE-D{post}']
    return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--out',required=True);a=ap.parse_args(); root=Path(a.root)
    freeze=json.loads((ROOT/'FREEZE02.json').read_text())
    for n,h in freeze['files'].items():
        if sha(ROOT/n)!=h: raise SystemExit(f'FREEZE02_HASH:{n}')
    seen=[]; endpoint=[]; posthash=None
    td=Path(tempfile.mkdtemp(prefix='2442-aggregate-'))
    try:
      (td/'START.json').write_text(json.dumps({'construction':False,'aggregate_from_batches':True})+'\n')
      for b,cnt in enumerate(COUNTS):
        bd=root/f'batch-{b}'; wrap=json.loads((bd/'BATCH_WRAPPER.json').read_text()); end=json.loads((bd/'END.json').read_text())
        if wrap['batch']!=b or wrap['run_returncode']!=0 or len(wrap['case_names'])!=cnt:raise SystemExit(f'WRAP:{b}')
        if end['stop'] is not None or end['xvfb_returncode']!=0 or not end['private_socket_and_auth_removed'] or end['case_count']!=cnt:raise SystemExit(f'END:{b}')
        if posthash is None:posthash=end['source_hashes_after']
        elif posthash!=end['source_hashes_after']:raise SystemExit('POSTHASH')
        dirs=sorted(p for p in bd.iterdir() if p.is_dir() and (p/'RESULT.json').exists())
        if len(dirs)!=cnt:raise SystemExit(f'DENOM:{b}')
        for d in dirs:
            name=json.loads((d/'RESULT.json').read_text())['case']['name'];seen.append(name)
            dest=td/d.name
            if dest.exists(): dest=td/f'b{b}-{d.name}'
            os.symlink(d,dest,target_is_directory=True)
        endpoint.append({'batch':b,'end_sha256':sha(bd/'END.json'),'wrapper_sha256':sha(bd/'BATCH_WRAPPER.json'),'case_count':cnt})
      if seen!=expected_names():raise SystemExit('CASE_ORDER_OR_IDENTITY')
      (td/'END.json').write_text(json.dumps({'stop':None,'xvfb_returncode':0,'private_socket_and_auth_removed':True,'input_dispatched':False,'source_hashes_after':posthash})+'\n')
      cmd=[sys.executable,'-B',str(ROOT/'audit.py'),str(td),'--study',str(ROOT),'--controls']
      p=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
      if p.returncode!=0:raise SystemExit('RAW_AUDIT:'+p.stdout+p.stderr)
      audit=json.loads(p.stdout)
      out={'allocation':'wallclock-source-time-reversal-2442-20260922-02-batches','batch_endpoints':endpoint,'case_count':len(seen),'case_names':seen,'raw_audit':audit,'raw_audit_stdout_sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'audit_process_returncode':p.returncode}
      Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return 0
    finally: shutil.rmtree(td,ignore_errors=True)
if __name__=='__main__':raise SystemExit(main())
