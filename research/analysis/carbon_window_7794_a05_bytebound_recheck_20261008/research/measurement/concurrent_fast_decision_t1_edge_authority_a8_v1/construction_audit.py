from __future__ import annotations
import argparse,copy,json
from pathlib import Path
from audit import BASE,CAND,CLEAR,WATCH,FRONTIER,PROGRAMS,INITIAL,transition_program,observed_clear_entries,state_intervals
TASK='CONCURRENT-FAST-DECISION-T1-X11-EDGE-AUTHORITY-A8-20260918-008'

def evaluate(r):
    errors=[]
    if r.get('task')!=TASK or r.get('phase')!='construction' or r.get('construction_invocations')!=1 or r.get('formal_invocations')!=0: errors.append('contract')
    if any(r.get(k)!=0 for k in ('reruns','replacements','tuning')): errors.append('rerun_contract')
    if r.get('scenario')!='TRANSIENT_28' or r.get('pairs')!=1 or len(r.get('cases',[]))!=2 or len(r.get('child_runs',[]))!=2: errors.append('shape')
    if any(x.get('returncode')!=0 for x in r.get('child_runs',[])): errors.append('child_exit')
    by={c.get('arm'):c for c in r.get('cases',[])}
    if set(by)!={BASE,CAND}: errors.append('arms')
    for arm,c in by.items():
        cid=c.get('case_id','?')
        if c.get('initial_state')!=INITIAL['TRANSIENT_28']: errors.append(cid+':initial')
        if transition_program(c)!=PROGRAMS['TRANSIENT_28']: errors.append(cid+':transition_program')
        if c.get('exceptions'): errors.append(cid+':exception')
        if c.get('terminal_f8_up') is not True: errors.append(cid+':terminal')
        if not all(c.get('cleanup',{}).get(k) is True for k in ('xvfb_exit','tk_destroyed','control_closed','scorer_closed')): errors.append(cid+':cleanup')
        handback=c.get('start_ns',0)+FRONTIER
        close=c.get('authority_stop_set_ns')
        if c.get('authority_deadline_ns')!=handback or not isinstance(close,int) or close < handback: errors.append(cid+':authority_close_clock')
        if any(s.get('send_begin_ns',0)>=handback for s in c.get('sends',[])): errors.append(cid+':post_handback_send')
        for tr in c.get('actual_transitions',[]):
            if tr.get('nominal_offset_ns')==FRONTIER and isinstance(close,int) and tr.get('t_ns',0)<close: errors.append(cid+':boundary_before_authority_close')
    b=by.get(BASE); c=by.get(CAND)
    if b and (b.get('sends') or b.get('score',{}).get('progress_pixels')!=0): errors.append('baseline_effect')
    if c:
        if len(c.get('sends',[]))!=len(observed_clear_entries(c)): errors.append('edge_send_count')
        if c.get('score',{}).get('harm_pixels',0)!=0: errors.append('candidate_harm')
        for lo,hi in state_intervals(c,WATCH):
            if any(lo<=e.get('t_ns',0)<hi for e in c.get('effects',[])): errors.append('watch_effect')
    return {'decision':'PASS_T1_A7_BOUNDARY_CONSTRUCTION_ELIGIBLE' if not errors else 'STOP_T1_A7_BOUNDARY_CONSTRUCTION','pass':not errors,'errors':errors}

def synthetic():
    start=1_000_000_000; cases=[]
    for arm in (BASE,CAND):
        close=start+FRONTIER+100_000
        c={'case_id':arm,'arm':arm,'scenario':'TRANSIENT_28','start_ns':start,'initial_state':CLEAR,
           'authority_deadline_ns':start+FRONTIER,'authority_stop_set_ns':close,
           'actual_transitions':[{'nominal_offset_ns':o,'state':st,'t_ns':(close+100_000 if o==FRONTIER else start+o)} for o,st in PROGRAMS['TRANSIENT_28']],
           'samples':[],'sends':[],'effects':[],'score':{'progress_pixels':0,'harm_pixels':0},'terminal_f8_up':True,
           'cleanup':{'xvfb_exit':True,'tk_destroyed':True,'control_closed':True,'scorer_closed':True},'exceptions':[]}
        if arm==CAND:
            c['samples']=[{'idx':0,'state':CLEAR,'disposition':'ADVANCE','sample_end_ns':start+100_000},{'idx':1,'state':CLEAR,'disposition':'ADVANCE','sample_end_ns':start+5_100_000},{'idx':6,'state':WATCH,'disposition':'WATCH','sample_end_ns':start+30_100_000}]
            c['sends']=[{'sample_idx':0,'send_begin_ns':start+200_000,'send_end_ns':start+300_000}]
            c['effects']=[{'effect_kind':'useful','t_ns':start+800_000}];c['score']['progress_pixels']=100
        cases.append(c)
    return {'task':TASK,'phase':'construction','construction_invocations':1,'formal_invocations':0,'reruns':0,'replacements':0,'tuning':0,'scenario':'TRANSIENT_28','pairs':1,'cases':cases,'child_runs':[{'returncode':0},{'returncode':0}]}

def preflight():
    b=synthetic(); tests={'pass_baseline':evaluate(b)['pass']}
    q=copy.deepcopy(b);q['cases'][0]['actual_transitions'].pop();tests['missing_clear40']=not evaluate(q)['pass']
    q=copy.deepcopy(b);next(c for c in q['cases'] if c['arm']==CAND)['sends'][0]['send_begin_ns']=1_040_000_001;tests['post_handback_send']=not evaluate(q)['pass']
    q=copy.deepcopy(b);next(c for c in q['cases'] if c['arm']==CAND)['sends'].append({'send_begin_ns':1_010_000_000});tests['repeat_send']=not evaluate(q)['pass']
    return {'all_pass':all(tests.values()),'tests':tests}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['preflight','audit']);ap.add_argument('result',nargs='?');ap.add_argument('--out');a=ap.parse_args()
    if a.mode=='preflight':
        o=preflight();print(json.dumps(o,sort_keys=True));return 0 if o['all_pass'] else 5
    o=evaluate(json.loads(Path(a.result).read_text()));print(json.dumps(o,sort_keys=True))
    if a.out:Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
    return 0 if o['pass'] else 4
if __name__=='__main__':raise SystemExit(main())
