from __future__ import annotations
import argparse,json,pathlib
from common import *
TASK='TEMPORAL-X11-DISPLACEMENT-OBSERVABILITY-CEILING-R1-20260918-013'

def construction():
    toy_phases=(0,10,50)
    rows=[]
    for phase in toy_phases:
        rows.append({'phase_ms':phase,'blind_tail_witness':blind_tail_witness(phase),'expected':phase>0})
    pats=[(7.0,7.0),(8.0,7.0),(-7.0,-8.0),(6.4,7.0)]
    compat=[{'pair':p,'compatible':pair_full_compatible(p)} for p in pats]
    return {'task':TASK,'mode':'construction','formal_invocation':0,'reruns':0,'rows':rows,'compat':compat}

def formal():
    pattern_checks={str(age):[{'pair':list(p),'full_compatible':pair_full_compatible(p)} for p in PATTERNS[age]] for age in (100,200)}
    boundary_rows=[]
    for age in (100,200):
        spec=BOUNDARY[age]
        for post in spec['directions']:
            for phase in spec['unknown_phases']:
                boundary_rows.append({'age_ms':age,'post_dir':post,'phase_ms':phase,'opposite_current_witness':blind_tail_witness(phase),'timing_identifiable':phase==0})
    out={}
    for age in (100,200):
        rr=[r for r in boundary_rows if r['age_ms']==age]
        ambiguous=sum(r['opposite_current_witness'] for r in rr)
        timing=sum(r['timing_identifiable'] for r in rr)
        correct=BOUNDARY[age]['correct']; total=BOUNDARY[age]['total']
        out[str(age)]={
          'published_correct':correct,
          'published_unknown':len(rr),
          'blind_tail_ambiguous':ambiguous,
          'timing_identifiable':timing,
          'safe_correct_with_phase':correct+timing,
          'safe_accuracy_ceiling_with_phase':(correct+timing)/total,
        }
    return {'task':TASK,'mode':'formal','formal_invocation':1,'reruns':0,'nominal':NOMINAL,'bound':BOUND,'pattern_checks':pattern_checks,'boundary_rows':boundary_rows,'by_age':out}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['construction','formal']);ap.add_argument('out');a=ap.parse_args()
    p=construction() if a.mode=='construction' else formal();pathlib.Path(a.out).write_text(json.dumps(p,separators=(',',':'),sort_keys=True));print(json.dumps(p,sort_keys=True))
if __name__=='__main__':main()
