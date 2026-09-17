import argparse,hashlib,json,time
from dataclasses import asdict
from candidate import reduce_composed,CRITICAL,CAPACITY
from oracle import reduce_oracle
from fixture import batches,NOW_NS,MAX_AGE_NS

def invariants(rows,out):
    errs=[]; by_id={r.event_id:r for r in rows}
    delivered=set(out['delivered_ids']); stale=set(out['stale_ids'])
    if delivered & stale: errs.append('stale_delivered')
    if out['grants_input_authority'] is not False: errs.append('authority')
    sessions=[]
    for r in rows:
        if r.session not in sessions: sessions.append(r.session)
    for s in sessions:
        crit=[r for r in rows if r.session==s and r.kind in CRITICAL]
        expected=[r.event_id for r in crit[:CAPACITY]]
        actual=[x for x in out['retained_critical_ids'] if by_id[x].session==s]
        if actual!=expected: errs.append('critical_prefix')
        ov=out['overflow_by_session'].get(s)
        if len(crit)>CAPACITY:
            u=crit[CAPACITY]
            want={'status':'RESYNC_REQUIRED','first_unretained_event_id':u.event_id,'first_unretained_seq':u.seq,
                  'first_unretained_kind':u.kind,'unretained_count':len(crit)-CAPACITY}
            if ov!=want: errs.append('gap')
            if out['coverage_complete_by_session'].get(s) is not False: errs.append('coverage_false')
        else:
            if ov is not None: errs.append('spurious_gap')
            if out['coverage_complete_by_session'].get(s) is not True: errs.append('coverage_true')
    scopes={}
    for eid in out['delivered_ids']:
        r=by_id[eid]
        if r.kind in CRITICAL: continue
        if NOW_NS-r.t_ns>MAX_AGE_NS: errs.append('stale_scope')
        k=(r.session,r.target,r.stream)
        if k in scopes: errs.append('scope_cardinality')
        scopes[k]=eid
    for k,eid in scopes.items():
        fresh=[r for r in rows if r.kind not in CRITICAL and (r.session,r.target,r.stream)==k and NOW_NS-r.t_ns<=MAX_AGE_NS]
        if not fresh or fresh[-1].event_id!=eid: errs.append('not_newest')
    return errs

def run(seed,count):
    h=hashlib.sha256(); summary=dict(batches=count,records=0,critical_records=0,retained_critical_records=0,
        unretained_critical_records=0,overflow_batches=0,overflow_sessions=0,candidate_oracle_mismatches=0,
        invariant_errors=0,formal_invocations=1,reruns=0)
    error_kinds={}
    for rows in batches(seed,count):
        a=reduce_composed(rows,NOW_NS,MAX_AGE_NS); b=reduce_oracle(rows,NOW_NS,MAX_AGE_NS)
        summary['records']+=len(rows)
        c=sum(r.kind in CRITICAL for r in rows); summary['critical_records']+=c
        summary['retained_critical_records']+=len(a['retained_critical_ids'])
        summary['unretained_critical_records']+=sum(x['unretained_count'] for x in a['overflow_by_session'].values())
        if a['overflow_by_session']:
            summary['overflow_batches']+=1; summary['overflow_sessions']+=len(a['overflow_by_session'])
        if a!=b: summary['candidate_oracle_mismatches']+=1
        errs=invariants(rows,a); summary['invariant_errors']+=len(errs)
        for e in errs: error_kinds[e]=error_kinds.get(e,0)+1
        h.update(json.dumps({'rows':[asdict(r) for r in rows],'out':a},sort_keys=True,separators=(',',':')).encode())
    accounted=summary['retained_critical_records']+summary['unretained_critical_records']
    summary['critical_accounting_error']=summary['critical_records']-accounted
    summary['error_kinds']=error_kinds; summary['digest']=h.hexdigest(); summary['seed']=seed
    ok=(summary['candidate_oracle_mismatches']==0 and summary['invariant_errors']==0 and summary['critical_accounting_error']==0 and summary['overflow_batches']>0)
    summary['decision']='PASS_FRESHNESS_BOUNDED_CRITICAL_COMPOSITION_SCOPED' if ok else 'FAIL_COMPOSITION_SEMANTICS'
    summary['grants_input_authority']=False
    return summary

def main():
    p=argparse.ArgumentParser(); p.add_argument('--seed',type=int,required=True); p.add_argument('--batches',type=int,required=True); p.add_argument('--out',required=True)
    a=p.parse_args(); t=time.perf_counter(); result=run(a.seed,a.batches); result['wall_s']=time.perf_counter()-t
    with open(a.out,'x') as f: json.dump(result,f,indent=2,sort_keys=True); f.write('\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
