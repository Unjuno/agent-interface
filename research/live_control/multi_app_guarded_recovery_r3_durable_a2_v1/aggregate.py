from __future__ import annotations
import hashlib,json,platform,subprocess,sys
from pathlib import Path
TASK='MULTI-APP-GUARDED-RECOVERY-R3-DURABLE-A2-20260918-004'
PARENT='MULTI-APP-GUARDED-RECOVERY-R3-20260918-003'
ROOT=Path(__file__).resolve().parent

def version(cmd):
    try:return subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True,timeout=3).strip().splitlines()[0]
    except Exception:return 'unknown'

def main():
    batches=[];errors=[]
    for i in range(1,5):
        p=ROOT/f'BATCH_{i}.json'
        if not p.exists(): errors.append(f'missing_batch:{i}'); continue
        b=json.loads(p.read_text());batches.append(b)
        if b.get('task')!=TASK or b.get('parent_science_task')!=PARENT or b.get('session_id')!=i:errors.append(f'envelope:{i}')
        if (b.get('batch_invocations'),b.get('reruns'),b.get('replacements'),b.get('tuning'))!=(1,0,0,0):errors.append(f'discipline:{i}')
        if b.get('row',{}).get('pass') is not True or b.get('row',{}).get('errors')!=[]:errors.append(f'science:{i}')
    rows=[b['row'] for b in batches if 'row' in b]
    refusal=sum(len(r.get('refusals',[])) for r in rows); zero=sum(x.get('input_before')==x.get('input_after') for r in rows for x in r.get('refusals',[])); active=sum(x.get('active_before')==x.get('window') for r in rows for x in r.get('task_batches',[])); effects=sum(len(r.get('effects',[])) for r in rows); reps=sum(len(r.get('replacements',[])) for r in rows); neutral=sum(r.get('terminal_neutral') is True for r in rows)
    if len(rows)==4 and (refusal,zero,active,effects,reps,neutral)!=(48,48,48,48,12,4):errors.append('aggregate_gate')
    result={'schema':'multi-app-guarded-recovery-r3-durable-result-v1','task':TASK,'parent_science_task':PARENT,'formal_invocations':1,'batch_invocations':{str(i):1 for i in range(1,5)},'reruns':0,'replacements':0,'tuning':0,'sessions':len(rows),'passed_sessions':sum(r.get('pass') is True for r in rows),'aggregate':{'refusal_gates':refusal,'refusal_zero_task_input':zero,'fallback_active_match':active,'effects':effects,'replacement_valid':reps,'terminal_neutral':neutral},'errors':errors,'decision':'PASS_MULTI_APP_GUARDED_RECOVERY_R3_DURABLE_A2_SCOPED' if not errors and len(rows)==4 else 'STOP_OR_FAIL_MULTI_APP_GUARDED_RECOVERY_R3_DURABLE_A2','environment':{'python':sys.version.split()[0],'platform':platform.platform(),'chromium':version(['chromium','--version']),'xterm':version(['xterm','-version']),'x11':'private Xvfb/Openbox'},'batch_sha256':{str(b['session_id']):hashlib.sha256((ROOT/f"BATCH_{b['session_id']}.json").read_bytes()).hexdigest() for b in batches},'rows':rows}
    (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2,sort_keys=True))
    raise SystemExit(0 if result['decision'].startswith('PASS_') else 2)
if __name__=='__main__':main()
