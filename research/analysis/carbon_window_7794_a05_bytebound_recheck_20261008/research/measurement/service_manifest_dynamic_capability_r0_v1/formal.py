from __future__ import annotations
import json, random
from pathlib import Path
from model import stable_manifest, inline_manifest, digest, snapshot, linked_select, validate_manifest, BASE_CAPS
from oracle import decide
ROOT=Path(__file__).resolve().parent
SEED=160720260918001
SESSIONS=('s0','s1','s2','s3')
EXTRA=('clipboard','semantic_click','ui_tree','effect_verify')
N=250000

def directed():
    out={}
    m=stable_manifest(); h=digest(m)
    caps=set(BASE_CAPS)|{'clipboard'}
    s=snapshot('s0',1,caps)
    out['stable_supported']=linked_select(m,'s0',1,caps,s,'clipboard')=='SUPPORTED'
    caps2=set(BASE_CAPS)
    out['stale_after_revoke']=linked_select(m,'s0',2,caps2,s,'clipboard')=='DISCOVER_CAPABILITIES'
    out['fresh_after_revoke']=linked_select(m,'s0',2,caps2,snapshot('s0',2,caps2),'clipboard')=='FALLBACK'
    out['future_generation']=linked_select(m,'s0',2,caps2,snapshot('s0',3,caps2),'pointer')=='DISCOVER_CAPABILITIES'
    out['wrong_scope']=linked_select(m,'s0',2,caps2,snapshot('s1',2,caps2),'pointer')=='DISCOVER_CAPABILITIES'
    bad=dict(m); bad['relations']=dict(m['relations']); bad['relations'].pop('capability_snapshot')
    out['missing_capability_link']=validate_manifest(bad)[1]=='capability_discovery'
    bad2=dict(m); bad2.pop('fallback')
    out['missing_fallback']=validate_manifest(bad2)[1]=='fallback'
    out['stable_hash']=digest(m)==h
    return out

def main():
    rng=random.Random(SEED)
    service=stable_manifest(); service_hash=digest(service)
    mismatch=0; linked_stale=0; linked_supported=0; fallback_seen=0
    cached_stale=0; refreshed_hash_changes=0; changes=0; revocations=0; additions=0
    invalid_snapshot_authorizations=0
    for i in range(N):
        scope=SESSIONS[i&3]
        gen=1
        caps=set(BASE_CAPS)
        # force broad discriminator coverage while retaining seeded variation
        mode=i%5
        cap=EXTRA[rng.randrange(len(EXTRA))]
        if mode in (0,1):
            caps.add(cap)
        cached=inline_manifest(scope,gen,caps); cached_caps=set(cached['session_capabilities']['caps'])
        refreshed_hash=digest(cached)
        requested=cap if mode!=4 else 'pointer'
        # mutate current state after stable/cached discovery
        if mode==0: # revoke
            gen+=1; caps.discard(cap); revocations+=1; changes+=1
        elif mode==1: # add a different capability after initial support
            gen+=1; newcap=EXTRA[(EXTRA.index(cap)+1)%len(EXTRA)]; caps.add(newcap); requested=newcap; additions+=1; changes+=1
        elif mode==2: # addition from base
            gen+=1; caps.add(cap); additions+=1; changes+=1
        elif mode==3: # generation-only currentness shift
            gen+=1; changes+=1
        # linked current snapshot
        current_snap=snapshot(scope,gen,caps)
        got=linked_select(service,scope,gen,caps,current_snap,requested)
        exp=decide(scope,gen,caps,current_snap,requested,True)
        if got!=exp: mismatch+=1
        if got=='SUPPORTED': linked_supported+=1
        if got=='FALLBACK': fallback_seen+=1
        # inject stale/future/wrong-scope checks; none may authorize
        variants=[snapshot(scope,max(0,gen-1),caps),snapshot(scope,gen+1,caps),snapshot(SESSIONS[(i+1)&3],gen,caps)]
        for v in variants:
            if linked_select(service,scope,gen,caps,v,requested)=='SUPPORTED': invalid_snapshot_authorizations+=1
        # cached inline makes decisions from stale embedded caps after mutation
        if requested in cached_caps and requested not in caps: cached_stale+=1
        # refreshed inline preserves freshness by changing bytes whenever encoded state changes
        refreshed=inline_manifest(scope,gen,caps)
        if digest(refreshed)!=refreshed_hash: refreshed_hash_changes+=1
        if digest(service)!=service_hash: linked_stale+=1 # overloaded as impossible stable-hash change count
    controls=directed()
    passed=(mismatch==0 and linked_stale==0 and linked_supported>0 and fallback_seen>0 and cached_stale>0
            and refreshed_hash_changes==changes and invalid_snapshot_authorizations==0 and all(controls.values())
            and revocations>=50000 and additions>=50000)
    out={'task':'SERVICE-MANIFEST-DYNAMIC-CAPABILITY-SEPARATION-R0-20260918-001','formal_invocations':1,'reruns':0,'seed':SEED,'histories':N,
         'linked':{'candidate_oracle_mismatch':mismatch,'service_manifest_hash_changes':linked_stale,'supported_selections':linked_supported,'fallback_selections':fallback_seen,'invalid_snapshot_authorizations':invalid_snapshot_authorizations},
         'inline_cached':{'stale_support_assumptions':cached_stale},
         'inline_refreshed':{'manifest_hash_changes':refreshed_hash_changes},
         'capability_changes':changes,'revocations':revocations,'additions':additions,'controls':controls,
         'decision':'PASS_SERVICE_MANIFEST_CAPABILITY_SEPARATION_SCOPED' if passed else 'FAIL_SERVICE_MANIFEST_SEPARATION','pass':passed}
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if passed else 1)
if __name__=='__main__': main()
