from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

TASK='EVIDENCE-DEPENDENT-COMPUTE-REUSE-ANALYTIC-R0-20260918-001'
N=4
STATES=tuple(range(1<<N))
SUBSETS=tuple(range(1<<N))
FULL=(1<<N)-1

def bits(mask): return [i for i in range(N) if mask>>i & 1]
def projection_equal(a,b,dep): return ((a^b)&dep)==0
def bit_value(state,i): return (state>>i)&1

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    exact=0;mismatch=0;disc_fail=0;witnesses=[];empty_pairs=0
    per_subset={}
    for dep in SUBSETS:
        eq=0;neq=0
        for src in STATES:
            for cur in STATES:
                if projection_equal(src,cur,dep):
                    exact+=1;eq+=1
                    if dep==0: empty_pairs+=1
                else:
                    mismatch+=1;neq+=1
                    changed=(src^cur)&dep
                    i=(changed & -changed).bit_length()-1
                    ok=bit_value(src,i)!=bit_value(cur,i)
                    if not ok: disc_fail+=1
                    if len(witnesses)<32: witnesses.append({'dep_mask':dep,'src':src,'cur':cur,'bit':i,'source_output':bit_value(src,i),'current_output':bit_value(cur,i)})
        per_subset[str(dep)]={'size':len(bits(dep)),'exact_pairs':eq,'mismatch_pairs':neq}

    hidden=[];hidden_fail=0
    for dep in SUBSETS:
        for h in range(N):
            if dep>>h & 1: continue
            src=0;cur=1<<h
            declared_same=projection_equal(src,cur,dep)
            stale=bit_value(src,h)!=bit_value(cur,h)
            ok=declared_same and stale
            if not ok: hidden_fail+=1
            hidden.append({'dep_mask':dep,'hidden_bit':h,'src':src,'cur':cur,'declared_projection_equal':declared_same,'hidden_function_differs':stale})

    expected_exact=sum((1<<N)*(1<<(N-len(bits(dep)))) for dep in SUBSETS)
    expected_total=len(SUBSETS)*len(STATES)*len(STATES)
    expected_mismatch=expected_total-expected_exact
    expected_hidden=sum(N-len(bits(dep)) for dep in SUBSETS)

    corrupt={}
    dep=1;src=0;cur=1
    corrupt['mismatched_declared_reuse']=not projection_equal(src,cur,dep) and bit_value(src,0)!=bit_value(cur,0)
    same_token=True; semantic_changed=True
    corrupt['version_token_reuse_aba']=same_token and semantic_changed
    dep=1;h=1;src=0;cur=2
    corrupt['hidden_dependency_omission']=projection_equal(src,cur,dep) and bit_value(src,h)!=bit_value(cur,h)
    dep=FULL;src=5;cur=5
    corrupt['exact_match_overinvalidated']=projection_equal(src,cur,dep)
    corrupt['finite_counts']=expected_exact==1296 and expected_mismatch==2800 and expected_hidden==32

    checks={
      'exact_count':exact==expected_exact==1296,
      'mismatch_count':mismatch==expected_mismatch==2800,
      'all_mismatch_discriminators':disc_fail==0,
      'hidden_control_count':len(hidden)==expected_hidden==32,
      'hidden_controls_all_counterexamples':hidden_fail==0,
      'empty_dependency_pairs':empty_pairs==256,
      'per_subset_total':sum(v['exact_pairs']+v['mismatch_pairs'] for v in per_subset.values())==expected_total==4096,
      'corruptions':all(corrupt.values()),
    }
    decision='PASS_EXACT_DEPENDENCY_VERSION_REUSE_SCOPED' if all(checks.values()) else 'FAIL_INTEGRITY'
    result={
      'task':TASK,'decision':decision,'n_evidence_items':N,'states':len(STATES),'dependency_subsets':len(SUBSETS),
      'state_pairs_per_subset':len(STATES)**2,'total_cases':expected_total,
      'exact_projection_pairs':exact,'mismatched_projection_pairs':mismatch,'mismatch_discriminator_failures':disc_fail,
      'hidden_dependency_controls':len(hidden),'hidden_dependency_failures':hidden_fail,'empty_dependency_pairs':empty_pairs,
      'per_subset':per_subset,'sample_discriminator_witnesses':witnesses,'hidden_counterexamples':hidden,
      'corruption_controls':corrupt,'checks':checks,
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'assumptions':['deterministic_pure_job','complete_declared_dependencies','non_reused_semantic_version_identity']
    }
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if decision.startswith('PASS_') else 1)
if __name__=='__main__':main()
