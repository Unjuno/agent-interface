from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    r=json.loads((ROOT/'FORMAL_RESULT.json').read_text());errors=[]
    if r.get('formal_invocations')!=1 or r.get('reruns')!=0:errors.append('invocation')
    if r.get('bounded_random_cases')!=500000 or r.get('ns_stress_cases')!=100000:errors.append('coverage')
    if r.get('bounded_old_set_mismatches')!=0:errors.append('old_set_mismatch')
    if r.get('pointwise_oracle_mismatches')!=0:errors.append('pointwise_mismatch')
    if r.get('ns_invariant_errors')!=0:errors.append('ns_invariant')
    parent=(ROOT/'parent_candidate.py').read_bytes()
    blob=hashlib.sha1(f'blob {len(parent)}\0'.encode()+parent).hexdigest()
    if blob!='0482cf4c08b8c04d524a3eac11b798f07f0e0524':errors.append('parent_blob')
    tree=ast.parse((ROOT/'interval_candidate.py').read_text())
    bad=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {'range','set','frozenset'}:bad.append(node.func.id)
    if bad:errors.append('duration_materialization')
    controls=[]
    for key in ['bounded_old_set_mismatches','pointwise_oracle_mismatches','ns_invariant_errors']:
        x=dict(r);x[key]=1;controls.append(x[key]!=0)
    x=dict(r);x['formal_invocations']=2;controls.append(x['formal_invocations']!=1)
    x=dict(r);x['bounded_random_cases']=499999;controls.append(x['bounded_random_cases']!=500000)
    if not all(controls):errors.append('corruption_control')
    out={'task':r['task'],'pass':not errors,'errors':errors,'decision':r['decision'] if not errors else 'FAIL_INTEGRITY',
         'corruption_controls':{'passed':sum(controls),'total':len(controls)},
         'result_sha256':sha(ROOT/'FORMAL_RESULT.json'),
         'parent_git_blob':blob,'interval_candidate_sha256':sha(ROOT/'interval_candidate.py')}
    p=ROOT/'AUDIT.json'
    if p.exists():raise SystemExit('AUDIT exists')
    p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
