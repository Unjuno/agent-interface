import argparse,hashlib,json
from dataclasses import asdict
from candidate import reduce_composed,CRITICAL,CAPACITY
from oracle import reduce_oracle
from fixture import batches,NOW_NS,MAX_AGE_NS

def recompute(seed,count):
    h=hashlib.sha256(); s={'records':0,'critical_records':0,'retained_critical_records':0,'unretained_critical_records':0,
       'overflow_batches':0,'overflow_sessions':0,'candidate_oracle_mismatches':0,'invariant_errors':0}
    for rows in batches(seed,count):
        a=reduce_composed(rows,NOW_NS,MAX_AGE_NS); o=reduce_oracle(rows,NOW_NS,MAX_AGE_NS)
        if a!=o: s['candidate_oracle_mismatches']+=1
        s['records']+=len(rows); s['critical_records']+=sum(r.kind in CRITICAL for r in rows)
        s['retained_critical_records']+=len(a['retained_critical_ids']); s['unretained_critical_records']+=sum(v['unretained_count'] for v in a['overflow_by_session'].values())
        if a['overflow_by_session']: s['overflow_batches']+=1; s['overflow_sessions']+=len(a['overflow_by_session'])
        by_id={r.event_id:r for r in rows}
        if set(a['delivered_ids']) & set(a['stale_ids']): s['invariant_errors']+=1
        if a['grants_input_authority'] is not False: s['invariant_errors']+=1
        sessions={r.session for r in rows}
        for session in sessions:
            crit=[r for r in rows if r.session==session and r.kind in CRITICAL]
            got=[x for x in a['retained_critical_ids'] if by_id[x].session==session]
            if got != [r.event_id for r in crit[:CAPACITY]]: s['invariant_errors']+=1
            ov=a['overflow_by_session'].get(session)
            if len(crit)>CAPACITY:
                u=crit[CAPACITY]
                if ov != {'status':'RESYNC_REQUIRED','first_unretained_event_id':u.event_id,'first_unretained_seq':u.seq,'first_unretained_kind':u.kind,'unretained_count':len(crit)-CAPACITY}: s['invariant_errors']+=1
            elif ov is not None: s['invariant_errors']+=1
        seen={}
        for eid in a['delivered_ids']:
            r=by_id[eid]
            if r.kind in CRITICAL: continue
            k=(r.session,r.target,r.stream)
            if NOW_NS-r.t_ns>MAX_AGE_NS or k in seen: s['invariant_errors']+=1
            seen[k]=eid
        for k,eid in seen.items():
            possible=[r.event_id for r in rows if r.kind not in CRITICAL and (r.session,r.target,r.stream)==k and NOW_NS-r.t_ns<=MAX_AGE_NS]
            if not possible or possible[-1]!=eid: s['invariant_errors']+=1
        h.update(json.dumps({'rows':[asdict(r) for r in rows],'out':a},sort_keys=True,separators=(',',':')).encode())
    s['digest']=h.hexdigest(); return s

def verify(path):
    with open(path) as f: r=json.load(f)
    errors=[]
    if r.get('formal_invocations')!=1: errors.append('formal_invocations')
    if r.get('reruns')!=0: errors.append('reruns')
    if r.get('decision')!='PASS_FRESHNESS_BOUNDED_CRITICAL_COMPOSITION_SCOPED': errors.append('decision')
    if r.get('grants_input_authority') is not False: errors.append('authority')
    x=recompute(r.get('seed'),r.get('batches'))
    for k in ('records','critical_records','retained_critical_records','unretained_critical_records','overflow_batches','overflow_sessions','candidate_oracle_mismatches','invariant_errors','digest'):
        if r.get(k)!=x[k]: errors.append(k)
    if r.get('critical_accounting_error')!=0: errors.append('critical_accounting_error')
    return errors

def main():
    p=argparse.ArgumentParser(); p.add_argument('--result',required=True); a=p.parse_args(); errors=verify(a.result)
    print(json.dumps({'audit':'PASS' if not errors else 'FAIL','errors':errors},sort_keys=True))
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
