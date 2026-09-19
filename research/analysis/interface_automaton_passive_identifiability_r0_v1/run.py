import itertools, json, hashlib, platform, sys

STATES=range(3); ACTIONS=range(2); PAIRS=list(itertools.product(STATES,ACTIONS)); N=len(PAIRS)
AUTOMATA=list(itertools.product(STATES, repeat=N))

def signature(a, mask):
    return tuple(a[i] if mask>>i&1 else None for i in range(N))

def run():
    classes={}
    for mask in range(1<<N):
        groups={}
        for a in AUTOMATA: groups.setdefault(signature(a,mask),0); groups[signature(a,mask)]+=1
        sizes=sorted(groups.values())
        k=mask.bit_count(); expected=3**(N-k)
        assert sizes and all(x==expected for x in sizes)
        assert (len(groups)==len(AUTOMATA)) == (k==N)
        classes[str(mask)]={"observed_pairs":k,"groups":len(groups),"class_size":expected}
    # explicit one-missing witness
    a=(0,)*N; b=list(a); b[-1]=1; b=tuple(b)
    assert a!=b and signature(a,(1<<(N-1))-1)==signature(b,(1<<(N-1))-1)
    result={"decision":"PASS_PASSIVE_AUTOMATON_COVERAGE_IDENTIFIABILITY_SCOPED","states":3,"actions":2,"automata":len(AUTOMATA),"coverage_masks":1<<N,"classes":classes,"formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,"witness":True,"python":sys.version,"platform":platform.platform()}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result["sha256"]=hashlib.sha256(raw).hexdigest()
    return result

if __name__=='__main__': print(json.dumps(run(),sort_keys=True,indent=2))
