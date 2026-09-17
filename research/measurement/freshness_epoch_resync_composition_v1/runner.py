import argparse,hashlib,json,time
from dataclasses import asdict
from candidate import Manager,Snapshot,CRITICAL,CAPACITY
from oracle import reconstruct
from fixture import scenarios,PRE_NOW,RESYNC_NOW,FINAL_NOW

def run(seed,count):
    h=hashlib.sha256(); s={'scenarios':count,'candidate_oracle_mismatches':0,'invariant_errors':0,'pre_overflows':0,
        'post_overflows':0,'historical_gap_mutations':0,'cross_session_errors':0,'formal_invocations':1,'reruns':0,'records':0}
    for sc in scenarios(seed,count):
        m=Manager()
        for session in ('A','B'):
            for r in sc['pre'][session]:m.append(r,PRE_NOW); s['records']+=1
        a=m.get('A'); oid=a.overflow_identity()
        if oid is None: raise AssertionError('fixture must overflow A')
        s['pre_overflows']+=1
        snap=Snapshot(sc['case_id']+'-snap',sc['snapshot_seq'],RESYNC_NOW,'A','T0','X',oid)
        status=m.resync('A',snap,RESYNC_NOW)
        if status!='RESYNC_ACCEPTED': s['invariant_errors']+=1
        gap_before=[dict(x) for x in a.historical_gaps]
        for session in ('A','B'):
            for r in sc['post'][session]:m.append(r,FINAL_NOW); s['records']+=1
        got=m.view(FINAL_NOW)
        expected=reconstruct(sc['pre'],snap,sc['post'],FINAL_NOW)
        if got!=expected:s['candidate_oracle_mismatches']+=1
        av=got['A']; bv=got['B']
        if av['epoch']!=2 or len(av['historical_gaps'])!=1 or av['grants_input_authority'] is not False:s['invariant_errors']+=1
        if av['historical_gaps']!=gap_before:s['historical_gap_mutations']+=1
        if bv['epoch']!=1 or bv['historical_gaps'] or bv['grants_input_authority'] is not False:s['cross_session_errors']+=1
        if av['active_overflow'] is not None:s['post_overflows']+=1
        h.update(json.dumps({'case':sc['case_id'],'snapshot':asdict(snap),'view':got},sort_keys=True,separators=(',',':')).encode())
    s['digest']=h.hexdigest(); s['seed']=seed
    ok=all(s[k]==0 for k in ('candidate_oracle_mismatches','invariant_errors','historical_gap_mutations','cross_session_errors')) and s['pre_overflows']==count and s['post_overflows']>0
    s['decision']='PASS_FRESHNESS_EPOCH_RESYNC_COMPOSITION_SCOPED' if ok else 'FAIL_RESYNC_COMPOSITION'
    s['grants_input_authority']=False
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--scenarios',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args()
    t=time.perf_counter(); r=run(a.seed,a.scenarios);r['wall_s']=time.perf_counter()-t
    with open(a.out,'x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
