import argparse, copy, json
from pathlib import Path
ARMS=('STABLE','PAINT_ONLY','FOCUS_ABA','FOCUS_CHANGE','IDENTITY_MISMATCH')
SKEW_NS=2_000_000

def recompute(r):
    rows=r.get('rows',[])
    return {
      'rows':len(rows),
      'generation_oracle_mismatch':sum(x.get('generation_witnessed')!=x.get('oracle') for x in rows),
      'equality_focus_aba_joins':sum(bool(x.get('equality_revalidation')) for x in rows if x.get('arm')=='FOCUS_ABA'),
      'generation_focus_aba_joins':sum(bool(x.get('generation_witnessed')) for x in rows if x.get('arm')=='FOCUS_ABA'),
      'generation_focus_change_joins':sum(bool(x.get('generation_witnessed')) for x in rows if x.get('arm')=='FOCUS_CHANGE'),
      'generation_identity_mismatch_joins':sum(bool(x.get('generation_witnessed')) for x in rows if x.get('arm')=='IDENTITY_MISMATCH'),
      'generation_stable_paint_joins':sum(bool(x.get('generation_witnessed')) for x in rows if x.get('arm') in ('STABLE','PAINT_ONLY')),
      'equality_stable_paint_joins':sum(bool(x.get('equality_revalidation')) for x in rows if x.get('arm') in ('STABLE','PAINT_ONLY')),
      'aba_rows_with_focus_events':sum(bool(x.get('raw',{}).get('focus_events')) for x in rows if x.get('arm')=='FOCUS_ABA'),
      'change_rows_with_focus_events':sum(bool(x.get('raw',{}).get('focus_events')) for x in rows if x.get('arm')=='FOCUS_CHANGE'),
      'stable_paint_rows_with_focus_events':sum(bool(x.get('raw',{}).get('focus_events')) for x in rows if x.get('arm') in ('STABLE','PAINT_ONLY')),
      'noncritical_within_2ms':sum(x.get('noncritical_age_ns',10**30)<=SKEW_NS for x in rows),
      'image_bytes_all_1024':all(x.get('raw',{}).get('image_bytes')==1024 for x in rows),
      'restored_focus_all':all(x.get('restored_focus')==x.get('raw',{}).get('initial_focus') for x in rows),
      'arm_counts':{a:sum(x.get('arm')==a for x in rows) for a in ARMS},
      'terminal_focus':r.get('metrics',{}).get('terminal_focus')
    }

def evaluate(r):
    errs=[]; m=recompute(r)
    if r.get('task')!='OBSERVATION-EPOCH-XTERM-FOCUS-ABA-A2-20260918-002': errs.append('task')
    if m!=r.get('metrics'): errs.append('metrics')
    if m['generation_oracle_mismatch']!=0: errs.append('oracle')
    if m['generation_focus_aba_joins']!=0: errs.append('aba_leak')
    if m['generation_focus_change_joins']!=0: errs.append('focus_change')
    if m['generation_identity_mismatch_joins']!=0: errs.append('identity')
    if m['equality_focus_aba_joins']<=0: errs.append('no_equality_discriminator')
    if m['aba_rows_with_focus_events']!=m['arm_counts']['FOCUS_ABA']: errs.append('aba_witness')
    if m['change_rows_with_focus_events']!=m['arm_counts']['FOCUS_CHANGE']: errs.append('change_witness')
    if m['stable_paint_rows_with_focus_events']!=0: errs.append('stable_contamination')
    if not m['image_bytes_all_1024'] or not m['restored_focus_all']: errs.append('integrity')
    if r.get('phase')=='construction':
        if r.get('formal_invocations')!=0 or m['arm_counts']!={a:8 for a in ARMS}: errs.append('construction_shape')
        if m['generation_stable_paint_joins']<=0: errs.append('construction_value')
    elif r.get('phase')=='formal':
        if r.get('formal_invocations')!=1 or m['arm_counts']!={a:64 for a in ARMS}: errs.append('formal_shape')
        if m['generation_stable_paint_joins']<96: errs.append('formal_value')
    else: errs.append('phase')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errs.append('counters')
    return sorted(set(errs))

def controls(r):
    tests={}
    q=copy.deepcopy(r); q['rows'][0]['generation_witnessed']=not q['rows'][0]['generation_witnessed']; tests['candidate_flip']=bool(evaluate(q))
    aba=next(i for i,x in enumerate(r['rows']) if x['arm']=='FOCUS_ABA')
    q=copy.deepcopy(r); q['rows'][aba]['generation_witnessed']=True; tests['aba_escape']=bool(evaluate(q))
    q=copy.deepcopy(r); q['rows'][aba]['raw']['focus_events']=[]; tests['witness_drop']=bool(evaluate(q))
    q=copy.deepcopy(r); q['metrics']['rows']+=1; tests['metric_tamper']=bool(evaluate(q))
    return tests

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args(); r=json.loads(Path(a.result).read_text())
    errs=evaluate(r); cc=controls(r); o={'pass':not errs and all(cc.values()),'errors':errs,'corruption_controls':cc,'controls_pass':all(cc.values())}
    Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True)); raise SystemExit(0 if o['pass'] else 4)
