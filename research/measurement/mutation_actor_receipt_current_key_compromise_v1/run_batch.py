from __future__ import annotations
import hashlib,json,sys,time
from core import pair_case
from oracle import verifier_accepts_current,hidden_provenance_disposition
from schedule import range_for,PAIRS_PER_BATCH,TASK
import predecessor_experiment as parent

def main(batch:int):
    start,end=range_for(batch)
    counts={'pairs':0,'legit_accept':0,'forge_accept':0,'visible_equal':0,'candidate_pair_decision_equal':0,'oracle_mac_accept_legit':0,'oracle_mac_accept_forge':0,
            'compromised_hidden_detected':0,'authority_promotions':0,'task_success_promotions':0}
    h=hashlib.sha256(); t0=time.perf_counter_ns()
    for i in range(start,end):
        q=pair_case(i)
        legit=parent.signed(i,1,nonce=f'p{i}')
        forge=dict(legit)  # byte-identical verifier-visible evidence by construction
        rl=parent.rec(i,[legit]); rf=parent.rec(i,[forge])
        ol=verifier_accepts_current(rl,legit); of=verifier_accepts_current(rf,forge)
        lp=q['legit']; fp=q['forge']
        counts['pairs']+=1
        counts['legit_accept'] += lp['state']=='SELF_CONFIRMED'
        counts['forge_accept'] += fp['state']=='SELF_CONFIRMED'
        counts['visible_equal'] += q['visible_equal']
        counts['candidate_pair_decision_equal'] += lp==fp
        counts['oracle_mac_accept_legit'] += ol; counts['oracle_mac_accept_forge'] += of
        counts['compromised_hidden_detected'] += hidden_provenance_disposition(of,'COMPROMISED_ACTOR')=='COMPROMISED_FORGE_ACCEPTED_BY_SINGLE_ROOT'
        counts['authority_promotions'] += int(lp['grants_authority'])+int(fp['grants_authority'])
        counts['task_success_promotions'] += int(lp['verifies_task_success'])+int(fp['verifies_task_success'])
        h.update(json.dumps([i,q['visible_sha256'],lp['state'],fp['state']],separators=(',',':')).encode())
    out={'task':TASK,'batch':batch,'start':start,'end':end,'elapsed_ns':time.perf_counter_ns()-t0,'digest_sha256':h.hexdigest(),**counts}
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main(int(sys.argv[1]))
