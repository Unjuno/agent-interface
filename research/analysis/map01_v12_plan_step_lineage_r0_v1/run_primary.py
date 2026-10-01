from __future__ import annotations
import copy,hashlib,itertools,json,random,time
from pathlib import Path
import candidate,oracle
ROOT=Path(__file__).resolve().parent
SEED=190720260919001
N_RANDOM=100_000

def make(n=2):
    rows=[];pairs={}
    for i,key in enumerate(['a','d'][:n]):
        rs=1000+i*100; up=(rs+20,rs+30)
        rows.append(dict(event='input_release_transition',operation='up',transition_schema='input-release-transition-v3',
            key=key,owner_id='owner-A',intent_token='intent-A',ordinary_release_candidate=True,
            release_batch_schema='input-release-batch-v3',release_batch_size=n,release_batch_position=i,
            release_batch_identifier='program-A',release_batch_step=7,owner_transition_verified=True,
            physical_verification_authoritative=False,grants_input_authority=False,
            release_call_started_ns=rs,release_call_returned_ns=rs+50))
        aid=f'act-{i}'
        pairs[key]=[
          dict(edge='down',status='CONFIRMED_PHYSICAL_DOWN',actuation_id=aid,owner_id='owner-A',intent_token='intent-A',key=key,interval=(100+i*100,110+i*100)),
          dict(edge='up',status='CONFIRMED_PHYSICAL_UP',actuation_id=aid,owner_id='owner-A',intent_token='intent-A',key=key,interval=up)]
    return rows,pairs,copy.deepcopy(candidate.EXPECTED_SOURCE)

def accepted(x): return x.get('status')=='BOUND_MAP01_PHYSICAL_BATCH'
def mutate_case(name):
    r,p,s=make(2)
    if name=='valid_one':return make(1),True
    if name=='valid_two':return (r,p,s),True
    if name=='v3_only': p={}; return (r,p,s),False
    if name=='nonordinary':r[0]['ordinary_release_candidate']=False
    elif name=='duplicate_position':r[1]['release_batch_position']=0
    elif name=='duplicate_actuation':p['d'][0]['actuation_id']=p['a'][0]['actuation_id'];p['d'][1]['actuation_id']=p['a'][1]['actuation_id']
    elif name=='identifier_mismatch':r[1]['release_batch_identifier']='program-B'
    elif name=='step_mismatch':r[1]['release_batch_step']=8
    elif name=='owner_mismatch':p['a'][0]['owner_id']='owner-B';p['a'][1]['owner_id']='owner-B'
    elif name=='intent_mismatch':p['a'][0]['intent_token']='intent-B';p['a'][1]['intent_token']='intent-B'
    elif name=='key_mismatch':p['a'][0]['key']='x';p['a'][1]['key']='x'
    elif name=='missing_actuation':p['a'][0]['actuation_id']='';p['a'][1]['actuation_id']=''
    elif name=='unconfirmed_down':p['a'][0]['status']='PRESS_UNCONFIRMED';p['a'][0]['interval']=None
    elif name=='unconfirmed_up':p['a'][1]['status']='RELEASE_UNCONFIRMED';p['a'][1]['interval']=None
    elif name=='inverted_edges':p['a'][1]['interval']=(105,108)
    elif name=='up_outside_rpc':p['a'][1]['interval']=(999,1001)
    elif name=='source_drift':s['input_owner_v12_sha256']='0'*64
    elif name=='authority_true':r[0]['grants_input_authority']=True
    elif name=='v3_claims_physical':r[0]['physical_verification_authoritative']=True
    elif name=='unverified_batch':r[0]['owner_transition_verified']=False
    elif name=='wrong_pair_set':del p['d']
    else:raise KeyError(name)
    return (r,p,s),False

FIXED=['valid_one','valid_two','v3_only','nonordinary','duplicate_position','duplicate_actuation','identifier_mismatch','step_mismatch','owner_mismatch','intent_mismatch','key_mismatch','missing_actuation','unconfirmed_down','unconfirmed_up','inverted_edges','up_outside_rpc','source_drift','authority_true','v3_claims_physical','unverified_batch','wrong_pair_set']

def main():
    t0=time.perf_counter_ns();fixed={};mismatch=0;timestamp_changes=0;authority_expansions=0;v3_only_accepted=0
    for name in FIXED:
        (r,p,s),want=mutate_case(name);c=candidate.bind_batch(r,p,s);o=oracle.oracle(r,p,s);ok=(accepted(c)==want==o)
        fixed[name]=dict(pass_=ok,candidate=c['status'],oracle=o,want=want)
        mismatch+=not (accepted(c)==o)
        if name=='v3_only' and accepted(c):v3_only_accepted+=1
    # Exhaustive orthogonal small domain: one-key case, 2^12 validity toggles.
    exhaustive=0;ex_mismatch=0
    toggles=list(range(12))
    for bits in itertools.product((0,1), repeat=len(toggles)):
        r,p,s=make(1);exhaustive+=1
        # each bit=1 preserves validity, 0 breaks exactly one condition; combinations stress precedence
        if not bits[0]: r[0]['ordinary_release_candidate']=False
        if not bits[1]: r[0]['owner_transition_verified']=False
        if not bits[2]: r[0]['grants_input_authority']=True
        if not bits[3]: r[0]['physical_verification_authoritative']=True
        if not bits[4]: p['a'][0]['status']='PRESS_UNCONFIRMED';p['a'][0]['interval']=None
        if not bits[5]: p['a'][1]['status']='RELEASE_UNCONFIRMED';p['a'][1]['interval']=None
        if not bits[6]: p['a'][1]['owner_id']='other';p['a'][0]['owner_id']='other'
        if not bits[7]: p['a'][1]['intent_token']='other';p['a'][0]['intent_token']='other'
        if not bits[8]: p['a'][1]['key']='x';p['a'][0]['key']='x'
        if not bits[9]: s['adapter_contract_sha256']='f'*64
        if not bits[10]: p['a'][1]['interval']=(999,1001)
        if not bits[11]: r[0]['release_batch_position']=1
        c=candidate.bind_batch(r,p,s);o=oracle.oracle(r,p,s);ex_mismatch += (accepted(c)!=o)
    # Random mutation corpus. Oracle is independent and only compares accept/reject.
    rng=random.Random(SEED);h=hashlib.sha256();rnd_mismatch=0;accepted_n=0
    fields=['ordinary','verified','authority','v3phys','dstatus','ustatus','owner','intent','key','source','rpc','pos','size','id','step','duplicate_act']
    for i in range(N_RANDOM):
        n=1 if rng.random()<0.55 else 2;r,p,s=make(n)
        k=rng.randrange(0,5)
        chosen=rng.sample(fields,k=min(k,len(fields)))
        for f in chosen:
            j=rng.randrange(n);key=r[j]['key']
            if f=='ordinary':r[j]['ordinary_release_candidate']=False
            elif f=='verified':r[j]['owner_transition_verified']=False
            elif f=='authority':r[j]['grants_input_authority']=True
            elif f=='v3phys':r[j]['physical_verification_authoritative']=True
            elif f=='dstatus':p[key][0]['status']='OWNER_ALREADY_HELD';p[key][0]['interval']=None
            elif f=='ustatus':p[key][1]['status']='NOOP_ALREADY_UP';p[key][1]['interval']=None
            elif f=='owner':p[key][0]['owner_id']='other';p[key][1]['owner_id']='other'
            elif f=='intent':p[key][0]['intent_token']='other';p[key][1]['intent_token']='other'
            elif f=='key':p[key][0]['key']='x';p[key][1]['key']='x'
            elif f=='source':s['session_map01_v13_git_blob']='0'*40
            elif f=='rpc':p[key][1]['interval']=(r[j]['release_call_started_ns']-2,r[j]['release_call_started_ns']-1)
            elif f=='pos':r[j]['release_batch_position']=9
            elif f=='size':r[j]['release_batch_size']=n+1
            elif f=='id':r[j]['release_batch_identifier']='other'
            elif f=='step':r[j]['release_batch_step']=99
            elif f=='duplicate_act' and n==2:
                ks=[x['key'] for x in r];p[ks[1]][0]['actuation_id']=p[ks[0]][0]['actuation_id'];p[ks[1]][1]['actuation_id']=p[ks[0]][1]['actuation_id']
        c=candidate.bind_batch(r,p,s);o=oracle.oracle(r,p,s);a=accepted(c);rnd_mismatch+=(a!=o);accepted_n+=a
        if a:
            # Accepted output must copy all authoritative intervals, never synthesize/narrow them.
            by={x['key']:x for x in c['actuations']}
            for row in r:
                key=row['key'];d,u=p[key];z=by[key]
                timestamp_changes += z['physical_down_interval']!=list(d['interval']) or z['physical_up_interval']!=list(u['interval']) or z['map01_release_rpc_interval']!=[row['release_call_started_ns'],row['release_call_returned_ns']]
                authority_expansions += z['grants_input_authority'] is not False or c['grants_input_authority'] is not False
        h.update(json.dumps({'i':i,'a':a,'o':o,'s':c['status']},sort_keys=True,separators=(',',':')).encode())
    decision='PASS_MAP01_V12_PLAN_STEP_LINEAGE_R0_SCOPED' if (all(x['pass_'] for x in fixed.values()) and mismatch==0 and ex_mismatch==0 and rnd_mismatch==0 and v3_only_accepted==0 and timestamp_changes==0 and authority_expansions==0) else 'FAIL_R0'
    result=dict(task='MAP01-V12-PLAN-STEP-LINEAGE-R0-20260919-001',issue=1907,base='7f02687f8136ea6a390fc800900937adc227969c',decision=decision,primary_invocations=1,reruns=0,tuning=0,
      fixed_controls=fixed,exhaustive_cases=exhaustive,exhaustive_mismatches=ex_mismatch,random_seed=SEED,random_cases=N_RANDOM,random_mismatches=rnd_mismatch,random_accepted=accepted_n,
      v3_only_accepted=v3_only_accepted,timestamp_changes=timestamp_changes,authority_expansions=authority_expansions,case_digest_sha256=h.hexdigest(),elapsed_ns=time.perf_counter_ns()-t0)
    (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['decision','exhaustive_cases','exhaustive_mismatches','random_cases','random_mismatches','random_accepted','v3_only_accepted','timestamp_changes','authority_expansions','case_digest_sha256','elapsed_ns']},sort_keys=True))
if __name__=='__main__':main()
