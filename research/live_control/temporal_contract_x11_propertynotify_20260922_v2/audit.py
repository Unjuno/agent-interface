from __future__ import annotations
import argparse,copy,json
from pathlib import Path
from monitor import SATISFIED,EXPIRED

TASK='TEMPORAL-CONTRACT-X11-PROPERTYNOTIFY-R1-20260918-001'
EXPECTED={'POSITIVE':SATISFIED,'EXPIRE':EXPIRED,'NO_RESTART':EXPIRED}

def oracle(events,delta=80):
    anchor=None;last=None
    for row in events:
        t=row['server_time_ms'];lab=row['label']
        if last is not None and t<last:return 'UNKNOWN'
        if anchor is not None and t>anchor+delta:return EXPIRED
        if anchor is None and lab=='A':anchor=t
        if anchor is not None and lab=='B' and anchor<=t<=anchor+delta:return SATISFIED
        last=t
    return 'PENDING'

def evaluate(r):
    errs=[];term={k:0 for k in EXPECTED};expected_rows=3 if r.get('phase')=='construction' else 12
    if r.get('task')!=TASK:errs.append('task')
    if len(r.get('rows',[]))!=expected_rows:errs.append('row_count')
    if r.get('phase')=='formal' and r.get('formal_invocations')!=1:errs.append('formal_count')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0:errs.append('rerun_contract')
    for row in r.get('rows',[]):
        cid=row.get('case_id','?');s=row.get('scenario');ev=row.get('events',[])
        if s not in EXPECTED:errs.append(cid+':scenario');continue
        if not row.get('event_count_ok'):errs.append(cid+':event_count')
        if not row.get('labels_exact'):errs.append(cid+':labels')
        if not row.get('server_times_nondecreasing'):errs.append(cid+':time_order')
        if row.get('task_input_events')!=0:errs.append(cid+':task_input')
        o=oracle(ev,row.get('delta_ms',80))
        if row.get('oracle_terminal')!=o:errs.append(cid+':oracle_binding')
        if row.get('candidate_terminal')!=o:errs.append(cid+':candidate_oracle')
        if row.get('candidate_terminal')!=EXPECTED[s]:errs.append(cid+':terminal')
        if len({e.get('seq_index') for e in ev})!=len(ev):errs.append(cid+':duplicate_seq')
        term[s]+=row.get('candidate_terminal')==EXPECTED[s]
    if r.get('phase')=='formal':
        for s in EXPECTED:
            if term[s]!=4:errs.append(s+':count')
    decision=('PASS_CONSTRUCTION_ELIGIBLE' if r.get('phase')=='construction' else 'PASS_TEMPORAL_CONTRACT_X11_PROPERTYNOTIFY_SCOPED') if not errs else 'FAIL_MEASUREMENT_INTEGRITY'
    return {'decision':decision,'pass':not errs,'errors':sorted(set(errs)),'terminal_counts':term,'rows':len(r.get('rows',[]))}

def controls(r):
    c={}
    if not r.get('rows'):return {'row_present':False}
    q=copy.deepcopy(r);q['rows'][0]['events'][0]['label']='B';c['wrong_atom_label']=not evaluate(q)['pass']
    q=copy.deepcopy(r);q['rows'][0]['events'].append(copy.deepcopy(q['rows'][0]['events'][-1]));c['duplicate_event']=not evaluate(q)['pass']
    q=copy.deepcopy(r);q['rows'][0]['server_times_nondecreasing']=False;c['time_regression']=not evaluate(q)['pass']
    q=copy.deepcopy(r);q['rows'][0]['candidate_terminal']='PENDING';c['wrong_terminal']=not evaluate(q)['pass']
    q=copy.deepcopy(r);q['rows'][0]['task_input_events']=1;c['task_input']=not evaluate(q)['pass']
    return c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());z=evaluate(r);z['corruption_controls']=controls(r);z['controls_pass']=all(z['corruption_controls'].values());z['pass']=z['pass'] and z['controls_pass']
    if not z['pass'] and z['decision'].startswith('PASS_'):z['decision']='FAIL_INTEGRITY'
    Path(a.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['pass'] else 1)
if __name__=='__main__':main()
