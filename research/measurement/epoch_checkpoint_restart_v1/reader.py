import argparse,hashlib,json,sqlite3
from checkpoint import restore_row
from parent_candidate import Snapshot,Record
from fixture import FINAL

def current_only_loses(expected,current):
    # Negative representation deliberately retains only current visible state + sequence.
    a=expected['A']; ca=current['sessions']['A']
    hidden_absent=all(k not in ca for k in ('epoch','historical_gaps','active_overflow','retained_critical_ids','accepted_resync'))
    return hidden_absent and a['epoch']==2 and bool(a['historical_gaps'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--out',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--cases',type=int,required=True);a=p.parse_args()
    c=sqlite3.connect(a.db); rows=c.execute('SELECT case_id,schema,payload,sha256,expected_view,current_only FROM checkpoints ORDER BY case_id').fetchall(); c.close()
    s={'cases':a.cases,'rows':len(rows),'exact_restore':0,'restore_mismatches':0,'current_only_discriminators':0,'replay_checks':0,'replay_failures':0,'future_append_checks':0,'future_append_failures':0,'authority_errors':0,'formal_invocations':1,'reruns':0}
    h=hashlib.sha256()
    for idx,row in enumerate(rows):
        cid,m,expected,current_only=restore_row(row); got=m.view(FINAL)
        if got==expected:s['exact_restore']+=1
        else:s['restore_mismatches']+=1
        if current_only_loses(expected,current_only):s['current_only_discriminators']+=1
        if any(v['grants_input_authority'] is not False for v in got.values()):s['authority_errors']+=1
        if idx<256:
            st=m.get('A'); ar=st.accepted_resync; before=st.view(FINAL)
            snap=Snapshot(ar[0],ar[1],ar[2],ar[3],ar[4],ar[5],ar[6]); s['replay_checks']+=1
            if m.resync('A',snap,FINAL)!='ALREADY_RESYNCED_SELF' or st.view(FINAL)!=before:s['replay_failures']+=1
        if 256<=idx<512:
            st=m.get('A'); seq=st.latest_seq+1; s['future_append_checks']+=1
            try:
                m.append(Record(cid+'-future',seq,FINAL,'A','T0','X','STATUS'),FINAL)
                if st.latest_seq!=seq:raise AssertionError('seq')
                try:m.append(Record(cid+'-stale',seq,FINAL,'A','T0','X','STATUS'),FINAL)
                except ValueError:pass
                else:raise AssertionError('stale accepted')
            except Exception:s['future_append_failures']+=1
        h.update(json.dumps({'id':cid,'view':got},sort_keys=True,separators=(',',':')).encode())
    s['digest']=h.hexdigest();s['seed']=a.seed
    ok=(len(rows)==a.cases and s['exact_restore']==a.cases and s['restore_mismatches']==0 and s['current_only_discriminators']==a.cases and s['replay_failures']==0 and s['future_append_failures']==0 and s['authority_errors']==0)
    s['decision']='PASS_EPOCH_CHECKPOINT_RESTART_SCOPED' if ok else 'FAIL_RESTART_STATE'
    with open(a.out,'x') as f:json.dump(s,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(s,sort_keys=True))
if __name__=='__main__':main()
