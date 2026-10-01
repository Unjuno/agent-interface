import json,sys
from collections import Counter
import experiment as e

def run_batch(start,count):
    cused=set(); oused=set(); mismatch=forge=auth=task=0; states=Counter(); kinds=Counter(); replay_attempts=replay_admit=0
    end=start+count
    for i in range(start,end):
        k=e.FORMAL_KINDS[i%len(e.FORMAL_KINDS)]
        r=e.make_record(i,k)
        a,cused=e.classify_candidate(r,cused)
        b,oused=e.classify_oracle(r,oused)
        mismatch+=a!=b; states[a['state']]+=1; kinds[k]+=1
        auth+=int(a['grants_authority']); task+=int(a['verifies_task_success'])
        if k not in ('valid_self','external','no_mutation') and a['state']=='SELF_CONFIRMED': forge+=1
        if k=='valid_self' and i%4==0:
            replay_attempts+=1
            ar,cused=e.classify_candidate(r,cused)
            br,oused=e.classify_oracle(r,oused)
            mismatch+=ar!=br
            replay_admit+=int(ar['state']=='SELF_CONFIRMED')
            states[ar['state']]+=1
    return {'start':start,'count':count,'end':end,'mismatches':mismatch,'forged_self_admissions':forge,'replay_attempts':replay_attempts,'replay_self_admissions':replay_admit,'authority_promotions':auth,'task_success_promotions':task,'states':dict(states),'kinds':dict(kinds)}

if __name__=='__main__':
    print(json.dumps(run_batch(int(sys.argv[1]),int(sys.argv[2])),sort_keys=True))
