from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
from common import run_session,evaluate,TASK
ROOT=Path(__file__).resolve().parent
SESSIONS=4

def version(cmd):
    try:return subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True,timeout=3).strip().splitlines()[0]
    except Exception:return 'unknown'

def main():
    rows=[]; errors=[]
    for i in range(1,SESSIONS+1):
        r=run_session(i); r['errors']=evaluate(r); r['pass']=not r['errors']; rows.append(r)
        errors.extend(f"session{i}:{e}" for e in r['errors'])
    result={
      'task':TASK,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'sessions':len(rows),'passed_sessions':sum(r['pass'] for r in rows),'errors':errors,
      'decision':'PASS_MULTI_APP_GUARDED_RECOVERY_A2_SCOPED' if len(rows)==SESSIONS and not errors else 'FAIL_MULTI_APP_GUARDED_RECOVERY_A2',
      'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'chromium':version(['chromium','--version']),'xterm':version(['xterm','-version']),'x11':'private Xvfb/Openbox'},
      'rows':rows,
    }
    basis=json.dumps({k:v for k,v in result.items() if k!='rows'},sort_keys=True,separators=(',',':')).encode()
    result['summary_digest_sha256']=hashlib.sha256(basis).hexdigest()
    (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_MULTI_APP_GUARDED_RECOVERY_A2_SCOPED' else 2)
if __name__=='__main__':main()
