import argparse,hashlib,json
from dataclasses import asdict
from candidate import Manager,Snapshot
from oracle import reconstruct
from fixture import scenarios,PRE_NOW,RESYNC_NOW,FINAL_NOW

def recompute(seed,count):
    h=hashlib.sha256(); x={'records':0,'pre_overflows':0,'post_overflows':0,'candidate_oracle_mismatches':0,'invariant_errors':0,'historical_gap_mutations':0,'cross_session_errors':0}
    for sc in scenarios(seed,count):
        m=Manager()
        for session in ('A','B'):
            for r in sc['pre'][session]:m.append(r,PRE_NOW);x['records']+=1
        a=m.get('A');oid=a.overflow_identity()
        if oid is None:x['invariant_errors']+=1;continue
        x['pre_overflows']+=1;snap=Snapshot(sc['case_id']+'-snap',sc['snapshot_seq'],RESYNC_NOW,'A','T0','X',oid)
        if m.resync('A',snap,RESYNC_NOW)!='RESYNC_ACCEPTED':x['invariant_errors']+=1
        hist=json.loads(json.dumps(a.historical_gaps))
        for session in ('A','B'):
            for r in sc['post'][session]:m.append(r,FINAL_NOW);x['records']+=1
        got=m.view(FINAL_NOW);exp=reconstruct(sc['pre'],snap,sc['post'],FINAL_NOW)
        if got!=exp:x['candidate_oracle_mismatches']+=1
        if got['A']['historical_gaps']!=hist:x['historical_gap_mutations']+=1
        if got['A']['active_overflow'] is not None:x['post_overflows']+=1
        if got['B']['epoch']!=1 or got['B']['historical_gaps']:x['cross_session_errors']+=1
        h.update(json.dumps({'case':sc['case_id'],'snapshot':asdict(snap),'view':got},sort_keys=True,separators=(',',':')).encode())
    x['digest']=h.hexdigest();return x

def verify(path):
    r=json.load(open(path));err=[]
    if r.get('formal_invocations')!=1:err.append('formal_invocations')
    if r.get('reruns')!=0:err.append('reruns')
    if r.get('decision')!='PASS_FRESHNESS_EPOCH_RESYNC_COMPOSITION_SCOPED':err.append('decision')
    if r.get('grants_input_authority') is not False:err.append('authority')
    x=recompute(r.get('seed'),r.get('scenarios'))
    for k in ('records','pre_overflows','post_overflows','candidate_oracle_mismatches','invariant_errors','historical_gap_mutations','cross_session_errors','digest'):
        if r.get(k)!=x[k]:err.append(k)
    return err

def main():
    p=argparse.ArgumentParser();p.add_argument('--result',required=True);a=p.parse_args();e=verify(a.result);print(json.dumps({'audit':'PASS' if not e else 'FAIL','errors':e},sort_keys=True));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
