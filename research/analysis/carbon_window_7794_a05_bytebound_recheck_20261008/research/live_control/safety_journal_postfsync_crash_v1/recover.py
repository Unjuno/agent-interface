import argparse, json
from model import digest, publish, read_journal
ap=argparse.ArgumentParser(); ap.add_argument('--journal'); ap.add_argument('--ledger'); ap.add_argument('--mutate',action='store_true'); a=ap.parse_args()
rows=read_journal(a.journal); out=[]
for r in rows:
    if a.mutate:
        r=dict(r); r['owner_instance']=r['owner_instance']+'-forged'
    out.append({'receipt_id':r['receipt_id'],'disposition':publish(a.ledger,r)})
print(json.dumps(out,sort_keys=True))
