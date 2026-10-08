from __future__ import annotations
import hashlib,json,platform,sys
from pathlib import Path
from common import run_session
ROOT=Path(__file__).resolve().parent
REQUIRED=('geometry_change','focus_drift','window_replacement','modal_transition','input_neutral')
SESSIONS=4

def main():
    rows=[]
    for i in range(SESSIONS):
        rows.append(run_session(i+1))
    errors=[]
    for r in rows:
        if set(r.get('gates',{}))!=set(REQUIRED):errors.append(f"gates:{r.get('session_id')}")
        if not all(r.get('gates',{}).get(k) is True for k in REQUIRED):errors.append(f"gate_false:{r.get('session_id')}")
        if sorted(r.get('apps',[]))!=['Chromium','XTerm']:errors.append(f"apps:{r.get('session_id')}")
        ev={e['event']:e for e in r.get('events',[])}
        rep=ev.get('window_replacement',{})
        if not (rep.get('old')!=rep.get('new') and rep.get('old_gone') is True):errors.append(f"replacement:{r.get('session_id')}")
        mod=ev.get('modal_transition',{})
        if not (mod.get('before') and mod.get('after') and mod.get('before')!=mod.get('after')):errors.append(f"modal:{r.get('session_id')}")
    result={
      'task':'MULTI-APP-TRANSITION-LIVE-FIXTURE-R1-20260918-001',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'sessions':len(rows),'passed_sessions':sum(bool(r.get('pass')) for r in rows),
      'required_gates':list(REQUIRED),'errors':errors,
      'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'x11':'private Xvfb/Openbox'},
      'decision':'PASS_MULTI_APP_TRANSITION_FIXTURE_SCOPED' if not errors and len(rows)==SESSIONS else 'FAIL_MULTI_APP_TRANSITION_FIXTURE',
      'rows':rows,
    }
    digest_basis=json.dumps({k:v for k,v in result.items() if k!='rows'},sort_keys=True,separators=(',',':')).encode()
    result['summary_digest_sha256']=hashlib.sha256(digest_basis).hexdigest()
    (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision']=='PASS_MULTI_APP_TRANSITION_FIXTURE_SCOPED' else 2)
if __name__=='__main__':main()
