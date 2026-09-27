import json,random,hashlib
from model import State,step
from oracle import oracle
SEED=112420260918001
N=250000

def event(r):
    if r.random()<.12:return {'kind':'backend_lost'}
    d={'kind':'release_observation','owner_id':r.choice(['o','x']),'intent_token':r.choice(['i','j']),'key':r.choice(['F8','F9']),
       'server_generation':r.choice(['G1','G2','G3']),'cleanup_attempt_id':r.choice(['a1','a2']),'key_up':bool(r.getrandbits(1))}
    if r.random()<.02:d.pop(r.choice(list(d.keys())[1:]))
    return d

def main():
    r=random.Random(SEED); mismatch=cross=valid=malformed=0; digest=hashlib.sha256(); steps=0
    for idx in range(N):
        init=('o','i','F8','G1','a1'); ev=[event(r) for _ in range(r.randint(1,8))]
        s=State(*init)
        try:
            for e in ev: step(s,e); steps+=1
            got=(s.status,s.verified_empty)
        except Exception:
            got=('ERROR',False)
        exp=oracle(init,ev)
        mismatch += got!=exp
        malformed += exp[0]=='ERROR'
        valid += got==('RELEASE_CONFIRMED',True)
        if got==('RELEASE_CONFIRMED',True):
            seen=False
            for e in ev:
                if e.get('kind')=='backend_lost': break
                if e.get('kind')=='release_observation' and all(e.get(k)==v for k,v in [('owner_id','o'),('intent_token','i'),('key','F8'),('server_generation','G1'),('cleanup_attempt_id','a1')]) and e.get('key_up') is True:
                    seen=True; break
            if not seen: cross+=1
        digest.update(json.dumps([idx,ev,got],sort_keys=True,separators=(',',':')).encode())
    out={'task':'XSERVER-RELEASE-CONFIRMATION-GENERATION-20260918-001','seed':SEED,'traces':N,'event_steps':steps,'candidate_oracle_mismatches':mismatch,
         'retro_confirmation_escapes':cross,'confirmed':valid,'malformed':malformed,'authority_grants':0,'task_input_grants':0,'digest_sha256':digest.hexdigest()}
    out['decision']='PASS_RELEASE_CONFIRMATION_GENERATION_BINDING_SCOPED' if mismatch==cross==0 else 'FAIL_CONTRACT_SEMANTICS'
    open('RESULT.json','w').write(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
