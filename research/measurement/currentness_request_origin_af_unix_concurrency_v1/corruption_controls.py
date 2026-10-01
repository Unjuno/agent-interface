import argparse, copy, json
from auditor import validate_summary

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--audit',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.load(open(a.result)); au=json.load(open(a.audit))
    muts=[
      ('cases',lambda x:x.__setitem__('cases_completed',x['cases_completed']-1)),
      ('peer_pid_count',lambda x:x.__setitem__('peer_client_pid_count',3)),
      ('stale_install',lambda x:x.__setitem__('stale_response_installs',1)),
      ('stale_admit',lambda x:x.__setitem__('stale_old_epoch_admissions',1)),
      ('race',lambda x:x.__setitem__('race_order_wrong',1)),
      ('authority',lambda x:x.__setitem__('authority_promotions',1)),
      ('ledger',lambda x:x.__setitem__('ledger_sha256','0'*64)),
      ('invocation',lambda x:x.__setitem__('primary_invocations',2)),
      ('exceptions',lambda x:x.__setitem__('server_client_exceptions',1)),
    ]
    rows=[]
    for name,fn in muts:
        z=copy.deepcopy(r); fn(z); rows.append({'name':name,'rejected':bool(validate_summary(z,au))})
    out={'controls':rows,'rejected':sum(x['rejected'] for x in rows),'total':len(rows)}
    open(a.out,'w').write(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['rejected']==out['total'] else 2)
if __name__=='__main__': main()
