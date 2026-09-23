import argparse, copy, json
from pathlib import Path

ARMS=('STABLE','DELAYED_PAINT','STALE_FOCUS','IDENTITY_MISMATCH')

def recompute(r):
    rows=r.get('rows',[])
    m={
      'rows':len(rows),
      'candidate_oracle_mismatch':sum(x.get('candidate')!=x.get('oracle') for x in rows),
      'valid_stable_paint_joins':sum(bool(x.get('candidate')) for x in rows if x.get('arm') in ('STABLE','DELAYED_PAINT')),
      'strict_stable_paint_joins':sum(bool(x.get('strict')) for x in rows if x.get('arm') in ('STABLE','DELAYED_PAINT')),
      'candidate_stale_focus_joins':sum(bool(x.get('candidate')) for x in rows if x.get('arm')=='STALE_FOCUS'),
      'naive_stale_focus_joins':sum(bool(x.get('naive')) for x in rows if x.get('arm')=='STALE_FOCUS'),
      'candidate_identity_mismatch_joins':sum(bool(x.get('candidate')) for x in rows if x.get('arm')=='IDENTITY_MISMATCH'),
      'max_sample_span_ns':max((x.get('sample_span_ns',-1) for x in rows),default=-1),
      'stable_paint_within_2ms':sum(x.get('sample_span_ns',10**30)<=2_000_000 for x in rows if x.get('arm') in ('STABLE','DELAYED_PAINT')),
      'stale_focus_within_2ms':sum(x.get('sample_span_ns',10**30)<=2_000_000 for x in rows if x.get('arm')=='STALE_FOCUS'),
      'restored_focus_all':all(x.get('restored_focus')==x.get('raw',{}).get('initial_focus') for x in rows),
      'image_bytes_all_1024':all(x.get('raw',{}).get('image_bytes')==1024 for x in rows),
      'arm_counts':{a:sum(x.get('arm')==a for x in rows) for a in ARMS}
    }
    return m

def evaluate(r):
    errs=[]; m=recompute(r)
    if r.get('task')!='OBSERVATION-EPOCH-BOUNDED-SKEW-X11-R2-20260918-001': errs.append('task')
    if m!=r.get('metrics'): errs.append('metrics')
    if m['candidate_oracle_mismatch']!=0: errs.append('oracle')
    if m['candidate_stale_focus_joins']!=0: errs.append('stale_focus')
    if m['candidate_identity_mismatch_joins']!=0: errs.append('identity')
    if not m['restored_focus_all'] or not m['image_bytes_all_1024']: errs.append('integrity')
    if r.get('phase')=='construction':
        if r.get('formal_invocations')!=0: errs.append('construction_counter')
        if m['arm_counts']!={a:8 for a in ARMS}: errs.append('construction_shape')
        if m['valid_stable_paint_joins']<=0 or m['naive_stale_focus_joins']<=0: errs.append('construction_exposure')
    elif r.get('phase')=='formal':
        if r.get('formal_invocations')!=1 or m['arm_counts']!={a:64 for a in ARMS}: errs.append('formal_shape')
        if m['valid_stable_paint_joins']<96: errs.append('candidate_value')
        if not (m['strict_stable_paint_joins']<m['valid_stable_paint_joins']): errs.append('strict_value')
        if m['naive_stale_focus_joins']<=0: errs.append('naive_discriminator')
    else: errs.append('phase')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: errs.append('counters')
    return sorted(set(errs))

def controls(r):
    tests={}
    q=copy.deepcopy(r); q['rows'][0]['candidate']=not q['rows'][0]['candidate']; tests['candidate_flip']=bool(evaluate(q))
    sf=next(i for i,x in enumerate(r['rows']) if x['arm']=='STALE_FOCUS')
    q=copy.deepcopy(r); q['rows'][sf]['candidate']=True; tests['stale_join']=bool(evaluate(q))
    q=copy.deepcopy(r); q['rows'][0]['raw']['image_bytes']=3; tests['image_bytes']=bool(evaluate(q))
    q=copy.deepcopy(r); q['metrics']['rows']+=1; tests['metric_tamper']=bool(evaluate(q))
    return tests

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); errs=evaluate(r); cc=controls(r)
    o={'pass':not errs and all(cc.values()),'errors':errs,'corruption_controls':cc,'controls_pass':all(cc.values())}
    Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
    raise SystemExit(0 if o['pass'] else 4)
