from __future__ import annotations
import json,sys
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parent
M=[
 {'name':'policy','case':0,'path':['policy'],'value':'MID_EFFECT_SERVO'},
 {'name':'first_step','case':0,'path':['first_step'],'value':[10,6]},
 {'name':'authority','case':1,'path':['authority'],'value':'task'},
 {'name':'servo_correction','case':1,'path':['correction_count'],'value':0},
 {'name':'servo_saved','case':1,'path':['saved_effect_delta'],'value':[49.0,30.0]},
 {'name':'open_pointer','case':0,'path':['pointer_delta_final'],'value':[55,33]},
 {'name':'unavailable_observation','case':2,'path':['observed_effect_delta'],'value':[25,15]},
 {'name':'unavailable_decision','case':2,'path':['decision'],'value':'CORRECT_ONCE'},
 {'name':'neutral','case':3,'path':['final','button1'],'value':True},
 {'name':'process_exit','case':4,'path':['process_exits','xvfb'],'value':9},
 {'name':'mid_observation','case':4,'path':['observed_effect_delta'],'value':[21,12]},
 {'name':'saved_error','case':7,'path':['saved_effect_error'],'value':[1.0,0.0]}
]
def main():
    base=audit.audit(ROOT); out={'baseline':base,'controls':[]}
    if not base['audit_pass']:
        print(json.dumps(out,sort_keys=True));return 2
    for m in M:
        r=audit.audit(ROOT,m); out['controls'].append({'name':m['name'],'rejected':not r['audit_pass'],'errors':r['errors']})
    out['all_rejected']=all(x['rejected'] for x in out['controls']);print(json.dumps(out,sort_keys=True));return 0 if out['all_rejected'] else 1
if __name__=='__main__':raise SystemExit(main())
