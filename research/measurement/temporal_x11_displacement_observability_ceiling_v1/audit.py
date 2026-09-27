from __future__ import annotations
import argparse,json,pathlib
from common import *

def audit(path,formal=True):
    p=json.loads(pathlib.Path(path).read_text()); errors=[]; science=[]
    if p.get('formal_invocation')!=(1 if formal else 0):errors.append('invocation')
    if p.get('reruns')!=0:errors.append('reruns')
    if not formal:
        for r in p.get('rows',[]):
            if bool(r['blind_tail_witness']) != bool(r['expected']):errors.append('toy_witness')
        cc=p.get('compat',[])
        exp=[True,True,True,False]
        if [x['compatible'] for x in cc]!=exp:errors.append('toy_compat')
        return {'pass':not errors,'errors':errors}
    if abs(p.get('nominal')-NOMINAL)>1e-12:errors.append('nominal')
    if abs(p.get('bound')-BOUND)>1e-12:errors.append('bound')
    for age in (100,200):
        checks=p['pattern_checks'].get(str(age),[])
        if len(checks)!=len(PATTERNS[age]):errors.append(f'pattern_count_{age}')
        for got,expected in zip(checks,PATTERNS[age]):
            if tuple(got['pair'])!=expected:errors.append(f'pattern_{age}')
            if got['full_compatible'] != pair_full_compatible(expected):errors.append(f'pattern_compat_{age}')
            if not got['full_compatible']:science.append(f'published_pattern_not_full_compatible_{age}')
    rows=p.get('boundary_rows',[])
    if len(rows)!=26:errors.append('row_count')
    for age in (100,200):
        rr=[r for r in rows if r['age_ms']==age]
        expected_n=12 if age==100 else 14
        if len(rr)!=expected_n:errors.append(f'boundary_count_{age}')
        phases=sorted(r['phase_ms'] for r in rr)
        expected_phases=sorted(list(BOUNDARY[age]['unknown_phases'])*2)
        if phases!=expected_phases:errors.append(f'phases_{age}')
        for r in rr:
            if r['post_dir'] not in (-1,1):errors.append('direction')
            if r['opposite_current_witness'] != (r['phase_ms']>0):errors.append('witness')
            if r['timing_identifiable'] != (r['phase_ms']==0):errors.append('timing')
        metric=p['by_age'][str(age)]
        amb=sum(r['phase_ms']>0 for r in rr); timing=sum(r['phase_ms']==0 for r in rr)
        ceiling=(BOUNDARY[age]['correct']+timing)/BOUNDARY[age]['total']
        if metric['published_correct']!=BOUNDARY[age]['correct']:errors.append(f'published_correct_{age}')
        if metric['published_unknown']!=expected_n:errors.append(f'published_unknown_{age}')
        if metric['blind_tail_ambiguous']!=amb:errors.append(f'ambiguous_{age}')
        if metric['timing_identifiable']!=timing:errors.append(f'timing_count_{age}')
        if metric['safe_correct_with_phase']!=BOUNDARY[age]['correct']+timing:errors.append(f'safe_correct_{age}')
        if abs(metric['safe_accuracy_ceiling_with_phase']-ceiling)>1e-12:errors.append(f'ceiling_{age}')
    if not errors:
        if p['by_age']['100']['blind_tail_ambiguous']!=12:science.append('ambiguous100')
        if p['by_age']['200']['blind_tail_ambiguous']!=12:science.append('ambiguous200')
        if p['by_age']['200']['timing_identifiable']!=2:science.append('timing200')
        if p['by_age']['100']['safe_accuracy_ceiling_with_phase']>=.95-1e-12:science.append('ceiling100_reaches_gate')
        if p['by_age']['200']['safe_accuracy_ceiling_with_phase']>=.95-1e-12:science.append('ceiling200_reaches_gate')
    if errors:decision='FAIL_INTEGRITY'
    elif science:
        bad=[x for x in science if x.startswith('ceiling')]
        decision='HOLD_CURRENT_REPRESENTATION_MAY_SUFFICE' if bad else 'PASS_TWO_DISPLACEMENT_OBSERVABILITY_CEILING_SCOPED'
    else: decision='HOLD_BLIND_TAIL_NOT_SUFFICIENT'
    return {'pass':decision=='PASS_TWO_DISPLACEMENT_OBSERVABILITY_CEILING_SCOPED','decision':decision,'errors':errors,'science':science,'by_age':p.get('by_age')}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('path');ap.add_argument('--construction',action='store_true');ap.add_argument('--out');a=ap.parse_args();r=audit(a.path,not a.construction);s=json.dumps(r,separators=(',',':'),sort_keys=True);print(s);pathlib.Path(a.out).write_text(s) if a.out else None
if __name__=='__main__':main()
