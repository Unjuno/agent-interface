from __future__ import annotations
import datetime as dt, hashlib, json, subprocess, sys, time
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]; RUN=P/'run'
C=json.loads((P/'conditions.json').read_text(encoding='utf-8'))
def save(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def manifest():
    rows=[]
    for f in sorted(x for x in P.rglob('*') if x.is_file() and x.name!='SHA256SUMS'):
        rows.append(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(P).as_posix())
    (P/'SHA256SUMS').write_text('\n'.join(rows)+'\n',encoding='ascii')
def main():
    if sys.platform!='win32': raise SystemExit('R43 requires native Windows')
    if any((P/name).exists() for name in ['run','task_raw.json','audit_r43.json','phases.json','PRERUN_CUSTODY.json','SHA256SUMS']): raise SystemExit('one-shot outputs already exist; refusing replay')
    prepath=P/'preflight.json'
    if prepath.exists():
        predata=json.loads(prepath.read_text(encoding='utf-8'))
        age=(dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(predata['utc'])).total_seconds()
        cond_sha=hashlib.sha256((P/'conditions.json').read_bytes()).hexdigest()
        if (predata.get('status')!='PASS' or predata.get('attempt_id')!=C['attempt_id']
                or predata.get('source_commit')!=C['source_commit']
                or predata.get('conditions_sha256')!=cond_sha or not 0<=age<=300):
            raise SystemExit('retained preflight is not a fresh PASS for this frozen attempt')
        print(json.dumps({'retained_preflight':True,'status':predata['status'],'age_seconds':age},sort_keys=True))
    else:
        pre=subprocess.run([sys.executable,str(P/'preflight_r43.py')],cwd=ROOT,capture_output=True,text=True,timeout=45)
        print(pre.stdout,end='')
        if pre.returncode:
            if pre.stderr: print(pre.stderr,file=sys.stderr)
            return pre.returncode
        predata=json.loads(prepath.read_text(encoding='utf-8'))
    save(P/'PRERUN_CUSTODY.json',{'schema':'win32-r43-custody-v1','attempt_id':C['attempt_id'],'source_commit':C['source_commit'],'conditions_sha256':hashlib.sha256((P/'conditions.json').read_bytes()).hexdigest(),'preflight_sha256':hashlib.sha256((P/'preflight.json').read_bytes()).hexdigest(),'native_input_sent':False,'task_output_absent_before_launch':not RUN.exists(),'preflight':predata})
    phases={'schema':'win32-r43-phases-v1','attempt_id':C['attempt_id'],'task_started_monotonic_ns':time.monotonic_ns()}
    task=subprocess.run([sys.executable,str(P/'task_probe.py')],cwd=ROOT,capture_output=True,text=True,timeout=C['timeouts_seconds']['attempt_total']+15)
    phases['task_returned_monotonic_ns']=time.monotonic_ns(); phases['task_exit_code']=task.returncode; phases['stdout']=task.stdout; phases['stderr']=task.stderr
    result=P/'run'/'phase2_task'/'result.json'
    if result.exists(): save(P/'task_raw.json',json.loads(result.read_text(encoding='utf-8')))
    else: save(P/'task_raw.json',{'attempt_id':C['attempt_id'],'status':'FAIL_OR_UNKNOWN','exit_code':task.returncode,'stdout':task.stdout,'stderr':task.stderr})
    save(P/'phases.json',phases)
    audit=subprocess.run([sys.executable,str(P/'audit_r43.py')],cwd=ROOT,capture_output=True,text=True,timeout=20)
    print(audit.stdout,end='')
    if audit.stderr: print(audit.stderr,file=sys.stderr)
    manifest()
    return task.returncode or audit.returncode
if __name__=='__main__': raise SystemExit(main())
