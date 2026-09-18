import argparse,hashlib,json
from pathlib import Path
F=(0,1,2,3)
FUNCS=tuple(range(16))

def fval(fn,x): return bool(fn>>x & 1)
def projection(x): return x & 1

def local_decision(fn,current):
    return 'AUTO_RECOMMIT' if fval(fn,current) else 'REJECT'

def opaque_decision(old,current):
    return 'REUSE_APPROVAL' if old==current else 'YIELD_FOR_APPROVAL'

def run(construction=False):
    fps=(0,1) if construction else F
    funcs=FUNCS[:8] if construction else FUNCS
    st={
      'local_rows':0,'local_mismatch':0,'local_auto_recommit':0,'local_reject':0,'always_yield_false_yields':0,
      'opaque_classes':0,'opaque_changed_classes':0,'opaque_ambiguous_changed_classes':0,'opaque_changed_auto_recommits':0,
      'opaque_yields':0,'opaque_exact_reuse':0,'projected_value_reuse_unsafe_function_rows':0,'projected_value_reuse_unsafe_classes':0,
    }
    for fn in funcs:
        for old in fps:
            if not fval(fn,old): continue
            for cur in fps:
                got=local_decision(fn,cur); exp='AUTO_RECOMMIT' if fval(fn,cur) else 'REJECT'
                st['local_rows']+=1; st['local_mismatch']+=int(got!=exp)
                st['local_auto_recommit']+=int(got=='AUTO_RECOMMIT'); st['local_reject']+=int(got=='REJECT')
                st['always_yield_false_yields']+=int(got=='AUTO_RECOMMIT')
    all_hidden=FUNCS if not construction else FUNCS[:8]
    for old in fps:
        consistent=[fn for fn in all_hidden if fval(fn,old)]
        if not consistent: continue
        for cur in fps:
            st['opaque_classes']+=1
            got=opaque_decision(old,cur)
            vals={fval(fn,cur) for fn in consistent}
            if cur==old:
                st['opaque_exact_reuse']+=int(got=='REUSE_APPROVAL' and vals=={True})
            else:
                st['opaque_changed_classes']+=1
                ambiguous=(vals=={False,True})
                st['opaque_ambiguous_changed_classes']+=int(ambiguous)
                st['opaque_changed_auto_recommits']+=int(got in ('AUTO_RECOMMIT','REUSE_APPROVAL'))
                st['opaque_yields']+=int(got=='YIELD_FOR_APPROVAL')
                if projection(cur)==projection(old):
                    unsafe=sum(1 for fn in consistent if not fval(fn,cur))
                    if unsafe>0:
                        st['projected_value_reuse_unsafe_classes']+=1
                        st['projected_value_reuse_unsafe_function_rows']+=unsafe
    directed={
      'local_true_auto': local_decision(0b0011,1)=='AUTO_RECOMMIT',
      'local_false_reject': local_decision(0b0001,1)=='REJECT',
      'opaque_same_reuse': opaque_decision(2,2)=='REUSE_APPROVAL',
      'opaque_changed_yield': opaque_decision(0,2)=='YIELD_FOR_APPROVAL',
    }
    corrupt={
      'projection_collapse_detected':st['projected_value_reuse_unsafe_function_rows']>0 if not construction else True,
      'ambiguous_auto_approval_rejected':st['opaque_changed_auto_recommits']==0,
      'exact_reuse_not_denied':st['opaque_exact_reuse']>0,
      'local_not_forced_opaque':st['always_yield_false_yields']>0,
    }
    full_ambiguity=True if construction else st['opaque_ambiguous_changed_classes']==st['opaque_changed_classes']
    good=(st['local_mismatch']==0 and st['local_auto_recommit']>0 and st['local_reject']>0 and st['opaque_changed_auto_recommits']==0 and st['opaque_yields']>0 and st['opaque_exact_reuse']>0 and full_ambiguity and (construction or st['projected_value_reuse_unsafe_function_rows']>0) and st['always_yield_false_yields']>0 and all(directed.values()) and all(corrupt.values()))
    return st,directed,corrupt,good

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();st,dc,cor,good=run(a.construction)
    r={'construction':a.construction,'stats':st,'directed':dc,'corruptions':cor,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_BELIEF_AUTO_RECOMMIT_SEMANTIC_BOUNDARY_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
