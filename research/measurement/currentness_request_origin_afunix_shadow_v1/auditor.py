import argparse,hashlib,json
STRATA=['INVALIDATE_BEFORE_RESPONSE','INVALIDATE_BEFORE_REQUEST','RESPONSE_BEFORE_INVALIDATE','TRANSPORT_REPLAY']
PGENS=[0,1,2,100,1000000,2147483647]

def expected(s):
    return {'INVALIDATE_BEFORE_RESPONSE':('STALE_RESPONSE_REFUSED','UNKNOWN_DECISION',None),'INVALIDATE_BEFORE_REQUEST':('DECISION_INSTALLED','ADMITTED',None),'RESPONSE_BEFORE_INVALIDATE':('DECISION_INSTALLED','STALE_EPOCH_REFUSED',None),'TRANSPORT_REPLAY':('DECISION_INSTALLED','ADMITTED','RESPONSE_REPLAY_REFUSED')}[s]

def timeline_ok(r):
    t=r['timeline']; s=r['stratum']
    try:
        if s=='INVALIDATE_BEFORE_RESPONSE': return t['begin_end']<=t['request_sent']<=t['ack_received']<=t['invalidate_thread_start']<=t['invalidate_thread_end']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['use_start']
        if s=='INVALIDATE_BEFORE_REQUEST': return t['invalidate_thread_start']<=t['invalidate_thread_end']<=t['begin_start']<=t['begin_end']<=t['request_sent']<=t['ack_received']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['use_start']
        if s=='RESPONSE_BEFORE_INVALIDATE': return t['begin_end']<=t['request_sent']<=t['ack_received']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['invalidate_thread_start']<=t['invalidate_thread_end']<=t['use_start']
        if s=='TRANSPORT_REPLAY': return t['begin_end']<=t['request_sent']<=t['ack_received']<=t['release_sent']<=t['response_received']<=t['install1_start']<=t['install1_end']<=t['replay_release_sent']<=t['replay_response_received']<=t['install2_start']<=t['install2_end']<=t['use_start']
    except KeyError: return False
    return False

def audit(result_path,trace_path):
    res=json.load(open(result_path)); raw=open(trace_path,'rb').read(); rows=[json.loads(x) for x in raw.splitlines() if x]
    errors=[]; counts={s:0 for s in STRATA}; mismatch=timeline_bad=authority=rebind=exceptions=parse_errors=0; pgens=set(); status={s:{} for s in STRATA}
    for r in rows:
        s=r['stratum']; counts[s]+=1; pgens.add(r['planner_generation']); exceptions+=r['exception'] is not None; parse_errors+=r['parse_errors']; timeline_bad+=not timeline_ok(r)
        e1,eu,e2=expected(s); g1=(r['outputs'].get('install1') or {}).get('status'); gu=(r['outputs'].get('use') or {}).get('status'); g2=(r['outputs'].get('install2') or {}).get('status')
        mismatch += (g1!=e1 or gu!=eu or (e2 is not None and g2!=e2)); rebind += (s=='TRANSPORT_REPLAY' and not r['outputs'].get('replay_decisions_equal',False))
        for v in r['outputs'].values():
            if isinstance(v,dict) and v.get('grants_input_authority') is not False: authority+=1
        k=f'{g1}|{gu}|{g2}'; status[s][k]=status[s].get(k,0)+1
    sha=hashlib.sha256(raw).hexdigest(); n=res['cases_per_stratum']; expected_summary={'total_cases':len(rows),'stratum_counts':counts,'candidate_oracle_mismatches':mismatch,'timeline_violations':timeline_bad,'exceptions':exceptions,'parse_errors':parse_errors,'response_replay_rebinds':rebind,'authority_promotions':authority,'planner_generations_seen':sorted(pgens),'status_counts':status,'trace_sha256':sha,'trace_bytes':len(raw)}
    for k,v in expected_summary.items():
        if res.get(k)!=v: errors.append(k)
    if len(rows)!=4*n or any(counts[s]!=n for s in STRATA): errors.append('case_count')
    if mismatch or timeline_bad or exceptions or parse_errors or rebind or authority: errors.append('safety_or_integrity')
    if sorted(pgens)!=PGENS: errors.append('planner_generations')
    if res.get('cleanup_residual_processes')!=0: errors.append('cleanup')
    if res.get('planner_generation_influence')!=0: errors.append('planner_generation_influence')
    if res.get('primary_invocations')!=1 or res.get('reruns')!=0: errors.append('invocation')
    if res.get('decision')!='PASS_REQUEST_ORIGIN_AFUNIX_SHADOW_SCOPED': errors.append('decision')
    return {'audit':'PASS' if not errors else 'FAIL','errors':sorted(set(errors)),'derived':expected_summary}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('trace'); ap.add_argument('--out'); a=ap.parse_args(); z=audit(a.result,a.trace); open(a.out,'w').write(json.dumps(z,indent=2,sort_keys=True)+'\n'); print(json.dumps({'audit':z['audit'],'errors':z['errors']},sort_keys=True)); raise SystemExit(0 if z['audit']=='PASS' else 1)
if __name__=='__main__': main()
