#!/usr/bin/env python3
import itertools, json, math, hashlib
from pathlib import Path
ACTORS=['THIS_INTENT','THIS_SESSION_OTHER_INTENT','EXTERNAL_PROCESS','HUMAN','OS']
PARENTS={
 'partition_result':'91b4bf873337046101dc551ec8fb013db27858d0',
 'single_root_compromise_result':'697d53777bd2b7bd621178ed577fb344271bc5fd',
}

def hd(a,b): return (a^b).bit_count()
def fmt(x,m): return format(x,f'0{m}b')
def valid(code,m,d):
    return len(code)==5 and all(hd(a,b)>=d for a,b in itertools.combinations(code,2))

def find_code(m,d):
    # Deterministic backtracking with canonical first codeword 0; xor translation preserves distances.
    words=list(range(1<<m))
    target=5
    best=None
    def bt(start,chosen):
        nonlocal best
        if best is not None: return
        if len(chosen)==target:
            best=tuple(chosen); return
        if len(chosen)+(len(words)-start)<target: return
        for i in range(start,len(words)):
            w=words[i]
            if all(hd(w,x)>=d for x in chosen):
                bt(i+1,chosen+[w])
                if best is not None:return
    bt(0,[])
    return best

def min_roots(d):
    tried=[]
    for m in range(1,7):
        c=find_code(m,d); tried.append({'m':m,'found':c is not None})
        if c is not None:return m,c,tried
    return None,None,tried

def direct_no_fault(code,m):
    return len(set(code))==len(code)
def direct_erasure(code,m):
    for k in range(m):
        seen=set()
        for w in code:
            # remove coordinate k from LSB-indexed bit vector
            lo=w & ((1<<k)-1); hi=w>>(k+1); p=lo | (hi<<k)
            if p in seen:return False
            seen.add(p)
    return True
def direct_byz(code,m):
    balls=[]
    for w in code:
        s={w}
        for k in range(m):s.add(w^(1<<k))
        balls.append(s)
    return all(balls[i].isdisjoint(balls[j]) for i in range(len(balls)) for j in range(i+1,len(balls)))

def exhaustive_exists(m,d):
    if (1<<m)<5:return False
    for c in itertools.combinations(range(1<<m),5):
        if valid(c,m,d):return True
    return False

def main():
    specs={'NO_FAULT':1,'KNOWN_ERASURE_1':2,'UNKNOWN_BYZANTINE_1':3}
    out={}
    for name,d in specs.items():
        m,c,tried=min_roots(d)
        out[name]={
          'distance_required':d,'min_binary_roots':m,
          'codebook':[fmt(x,m) for x in c],
          'minimum_pair_distance':min(hd(a,b) for a,b in itertools.combinations(c,2)),
          'search_trace':tried,
          'direct_no_fault':direct_no_fault(c,m),
          'direct_erasure_1':direct_erasure(c,m),
          'direct_byzantine_1':direct_byz(c,m),
        }
    # Frozen negative controls: smaller-than-claimed root count cannot support 5 classes.
    controls={
      'm2_no_fault_exists':exhaustive_exists(2,1),
      'm3_erasure_exists':exhaustive_exists(3,2),
      'm5_byzantine_exists':exhaustive_exists(5,3),
    }
    errors=[]
    expected={'NO_FAULT':3,'KNOWN_ERASURE_1':4,'UNKNOWN_BYZANTINE_1':6}
    for k,v in expected.items():
        if out[k]['min_binary_roots']!=v:errors.append(f'min:{k}:{out[k]["min_binary_roots"]}')
    if controls!={'m2_no_fault_exists':False,'m3_erasure_exists':False,'m5_byzantine_exists':False}:errors.append('negative_controls')
    if not out['NO_FAULT']['direct_no_fault']:errors.append('nofault_direct')
    if not out['KNOWN_ERASURE_1']['direct_erasure_1']:errors.append('erasure_direct')
    if not out['UNKNOWN_BYZANTINE_1']['direct_byzantine_1']:errors.append('byz_direct')
    result={
      'task':'MUTATION-ACTOR-BINARY-ROOT-REDUNDANCY-20260918-001',
      'decision':'PASS_ACTOR_BINARY_ROOT_REDUNDANCY_BOUND_SCOPED' if not errors else 'FAIL_BOUND_COUNTEREXAMPLE',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'actors':ACTORS,'actor_count':5,'parent_blobs':PARENTS,
      'threat_models':out,'negative_controls':controls,
      'authority_promotions':0,'task_success_promotions':0,'errors':errors,
    }
    p=Path(__file__).parent/'RESULT.json'; p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    audit={
      'pass':not errors,'errors':errors,'decision':result['decision'],
      'result_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'formal_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'corruption_controls':{}
    }
    # Copy-result corruption controls.
    import copy
    muts=[]
    q=copy.deepcopy(result);q['threat_models']['NO_FAULT']['min_binary_roots']=2;muts.append(('nofault_underclaim',q))
    q=copy.deepcopy(result);q['threat_models']['KNOWN_ERASURE_1']['min_binary_roots']=3;muts.append(('erasure_underclaim',q))
    q=copy.deepcopy(result);q['threat_models']['UNKNOWN_BYZANTINE_1']['min_binary_roots']=5;muts.append(('byz_underclaim',q))
    q=copy.deepcopy(result);q['negative_controls']['m5_byzantine_exists']=True;muts.append(('negative_flip',q))
    q=copy.deepcopy(result);q['parent_blobs']['single_root_compromise_result']='0'*40;muts.append(('parent_identity',q))
    for name,q in muts:
        bad=False
        if q['threat_models']['NO_FAULT']['min_binary_roots']!=3:bad=True
        if q['threat_models']['KNOWN_ERASURE_1']['min_binary_roots']!=4:bad=True
        if q['threat_models']['UNKNOWN_BYZANTINE_1']['min_binary_roots']!=6:bad=True
        if q['negative_controls']!={'m2_no_fault_exists':False,'m3_erasure_exists':False,'m5_byzantine_exists':False}:bad=True
        if q['parent_blobs']!=PARENTS:bad=True
        audit['corruption_controls'][name]=bad
    audit['pass']=audit['pass'] and all(audit['corruption_controls'].values())
    (Path(__file__).parent/'AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':result['decision'],'models':{k:(v['min_binary_roots'],v['codebook']) for k,v in out.items()},'controls':controls,'errors':errors,'corruptions':audit['corruption_controls']},sort_keys=True))
    raise SystemExit(0 if audit['pass'] else 2)
if __name__=='__main__':main()
