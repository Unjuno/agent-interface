import argparse,hashlib,json,sqlite3
from checkpoint import restore_row
from fixture import FINAL

def verify(result_path,db_path):
    r=json.load(open(result_path));err=[]
    if r.get('formal_invocations')!=1:err.append('formal_invocations')
    if r.get('reruns')!=0:err.append('reruns')
    if r.get('decision')!='PASS_EPOCH_CHECKPOINT_RESTART_SCOPED':err.append('decision')
    c=sqlite3.connect(db_path);rows=c.execute('SELECT case_id,schema,payload,sha256,expected_view,current_only FROM checkpoints ORDER BY case_id').fetchall();c.close()
    h=hashlib.sha256();exact=0;disc=0;authority=0
    for row in rows:
        cid,m,expected,current=restore_row(row);got=m.view(FINAL);exact+=got==expected
        a=expected['A'];disc+=(a['epoch']!=1 or bool(a['historical_gaps']) or a['active_overflow'] is not None)
        authority+=any(v['grants_input_authority'] is not False for v in got.values())
        h.update(json.dumps({'id':cid,'view':got},sort_keys=True,separators=(',',':')).encode())
    if len(rows)!=r.get('cases'):err.append('rows')
    if exact!=r.get('exact_restore'):err.append('exact_restore')
    if disc!=r.get('current_only_discriminators'):err.append('current_only_discriminators')
    if authority!=r.get('authority_errors'):err.append('authority_errors')
    if h.hexdigest()!=r.get('digest'):err.append('digest')
    return err

def main():
    p=argparse.ArgumentParser();p.add_argument('--result',required=True);p.add_argument('--db',required=True);a=p.parse_args();e=verify(a.result,a.db);print(json.dumps({'audit':'PASS' if not e else 'FAIL','errors':e},sort_keys=True));raise SystemExit(0 if not e else 1)
if __name__=='__main__':main()
