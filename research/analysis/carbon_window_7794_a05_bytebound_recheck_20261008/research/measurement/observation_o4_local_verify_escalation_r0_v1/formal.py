import random, json, hashlib

def candidate(current_obs,current_intent,receipt):
    if receipt is None:
        return 'ESCALATE_MISSING'
    if receipt.get('input_authority') or receipt.get('semantic_authority'):
        return 'ESCALATE_AUTHORITY_INVALID'
    if receipt.get('obs') != current_obs:
        return 'ESCALATE_STALE_OBSERVATION'
    if receipt.get('intent') != current_intent:
        return 'ESCALATE_INTENT_MISMATCH'
    v=receipt.get('verdict')
    if v=='TRUE': return 'LOCAL_TRUE'
    if v=='FALSE': return 'LOCAL_FALSE'
    return 'ESCALATE_UNKNOWN'

def oracle(obs,intent,r):
    admissible = (
        isinstance(r,dict) and
        r.get('input_authority') is False and r.get('semantic_authority') is False and
        r.get('obs')==obs and r.get('intent')==intent and
        r.get('verdict') in ('TRUE','FALSE')
    )
    if admissible:
        return 'LOCAL_'+r['verdict']
    if not isinstance(r,dict): return 'ESCALATE_MISSING'
    if r.get('input_authority') or r.get('semantic_authority'): return 'ESCALATE_AUTHORITY_INVALID'
    if r.get('obs')!=obs: return 'ESCALATE_STALE_OBSERVATION'
    if r.get('intent')!=intent: return 'ESCALATE_INTENT_MISMATCH'
    return 'ESCALATE_UNKNOWN'

def naive(obs,intent,r):
    if isinstance(r,dict) and r.get('verdict') in ('TRUE','FALSE'):
        return 'LOCAL_'+r['verdict']
    return 'ESCALATE'

def run(seed=164720260918001,n=250000):
    rnd=random.Random(seed)
    cats={k:0 for k in ['CURRENT_TRUE','CURRENT_FALSE','UNKNOWN','STALE','INTENT_MISMATCH','MISSING','AUTHORITY_FORGED']}
    mismatch=0; unsafe_naive=0; local=0; escalated=0
    h=hashlib.sha256()
    for i in range(n):
        obs=rnd.randrange(1,5000); intent=rnd.randrange(1,1000)
        k=rnd.randrange(7)
        if k==0:
            cat='CURRENT_TRUE'; r={'obs':obs,'intent':intent,'verdict':'TRUE','input_authority':False,'semantic_authority':False}
        elif k==1:
            cat='CURRENT_FALSE'; r={'obs':obs,'intent':intent,'verdict':'FALSE','input_authority':False,'semantic_authority':False}
        elif k==2:
            cat='UNKNOWN'; r={'obs':obs,'intent':intent,'verdict':'UNKNOWN','input_authority':False,'semantic_authority':False}
        elif k==3:
            cat='STALE'; r={'obs':obs-1,'intent':intent,'verdict':rnd.choice(['TRUE','FALSE']),'input_authority':False,'semantic_authority':False}
        elif k==4:
            cat='INTENT_MISMATCH'; r={'obs':obs,'intent':intent+1,'verdict':rnd.choice(['TRUE','FALSE']),'input_authority':False,'semantic_authority':False}
        elif k==5:
            cat='MISSING'; r=None
        else:
            cat='AUTHORITY_FORGED'; r={'obs':obs,'intent':intent,'verdict':rnd.choice(['TRUE','FALSE']),'input_authority':bool(rnd.getrandbits(1)),'semantic_authority':True}
        cats[cat]+=1
        a=candidate(obs,intent,r); b=oracle(obs,intent,r)
        if a!=b: mismatch+=1
        if a.startswith('LOCAL_'): local+=1
        else: escalated+=1
        nv=naive(obs,intent,r)
        if cat in ('STALE','INTENT_MISMATCH','AUTHORITY_FORGED') and nv.startswith('LOCAL_'):
            unsafe_naive+=1
        h.update(json.dumps([i,cat,obs,intent,r,a],sort_keys=True,separators=(',',':')).encode())
    return {'seed':seed,'rows':n,'candidate_oracle_mismatch':mismatch,'categories':cats,'local_resolutions':local,'escalations':escalated,'unsafe_naive_suppressions':unsafe_naive,'digest':h.hexdigest()}

if __name__=='__main__':
    directed=[]
    base={'obs':7,'intent':3,'input_authority':False,'semantic_authority':False}
    for name,r in [
        ('true',{**base,'verdict':'TRUE'}),('false',{**base,'verdict':'FALSE'}),('unknown',{**base,'verdict':'UNKNOWN'}),
        ('stale',{**base,'obs':6,'verdict':'TRUE'}),('intent',{**base,'intent':4,'verdict':'FALSE'}),
        ('missing',None),('forged',{**base,'verdict':'TRUE','semantic_authority':True})]:
        directed.append([name,candidate(7,3,r),oracle(7,3,r)])
    result=run()
    result['directed']=directed
    result['formal_invocations']=1
    result['reruns']=0; result['replacements']=0; result['tuning']=0
    result['decision']='PASS_O4_LOCAL_VERIFY_ESCALATION_CONTRACT_SCOPED' if result['candidate_oracle_mismatch']==0 and result['unsafe_naive_suppressions']>0 and all(a==b for _,a,b in directed) else 'FAIL'
    print(json.dumps(result,indent=2,sort_keys=True))
