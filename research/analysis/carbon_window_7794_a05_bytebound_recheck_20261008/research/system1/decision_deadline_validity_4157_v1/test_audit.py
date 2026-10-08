#!/usr/bin/env python3
import copy, json, subprocess, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run_audit(obj):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'RAW.json'; p.write_text(json.dumps(obj))
        cp=subprocess.run([sys.executable,'-I','-S','-B',str(HERE/'audit.py'),str(p)],capture_output=True,text=True,timeout=5)
        return cp.returncode==0

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_audit.py RAW.json')
    base=json.loads(Path(sys.argv[1]).read_text())
    controls=[]
    mutations=[]
    mutations.append(('missing_case',lambda x:x['rows'].pop()))
    mutations.append(('duplicate_case',lambda x:x['rows'].append(copy.deepcopy(x['rows'][0]))))
    mutations.append(('wrong_decision',lambda x:x['rows'][0]['decision'].__setitem__('decision','REFUSE_DECISION_DEADLINE')))
    mutations.append(('effect_on_refusal',lambda x:x['rows'][-1].__setitem__('effect',{'effect_count':1,'received_ns':1,'semantic_valid':True})))
    mutations.append(('semantic_flag',lambda x:x['rows'][0]['effect'].__setitem__('semantic_valid',False)))
    mutations.append(('deadline_shift',lambda x:x['rows'][0]['observation'].__setitem__('decision_deadline_ns',x['rows'][0]['observation']['observation_available_ns']-1)))
    mutations.append(('policy_exit',lambda x:x['rows'][0].__setitem__('policy_exit',7)))
    mutations.append(('app_exit',lambda x:x['rows'][0].__setitem__('app_exit',9)))
    mutations.append(('boolean_time',lambda x:x['rows'][0].__setitem__('proposal_ready_ns',True)))
    mutations.append(('authority_true',lambda x:x['rows'][0]['decision'].__setitem__('authority',True)))
    if not run_audit(base): raise SystemExit('intact evidence failed')
    for name,fn in mutations:
        obj=copy.deepcopy(base); fn(obj); rejected=not run_audit(obj); controls.append({'name':name,'intact_pass':True,'mutation_rejected':rejected})
        if not rejected: raise SystemExit(f'mutation escaped: {name}')
    out={'status':'PASS_COPIED_EVIDENCE_CONTROLS','count':len(controls),'controls':controls}
    print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__': main()
