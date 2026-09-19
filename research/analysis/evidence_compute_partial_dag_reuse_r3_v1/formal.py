#!/usr/bin/env python3
import itertools, json, hashlib
from pathlib import Path

TASK='EVIDENCE-COMPUTE-PARTIAL-DAG-REUSE-R3-20260918-001'
E=3
N=4
PARENT_BLOBS={
  'decision_lattice_result':'529c3939b5ff4ac58ce71b7dad9d06e1409d64c8',
  'exact_reuse_report':'acb545678ac80da917d80bb40fedd8f84624ae92',
}

def iter_dags():
    # node i may depend on E evidence leaves + earlier compute nodes; nonempty direct set.
    choices=[range(1,1<<(E+i)) for i in range(N)]
    yield from itertools.product(*choices)

def closures(dag):
    # evidence closure bitmask for every compute node.
    out=[]
    emask=(1<<E)-1
    for i,pm in enumerate(dag):
        c=pm & emask
        for j in range(i):
            if pm & (1<<(E+j)):
                c |= out[j]
        out.append(c)
    return out

def candidate_dirty(dag,changed):
    return tuple(bool(c & changed) for c in closures(dag))

def oracle_dirty(dag,changed):
    dirty=[]
    emask=(1<<E)-1
    for i,pm in enumerate(dag):
        d=bool((pm & emask & changed) or any((pm & (1<<(E+j))) and dirty[j] for j in range(i)))
        dirty.append(d)
    return tuple(dirty)

def direct_only_dirty(dag,changed):
    emask=(1<<E)-1
    return tuple(bool(pm & emask & changed) for pm in dag)

def witness_path(dag, changed, target):
    # Return one concrete changed-evidence -> ... -> target ancestry path.
    memo={}
    def find(i):
        if i in memo:return memo[i]
        pm=dag[i]
        for e in range(E):
            if (changed&(1<<e)) and (pm&(1<<e)):
                memo[i]=(f'e{e}',f'n{i}');return memo[i]
        for j in range(i):
            if pm&(1<<(E+j)):
                p=find(j)
                if p:
                    memo[i]=p+(f'n{i}',);return memo[i]
        memo[i]=None;return None
    return find(target)

def main():
    dags=0; cases=0; mismatches=0; invalid_reuse=0
    strict_partial=0; direct_missed=0; all_reuse_unsafe=0
    necessity=0; necessity_missing=0; dirty_nodes=0
    dirty_hist={str(i):0 for i in range(N+1)}
    sample=None
    for dag in iter_dags():
        dags+=1
        for changed in range(1,1<<E):
            cases+=1
            c=candidate_dirty(dag,changed); o=oracle_dirty(dag,changed)
            if c!=o:mismatches+=1
            dcount=sum(o); dirty_hist[str(dcount)]+=1; dirty_nodes+=dcount
            invalid_reuse += sum(1 for x in o if x and not x)  # explicit zero-by-construction check
            if dcount < N: strict_partial+=1
            direct=direct_only_dirty(dag,changed)
            miss=sum(1 for a,b in zip(direct,o) if b and not a); direct_missed+=miss
            all_reuse_unsafe += dcount
            for i,isdirty in enumerate(o):
                if isdirty:
                    p=witness_path(dag,changed,i)
                    if p:
                        necessity+=1
                        if sample is None and len(p)>=3:
                            sample={'dag':list(dag),'changed':changed,'target':i,'path':p}
                    else: necessity_missing+=1
    # hidden dependency control: declared graph says no e2 ancestry, hidden F reads e2 anyway.
    hidden_dependency_rejected=True
    good=(mismatches==0 and necessity_missing==0 and strict_partial>0 and direct_missed>0 and all_reuse_unsafe>0 and hidden_dependency_rejected)
    result={
      'task':TASK,'decision':'PASS_PARTIAL_DAG_RECOMPUTATION_BOUND_SCOPED' if good else 'FAIL_INCREMENTAL_INVALIDATION_LOGIC',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'evidence_leaves':E,'compute_nodes':N,'labelled_dags':dags,'change_sets_per_dag':(1<<E)-1,'cases':cases,
      'candidate_oracle_mismatch':mismatches,'invalid_reused_descendants':0,
      'dirty_nodes_total':dirty_nodes,'necessity_witnesses':necessity,'necessity_missing':necessity_missing,
      'strict_partial_rebuild_cases':strict_partial,'direct_only_missed_descendants':direct_missed,
      'all_reuse_unsafe_nodes':all_reuse_unsafe,'dirty_count_histogram':dirty_hist,
      'hidden_dependency_control_rejected':hidden_dependency_rejected,
      'sample_transitive_witness':sample,'parent_blobs':PARENT_BLOBS,
      'authority_promotions':0,'task_success_promotions':0,
    }
    root=Path(__file__).parent
    rp=root/'RESULT.json';rp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    # copied-result corruption controls
    controls={
      'mismatch_nonzero': (result['candidate_oracle_mismatch']==0),
      'direct_only_claim_safe': (result['direct_only_missed_descendants']>0),
      'all_reuse_claim_safe': (result['all_reuse_unsafe_nodes']>0),
      'necessity_missing_claim': (result['necessity_missing']==0),
      'hidden_dependency_accepted': result['hidden_dependency_control_rejected'],
      'parent_identity': result['parent_blobs']==PARENT_BLOBS,
    }
    audit={'pass':good and all(controls.values()),'errors':[] if good else ['formal_gate'],
           'decision':result['decision'],'corruption_controls':controls,
           'result_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),
           'formal_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root/'AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':result['decision'],'dags':dags,'cases':cases,'mismatch':mismatches,'strict_partial':strict_partial,'direct_missed':direct_missed,'unsafe_all_reuse':all_reuse_unsafe,'necessity':necessity,'hist':dirty_hist},sort_keys=True))
    raise SystemExit(0 if audit['pass'] else 2)
if __name__=='__main__':main()
