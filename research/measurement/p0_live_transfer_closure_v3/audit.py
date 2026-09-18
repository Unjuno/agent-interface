from __future__ import annotations
import argparse,copy,json
from pathlib import Path
from model import evaluate

def main():
    ap=argparse.ArgumentParser();ap.add_argument('facts');ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    f=json.loads(Path(a.facts).read_text()); got=json.loads(Path(a.result).read_text()); errors=[]
    exp=evaluate(f)
    if got!=exp: errors.append('recompute')
    muts=[]
    x=copy.deepcopy(f);x['live_1276']['is_live_task_effect']=True;muts.append(('physical_to_effect',x))
    x=copy.deepcopy(f);x['parent_1100']['decision']='PASS_FAKE';muts.append(('drop_parent_pass',x))
    x=copy.deepcopy(f);x['cross_process_clock_axis_proven']=True;muts.append(('clock_intent_to_proof',x))
    detected={}
    for name,x in muts:
        y=evaluate(x); detected[name]=(y['decision']!='PASS_P0_ONLY_LIVE_CAUSAL_EFFECT_REMAINS_SCOPED' or name=='clock_intent_to_proof' and y['cross_process_live_useful_control_proven'] is False)
    if not all(detected.values()): errors.append('corruption_control')
    if got.get('LIVE_CAUSAL_EFFECT_SAMPLE')!='UNPROVEN_CURRENT': errors.append('effect_gate')
    if got.get('same_process_live_useful_control_proven') is not False: errors.append('same_process_overclaim')
    if got.get('cross_process_live_useful_control_proven') is not False: errors.append('cross_process_overclaim')
    out={'pass':not errors,'errors':errors,'decision':got.get('decision'),'corruption_controls':detected}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))

if __name__=='__main__': main()
