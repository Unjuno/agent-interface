#!/usr/bin/env python3
import json, math, hashlib
from pathlib import Path
A=range(5)

def rgs_partitions(n):
    # Restricted-growth-string enumeration independent of formal.py's recursive insertion.
    out=[]
    def rec(seq,maxv):
        if len(seq)==n:
            blocks=[]
            for j in range(maxv+1): blocks.append(tuple(i for i,v in enumerate(seq) if v==j))
            out.append(tuple(blocks)); return
        for v in range(maxv+2):
            rec(seq+[v],max(maxv,v))
    rec([0],0)
    # rec above permits invalid jumps; retain canonical RGS only.
    good=[]
    for p in out:
        seq=[None]*n
        for j,b in enumerate(p):
            for x in b: seq[x]=j
        ok=seq[0]==0 and all(seq[i] <= 1+max(seq[:i]) for i in range(1,n))
        if ok: good.append(p)
    return sorted(set(good),key=lambda p:(len(p),p))

def idx(p): return {x:j for j,b in enumerate(p) for x in b}
def operational(w,t):
    wi,ti=idx(w),idx(t)
    for b in w:
        if len({ti[x] for x in b})!=1:return False
    return True

def main():
    root=Path(__file__).parent; r=json.loads((root/'RESULT.json').read_text()); errors=[]
    ps=rgs_partitions(5)
    if len(ps)!=52: errors.append(['partition_count',len(ps)])
    pairs=0; feasible=0
    for w in ps:
        for t in ps:
            pairs+=1; feasible+=int(operational(w,t))
    if pairs!=r['witness_taxonomy_pairs']: errors.append('pairs')
    if feasible!=r['feasible_pairs']: errors.append(['feasible',feasible,r['feasible_pairs']])
    if r['exact_five_class_min_witness_states']!=5: errors.append('min_states')
    if r['exact_five_class_fixed_length_bits_lower_bound']!=math.ceil(math.log2(5)): errors.append('bits')
    sr=r['selected_rungs']
    expected={'NONE':(1,1,False),'SELF_BIT':(2,2,False),'SESSION_SCOPE':(3,5,False),'EXACT_ACTOR_CLASS':(5,52,True)}
    for k,(states,taxcount,exact) in expected.items():
        x=sr[k]
        if (x['witness_states'],x['safe_taxonomy_count'],x['exact_five_class_feasible'])!=(states,taxcount,exact): errors.append('selected:'+k)
    if r['parent_1579_blobs']!={'report':'a5ef28df339642cde2d585fcc199197635a1da25','result':'8ff6b368329d05e7724330305ff8cd006401aa42','proof':'9bf2190fab6429b2a98900c20fcf438e7f822efd'}: errors.append('parent')
    out={'pass':not errors,'errors':errors,'partitions':len(ps),'pairs':pairs,'feasible_pairs':feasible,'result_sha256':hashlib.sha256((root/'RESULT.json').read_bytes()).hexdigest()}
    (root/'INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(bool(errors))
if __name__=='__main__':main()
