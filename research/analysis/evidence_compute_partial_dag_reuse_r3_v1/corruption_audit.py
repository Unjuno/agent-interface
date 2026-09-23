#!/usr/bin/env python3
import copy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).parent
PARENTS={'decision_lattice_result':'529c3939b5ff4ac58ce71b7dad9d06e1409d64c8','exact_reuse_report':'acb545678ac80da917d80bb40fedd8f84624ae92'}

def verify(r):
    errors=[]
    if r.get('decision')!='PASS_PARTIAL_DAG_RECOMPUTATION_BOUND_SCOPED':errors.append('decision')
    if r.get('labelled_dags')!=205065 or r.get('cases')!=1435455:errors.append('domain')
    if r.get('candidate_oracle_mismatch')!=0:errors.append('mismatch')
    if r.get('necessity_missing')!=0 or r.get('necessity_witnesses')!=r.get('dirty_nodes_total'):errors.append('necessity')
    if not (r.get('strict_partial_rebuild_cases',0)>0):errors.append('partial')
    if not (r.get('direct_only_missed_descendants',0)>0):errors.append('direct')
    if not (r.get('all_reuse_unsafe_nodes',0)>0):errors.append('allreuse')
    if not r.get('hidden_dependency_control_rejected'):errors.append('hidden')
    if r.get('parent_blobs')!=PARENTS:errors.append('parents')
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0:errors.append('invocation')
    return errors

def main():
    r=json.loads((ROOT/'RESULT.json').read_text())
    assert not verify(r)
    tests=[]
    q=copy.deepcopy(r);q['candidate_oracle_mismatch']=1;tests.append(('mismatch',q))
    q=copy.deepcopy(r);q['direct_only_missed_descendants']=0;tests.append(('direct_only_launder',q))
    q=copy.deepcopy(r);q['all_reuse_unsafe_nodes']=0;tests.append(('all_reuse_launder',q))
    q=copy.deepcopy(r);q['necessity_missing']=1;tests.append(('necessity_gap',q))
    q=copy.deepcopy(r);q['hidden_dependency_control_rejected']=False;tests.append(('hidden_dependency',q))
    q=copy.deepcopy(r);q['parent_blobs']['decision_lattice_result']='0'*40;tests.append(('parent_identity',q))
    out={name:bool(verify(q)) for name,q in tests}
    result={'pass':all(out.values()),'corruption_controls':out,'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'CORRUPTION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True));raise SystemExit(0 if result['pass'] else 2)
if __name__=='__main__':main()
