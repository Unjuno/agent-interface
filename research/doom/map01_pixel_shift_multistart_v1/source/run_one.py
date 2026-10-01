from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path

def main(plan,case_id,root,python,ledger):
    p=json.loads(plan.read_text()); by={c['id']:c for c in p['cases']}
    if case_id not in by: raise SystemExit('unknown case id')
    if ledger.exists(): state=json.loads(ledger.read_text())
    else: state={'task':p['task'],'started':{},'completed':{},'failed':{}}
    if case_id in state['started'] or case_id in state['completed'] or case_id in state['failed']:
        raise RuntimeError(('case already consumed',case_id,state))
    root.mkdir(parents=True,exist_ok=True)
    state['started'][case_id]={'started_ns':time.time_ns()}; ledger.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
    c=by[case_id]; cfile=root/(case_id+'.case.json'); cfile.write_text(json.dumps(c,sort_keys=True)+'\n'); cd=root/case_id
    try:
        cp=subprocess.run([str(python),str(Path(__file__).parent/'run_case.py'),'--case',str(cfile),'--out',str(cd)],capture_output=True,text=True,timeout=50)
        (root/(case_id+'.stdout')).write_text(cp.stdout); (root/(case_id+'.stderr')).write_text(cp.stderr); (root/(case_id+'.exit')).write_text(str(cp.returncode)+'\n')
        if cp.returncode!=0: raise RuntimeError((case_id,cp.stderr[-3000:]))
        r=json.loads((cd/'result.json').read_text())
        state=json.loads(ledger.read_text()); state['completed'][case_id]={'completed_ns':time.time_ns(),'result_sha256':__import__('hashlib').sha256((cd/'result.json').read_bytes()).hexdigest()}; state['started'].pop(case_id,None); ledger.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'id':case_id,'status':r['terminal_status'],'setup':r['setup_right_pulses'],'corr':r['correction_pulses'],'yaw_error':r['terminal_yaw_error'],'within':r['within_6deg'],'false_matched':r['false_matched'],'ref_delta':r['reference_yaw_delta_from_initial']}),flush=True)
    except Exception as e:
        state=json.loads(ledger.read_text()); state['failed'][case_id]={'failed_ns':time.time_ns(),'error':repr(e)}; state['started'].pop(case_id,None); ledger.write_text(json.dumps(state,indent=2,sort_keys=True)+'\n'); raise
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--case-id',required=True);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--python',type=Path,required=True);ap.add_argument('--ledger',type=Path,required=True);a=ap.parse_args();main(a.plan,a.case_id,a.root,a.python,a.ledger)
