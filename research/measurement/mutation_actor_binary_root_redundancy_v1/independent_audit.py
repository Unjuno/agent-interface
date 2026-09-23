#!/usr/bin/env python3
import itertools,json,hashlib
from pathlib import Path

def bits(s):return tuple(int(c) for c in s)
def erase(word,k):return word[:k]+word[k+1:]
def one_error_ball(word):
    out={word}
    for k in range(len(word)):
        z=list(word);z[k]^=1;out.add(tuple(z))
    return out

def exhaustive_five_exists(m,mode):
    words=[tuple((x>>k)&1 for k in range(m)) for x in range(1<<m)]
    for code in itertools.combinations(words,5):
        if mode=='NO_FAULT':ok=len(set(code))==5
        elif mode=='ERASURE':ok=all(len({erase(w,k) for w in code})==5 for k in range(m))
        else:
            balls=[one_error_ball(w) for w in code]
            ok=all(balls[i].isdisjoint(balls[j]) for i in range(5) for j in range(i+1,5))
        if ok:return True
    return False

def main():
    root=Path(__file__).parent;r=json.loads((root/'RESULT.json').read_text());errs=[]
    exp={'NO_FAULT':3,'KNOWN_ERASURE_1':4,'UNKNOWN_BYZANTINE_1':6}
    modes={'NO_FAULT':'NO_FAULT','KNOWN_ERASURE_1':'ERASURE','UNKNOWN_BYZANTINE_1':'BYZ'}
    for name,m in exp.items():
        code=[bits(s) for s in r['threat_models'][name]['codebook']]
        if len(code)!=5 or any(len(w)!=m for w in code):errs.append('shape:'+name)
        if name=='NO_FAULT' and len(set(code))!=5:errs.append('direct:'+name)
        if name=='KNOWN_ERASURE_1' and not all(len({erase(w,k) for w in code})==5 for k in range(m)):errs.append('direct:'+name)
        if name=='UNKNOWN_BYZANTINE_1':
            balls=[one_error_ball(w) for w in code]
            if not all(balls[i].isdisjoint(balls[j]) for i in range(5) for j in range(i+1,5)):errs.append('direct:'+name)
        if exhaustive_five_exists(m-1,modes[name]):errs.append('smaller_counterexample:'+name)
    if r['parent_blobs']!={'partition_result':'91b4bf873337046101dc551ec8fb013db27858d0','single_root_compromise_result':'697d53777bd2b7bd621178ed577fb344271bc5fd'}:errs.append('parents')
    out={'pass':not errs,'errors':errs,'decision':r['decision'],'result_sha256':hashlib.sha256((root/'RESULT.json').read_bytes()).hexdigest(),'verified_min_roots':exp}
    (root/'INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(bool(errs))
if __name__=='__main__':main()
