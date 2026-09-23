from __future__ import annotations
import json,sys
from schedule import BATCHES,PAIRS_PER_BATCH,TOTAL_PAIRS

def main(paths):
    rows=[json.load(open(p)) for p in paths]; errs=[]
    if len(rows)!=BATCHES: errs.append('batch_count')
    if sorted(r.get('batch') for r in rows)!=list(range(BATCHES)): errs.append('batch_ids')
    total=lambda k:sum(int(r.get(k,-10**18)) for r in rows)
    if total('pairs')!=TOTAL_PAIRS: errs.append('pairs')
    for k in ('legit_accept','forge_accept','visible_equal','candidate_pair_decision_equal','oracle_mac_accept_legit','oracle_mac_accept_forge','compromised_hidden_detected'):
        if total(k)!=TOTAL_PAIRS: errs.append(k)
    for k in ('authority_promotions','task_success_promotions'):
        if total(k)!=0: errs.append(k)
    out={'errors':errs,'pass':not errs,'totals':{k:total(k) for k in ('pairs','legit_accept','forge_accept','visible_equal','candidate_pair_decision_equal','oracle_mac_accept_legit','oracle_mac_accept_forge','compromised_hidden_detected','authority_promotions','task_success_promotions')}}
    print(json.dumps(out,sort_keys=True)); raise SystemExit(bool(errs))
if __name__=='__main__': main(sys.argv[1:])
