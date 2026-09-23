import itertools,json,hashlib
FIELDS=('image','focus','tree'); TIMES=range(3)
cases=list(itertools.product(TIMES,repeat=3))
def strict(ts): return len(set(ts))==1
def bounded(ts,delta): return max(ts)-min(ts)<=delta
def naive(ts): return True
def run():
    rows=[]
    for ts in cases:
        rows.append({'ts':ts,'strict':strict(ts),'bounded1':bounded(ts,1),'naive':naive(ts)})
    assert all((r['strict']==(len(set(r['ts']))==1)) for r in rows)
    assert all((r['bounded1']==(max(r['ts'])-min(r['ts'])<=1)) for r in rows)
    assert sum(r['strict'] for r in rows)==3
    assert sum(r['bounded1'] for r in rows)==15
    mixed=sum(not r['strict'] for r in rows if r['naive'])
    result={'decision':'PASS_OBSERVATION_EPOCH_JOIN_SEMANTICS_SCOPED','cases':len(cases),'strict_coherent':sum(r['strict'] for r in rows),'bounded_skew_delta1':sum(r['bounded1'] for r in rows),'naive_mixed_time_cases':mixed,'fields':FIELDS,'formal_invocations':1,'reruns':0,'tuning':0}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['sha256']=hashlib.sha256(raw).hexdigest();return result
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
