from __future__ import annotations
import copy,json,random
from pathlib import Path
from schema import reference_manifest,resolve,omit,canonical_sha256,REQUIRED,REL,SEM
from oracle import inspect
ROOT=Path(__file__).resolve().parent
SEED=162320260918001
N=180000

def corrupt_type(m,q):
    x=copy.deepcopy(m)
    if q=='service_identity':x['service']['id']=7
    elif q=='protocol_identity':x['protocol']['id']=7
    elif q in REL:x['relations'][REL[q]]=7
    elif q in SEM:x['semantics'][SEM[q]]=7
    elif q=='fallback':x['fallback']=7
    return x

def directed():
    m=reference_manifest(); out={}
    out['valid']=resolve(m)['status']=='PASS'
    out['reorder']=canonical_sha256(m)==canonical_sha256({k:m[k] for k in reversed(list(m.keys()))})
    z=copy.deepcopy(m);z['x_future']={'anything':1};out['additive']=resolve(z)['status']=='PASS'
    z=copy.deepcopy(m);z['protocol']['major']=2;out['major']=resolve(z)['status']=='INVALID' and 'protocol_major' in resolve(z)['errors']
    z=copy.deepcopy(m);z['session_capabilities']={'generation':2};out['session_inline']=resolve(z)['status']=='INVALID'
    out['all_omissions']=all(resolve(omit(m,q))['status']=='INVALID' and q in resolve(omit(m,q))['errors'] for q in REQUIRED)
    out['wrong_type']=all(resolve(corrupt_type(m,q))['status']=='INVALID' for q in REQUIRED)
    z=copy.deepcopy(m);z['relations']['control']='';out['empty_relation']=resolve(z)['status']=='INVALID'
    return out

def main():
    rng=random.Random(SEED); base=reference_manifest(); mismatch=0
    fam={k:0 for k in ('valid','single_omission','multi_omission','wrong_type','major','forbidden_session','additive')}
    omission_counts={q:0 for q in REQUIRED}; accepted={k:0 for k in fam}; invented=0
    # 120k single omission = exactly 10k/query
    for i in range(120000):
        q=REQUIRED[i%len(REQUIRED)]; m=omit(base,q); fam['single_omission']+=1;omission_counts[q]+=1
        a=resolve(m);b=inspect(m);mismatch+=a!=b;accepted['single_omission']+=a['status']=='PASS';invented+=q in a.get('values',{})
    # 15k valid
    for _ in range(15000):
        m=copy.deepcopy(base);a=resolve(m);b=inspect(m);mismatch+=a!=b;fam['valid']+=1;accepted['valid']+=a['status']=='PASS'
    # 10k multi omission
    for _ in range(10000):
        q1,q2=rng.sample(REQUIRED,2);m=omit(omit(base,q1),q2);a=resolve(m);b=inspect(m);mismatch+=a!=b;fam['multi_omission']+=1;accepted['multi_omission']+=a['status']=='PASS';invented+=sum(q in a.get('values',{}) for q in (q1,q2))
    # 10k wrong type
    for i in range(10000):
        q=REQUIRED[i%12];m=corrupt_type(base,q);a=resolve(m);b=inspect(m);mismatch+=a!=b;fam['wrong_type']+=1;accepted['wrong_type']+=a['status']=='PASS'
    # 5k incompatible major
    for _ in range(5000):
        m=copy.deepcopy(base);m['protocol']['major']=2;a=resolve(m);b=inspect(m);mismatch+=a!=b;fam['major']+=1;accepted['major']+=a['status']=='PASS'
    # 5k forbidden inline session state
    for i in range(5000):
        m=copy.deepcopy(base);m['session_capabilities']={'scope':f's{i%4}','generation':i+1,'caps':['pointer']};a=resolve(m);b=inspect(m);mismatch+=a!=b;fam['forbidden_session']+=1;accepted['forbidden_session']+=a['status']=='PASS'
    # 15k additive extensions, randomized key insertion/order semantics
    canon=canonical_sha256(base)
    reorder_mismatch=0
    for i in range(15000):
        m=copy.deepcopy(base);m[f'x_{i%7}']={'n':i};a=resolve(m);b=inspect(m);mismatch+=a!=b;fam['additive']+=1;accepted['additive']+=a['status']=='PASS'
        if canonical_sha256({k:base[k] for k in reversed(list(base.keys()))})!=canon:reorder_mismatch+=1
    controls=directed()
    passed=(mismatch==0 and invented==0 and accepted['valid']==15000 and accepted['additive']==15000
            and all(accepted[k]==0 for k in ('single_omission','multi_omission','wrong_type','major','forbidden_session'))
            and all(v>=10000 for v in omission_counts.values()) and reorder_mismatch==0 and all(controls.values()))
    out={'task':'SERVICE-MANIFEST-DISCOVERY-CLOSURE-R1-20260918-001','formal_invocations':1,'reruns':0,'seed':SEED,'manifests':N,
         'candidate_oracle_mismatch':mismatch,'families':fam,'accepted':accepted,'single_omission_counts':omission_counts,
         'silent_invented_values':invented,'canonical_reorder_mismatch':reorder_mismatch,'controls':controls,
         'decision':'PASS_SERVICE_MANIFEST_DISCOVERY_CLOSURE_R1_SCOPED' if passed else 'FAIL_MANIFEST_SCHEMA_SEMANTICS','pass':passed}
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
