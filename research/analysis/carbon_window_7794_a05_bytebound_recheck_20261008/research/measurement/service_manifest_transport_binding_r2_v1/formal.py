from __future__ import annotations
import json, random
from pathlib import Path
from model import RELATIONS, semantic_manifest, canonical_hash, binding, inline_manifest, resolve
from oracle import decide
ROOT=Path(__file__).resolve().parent
SEED=164420260918001
N=240000
SESSIONS=('s0','s1','s2','s3')
ADAPTERS=('adapterA','adapterB')
REQUEST=('control','observation','operation_schema','capability_snapshot','observation_catalog','events')

def endpoints(adapter,rev):
    return {f'rel.{r}':f'{adapter}|{r}|{rev}' for r in RELATIONS}

def main():
    rng=random.Random(SEED)
    manifest=semantic_manifest(); mh=canonical_hash(manifest)
    mismatch=0; manifest_hash_changes=0; invalid_binding_authorizations=0
    current_bound=0; fallback=0; cached_stale=0; refreshed_hash_changes=0
    binding_changes=0; rotations=0; switches=0; withdrawals=0; stable=0
    for i in range(N):
        session=SESSIONS[i&3]
        relation=REQUEST[rng.randrange(len(REQUEST))]
        epoch=1; adapter='adapterA'; eps0=endpoints(adapter,0); current_eps=dict(eps0)
        cached=inline_manifest(session,epoch,adapter,eps0); cached_ep=eps0[f'rel.{relation}']
        mode=i&3
        if mode==0:
            stable+=1
        elif mode==1:
            epoch=2; current_eps=endpoints(adapter,1); rotations+=1; binding_changes+=1
        elif mode==2:
            epoch=2; adapter='adapterB'; current_eps=endpoints(adapter,0); switches+=1; binding_changes+=1
        else:
            epoch=2; current_eps=endpoints(adapter,0); current_eps.pop(f'rel.{relation}'); withdrawals+=1; binding_changes+=1
        cur=binding('agent-interface',1,epoch,adapter,current_eps)
        got=resolve(manifest,'agent-interface',1,epoch,cur,relation)
        exp=decide(manifest,'agent-interface',1,epoch,cur,relation)
        if got!=exp: mismatch+=1
        if got[0]=='BOUND': current_bound+=1
        elif got[0]=='FALLBACK': fallback+=1
        if canonical_hash(manifest)!=mh: manifest_hash_changes+=1
        current_target=current_eps.get(f'rel.{relation}')
        if mode!=0 and cached_ep!=current_target: cached_stale+=1
        refreshed=inline_manifest(session,epoch,adapter,current_eps)
        if canonical_hash(refreshed)!=canonical_hash(cached): refreshed_hash_changes+=1
        variants=[
          binding('agent-interface',1,max(0,epoch-1),adapter,current_eps),
          binding('agent-interface',1,epoch+1,adapter,current_eps),
          binding('other-service',1,epoch,adapter,current_eps),
          binding('agent-interface',2,epoch,adapter,current_eps),
        ]
        for bad in variants:
            if resolve(manifest,'agent-interface',1,epoch,bad,relation)[0] in ('BOUND','FALLBACK'):
                invalid_binding_authorizations+=1
    passed=(mismatch==0 and manifest_hash_changes==0 and invalid_binding_authorizations==0
            and current_bound>0 and fallback>0 and cached_stale>0
            and refreshed_hash_changes==binding_changes and rotations>=50000 and switches>=50000
            and N==stable+rotations+switches+withdrawals)
    out={
      'task':'SERVICE-MANIFEST-TRANSPORT-BINDING-R2-20260918-001','formal_invocations':1,'reruns':0,
      'seed':SEED,'histories':N,'candidate_oracle_mismatch':mismatch,
      'logical_binding':{'semantic_manifest_hash_changes':manifest_hash_changes,'invalid_binding_authorizations':invalid_binding_authorizations,
                         'current_bound_selections':current_bound,'fallback_selections':fallback},
      'inline_cached':{'stale_endpoint_selections':cached_stale},
      'inline_refreshed':{'manifest_hash_changes':refreshed_hash_changes},
      'binding_changes':binding_changes,'stable_histories':stable,'endpoint_rotations':rotations,'adapter_switches':switches,
      'relation_withdrawals':withdrawals,
      'decision':'PASS_SERVICE_MANIFEST_TRANSPORT_BINDING_R2_SCOPED' if passed else 'FAIL_TRANSPORT_BINDING_SEMANTICS',
      'pass':passed}
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
