import json,tempfile,subprocess,sys
from pathlib import Path

GOOD={
 'task':'MUTATION-ACTOR-RECEIPT-CURRENT-KEY-COMPROMISE-20260918-001','batch':0,'start':10000000,'end':10050000,'pairs':50000,
 'legit_accept':50000,'forge_accept':50000,'visible_equal':50000,'candidate_pair_decision_equal':50000,
 'oracle_mac_accept_legit':50000,'oracle_mac_accept_forge':50000,'compromised_hidden_detected':50000,
 'authority_promotions':0,'task_success_promotions':0,'digest_sha256':'x','elapsed_ns':1}

def run(rows):
    with tempfile.TemporaryDirectory() as td:
        ps=[]
        for i,r in enumerate(rows):
            rr=dict(r);rr['batch']=i;rr['start']=10000000+i*50000;rr['end']=rr['start']+50000
            p=Path(td)/f'b{i}.json';p.write_text(json.dumps(rr));ps.append(str(p))
        return subprocess.run([sys.executable,'audit.py',*ps],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode

def main():
    base=[dict(GOOD) for _ in range(4)]
    controls=[]
    for name,field,val in [
        ('forge_rejected','forge_accept',49999),
        ('visible_diverged','visible_equal',49999),
        ('authority','authority_promotions',1),
        ('hidden_not_detected','compromised_hidden_detected',49999),
        ('wrong_batch_count','pairs',49999),
    ]:
        rows=[dict(x) for x in base]; rows[2][field]=val
        controls.append({'name':name,'rejected':run(rows)!=0})
    out={'controls':controls,'all_rejected':all(x['rejected'] for x in controls)}
    print(json.dumps(out,sort_keys=True)); raise SystemExit(not out['all_rejected'])
if __name__=='__main__':main()
