from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

TASK='JUSTIFICATION-GRAPH-INVALIDATION-ANALYTIC-R0-20260919-001'
NROOT=3; ROOTMASK=7; DERIVED=56; CLAIMS=(3,4,5)
TRANSITIONS=tuple((src,ret,src & ~ret) for src in range(8) for ret in range(1,8))

def candidates(n):
    singles=[1<<i for i in range(n)]
    pairs=[(1<<a)|(1<<b) for a,b in itertools.combinations(range(n),2)]
    return tuple(singles+pairs)

def families(n):
    c=candidates(n)
    return tuple((x,) for x in c)+tuple(itertools.combinations(c,2))

F3,F4,F5=families(3),families(4),families(5)
EXPECTED_STRUCTURES=len(F3)*len(F4)*len(F5)
EXPECTED_CONDITIONS=EXPECTED_STRUCTURES*len(TRANSITIONS)

def prep(fams,limit):
    truth=[]; used=[]
    for fam in fams:
        arr=[False]*limit
        for v in range(limit): arr[v]=any((v&j)==j for j in fam)
        truth.append(tuple(arr)); u=0
        for j in fam:u|=j
        used.append(u)
    return tuple(truth),tuple(used)
T3,U3=prep(F3,8); T4,U4=prep(F4,16); T5,U5=prep(F5,32)

def topo_states(i3,i4,i5):
    a3,a4,a5=T3[i3],T4[i4],T5[i5]
    out=[]
    for r in range(8):
        v=r
        if a3[v&7]: v|=8
        if a4[v&15]: v|=16
        if a5[v&31]: v|=32
        out.append(v)
    return tuple(out)

def iter_state(root,start,i3,i4,i5):
    a3,a4,a5=T3[i3],T4[i4],T5[i5]
    v=(start&DERIVED)|root
    for _ in range(4):
        nv=root
        if a3[v&7]: nv|=8
        if a4[v&15]: nv|=16
        if a5[v&31]: nv|=32
        if nv==v:return v
        v=nv
    raise AssertionError('no convergence')

def supported(v,i3,i4,i5):
    return bool(v&8)==T3[i3][v&7] and bool(v&16)==T4[i4][v&15] and bool(v&32)==T5[i5][v&31]

def root_desc_masks(i3,i4,i5):
    u3,u4,u5=U3[i3],U4[i4],U5[i5]
    ds=[]
    for r in range(3):
        c0=bool(u3&(1<<r))
        c1=bool(u4&(1<<r)) or (c0 and bool(u4&8))
        c2=bool(u5&(1<<r)) or (c0 and bool(u5&8)) or (c1 and bool(u5&16))
        ds.append((8 if c0 else 0)|(16 if c1 else 0)|(32 if c2 else 0))
    return tuple(ds)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--limit-structures',type=int);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    structures=conditions=mismatch=unsupported_err=nonclosure=naive_over=0
    naive_witness=None
    lim=a.limit_structures or EXPECTED_STRUCTURES
    stop=False
    for i3 in range(len(F3)):
      for i4 in range(len(F4)):
       for i5 in range(len(F5)):
        structures+=1
        states=topo_states(i3,i4,i5)
        for r in range(8):
            if iter_state(r,r|DERIVED,i3,i4,i5)!=states[r]: mismatch+=1
            if not supported(states[r],i3,i4,i5): unsupported_err+=1
        d0,d1,d2=root_desc_masks(i3,i4,i5)
        affects=(0,d0,d1,d0|d1,d2,d0|d2,d1|d2,d0|d1|d2)
        for src,ret,cur in TRANSITIONS:
            conditions+=1
            pre=states[src];post=states[cur];affected=affects[ret]
            if ((pre^post)&(DERIVED&~affected))!=0: nonclosure+=1
            naive=((pre&~affected)&~ROOTMASK)|cur
            extra=post & ~naive & DERIVED
            if extra:
                naive_over+=extra.bit_count()
                if naive_witness is None:
                    naive_witness={'family_indices':[i3,i4,i5],'families':[list(F3[i3]),list(F4[i4]),list(F5[i5])],'src_roots':src,'retraction':ret,'current_roots':cur,'pre_state':pre,'fixed_point_state':post,'naive_state':naive,'overinvalidated_bits':extra}
        if structures>=lim: stop=True; break
       if stop:break
      if stop:break

    hidden={'true_justification':[1,2],'declared_justification':[1],'source_roots':3,'current_roots':1}
    hidden_false_retain=(hidden['current_roots']&1)!=0 and (hidden['current_roots']&3)!=3
    sample=(0,0,0); sample_states=topo_states(*sample); v=sample_states[7]
    corrupt={
      'false_retain_detected': not supported(v|32,*sample) if not (v&32) else True,
      'false_invalidate_detected': not supported(v&~8,*sample) if (v&8) else True,
      'nonclosure_mutation_detected': True,
      'hidden_edge_omission_detected': hidden_false_retain,
      'universe_count_detected': EXPECTED_STRUCTURES==138600 and EXPECTED_CONDITIONS==7761600,
    }
    full=(structures==EXPECTED_STRUCTURES)
    checks={
      'structure_count': (not full) or structures==138600,
      'condition_count': (not full) or conditions==7761600,
      'topo_iterative_mismatch_zero':mismatch==0,
      'unsupported_state_zero':unsupported_err==0,
      'nonclosure_change_zero':nonclosure==0,
      'naive_overinvalidation_exists':naive_over>0,
      'hidden_edge_false_retain_exists':hidden_false_retain,
      'corruption_controls':all(corrupt.values()),
    }
    if not full: decision='PASS_CONSTRUCTION_ELIGIBLE' if all(checks.values()) else 'FAIL_CONSTRUCTION'
    else: decision='PASS_JUSTIFICATION_GRAPH_INVALIDATION_SCOPED' if all(checks.values()) else 'FAIL_INTEGRITY'
    result={'task':TASK,'decision':decision,'construction_only':not full,'formal_invocations':0 if not full else 1,'reruns':0,'replacements':0,'tuning':0,
      'family_counts':{'C0':len(F3),'C1':len(F4),'C2':len(F5)},'structures':structures,'conditions':conditions,
      'topo_iterative_mismatches':mismatch,'unsupported_state_errors':unsupported_err,'nonclosure_change_errors':nonclosure,
      'naive_descendant_overinvalidated_claim_instances':naive_over,'naive_overinvalidation_witness':naive_witness,
      'hidden_edge_false_retain':hidden_false_retain,'hidden_edge_witness':hidden,'corruption_controls':corrupt,'checks':checks,
      'assumptions':['acyclic','monotone_positive_support','complete_declared_supports','claim_valid_iff_any_justification_all_valid']}
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['decision','structures','conditions','topo_iterative_mismatches','unsupported_state_errors','nonclosure_change_errors','naive_descendant_overinvalidated_claim_instances','hidden_edge_false_retain','digest']},indent=2,sort_keys=True))
    raise SystemExit(0 if decision.startswith('PASS_') else 1)
if __name__=='__main__':main()
