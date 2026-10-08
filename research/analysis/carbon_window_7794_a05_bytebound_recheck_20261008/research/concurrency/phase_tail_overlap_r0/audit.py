from itertools import product, permutations
import json, pathlib, sys

root=pathlib.Path(__file__).parent
result=json.loads((root/'RESULT.json').read_text())

def score(order,p,q):
    elapsed=0
    finishes=[]
    for j in order:
        elapsed += p[j]
        finishes.append(elapsed+q[j])
    return max(finishes)

def canonical(q):
    # Independent construction: stable insertion by descending tail.
    order=[]
    for j,val in enumerate(q):
        k=0
        while k < len(order) and q[order[k]] >= val:
            k += 1
        order.insert(k,j)
    return tuple(order)

errors=[]
recomputed=0
strict_by_n={}
for n in result['ranges']['n']:
    strict=0
    for p in product(result['ranges']['p'], repeat=n):
        for q in product(result['ranges']['q'], repeat=n):
            recomputed += 1
            got=score(canonical(q),p,q)
            best=min(score(o,p,q) for o in permutations(range(n)))
            if got != best:
                errors.append({"n":n,"p":p,"q":q,"got":got,"best":best})
                if len(errors)>=5: break
            if got < sum(p)+sum(q): strict += 1
        if errors: break
    strict_by_n[str(n)]=strict
    if errors: break
checks={
  "formal_invocations_one":result.get('formal_invocations')==1,
  "decision_pass":result.get('decision')=='PASS_PHASE_LEVEL_OVERLAP_SCOPED',
  "case_count_exact":result.get('total_cases')==37440==recomputed,
  "reported_counterexamples_zero":result.get('counterexamples')==0,
  "independent_counterexamples_zero":len(errors)==0,
  "strict_gain_each_n":all(v>0 for v in strict_by_n.values()) and len(strict_by_n)==4,
}
out={"pass":all(checks.values()),"checks":checks,"recomputed_cases":recomputed,"strict_by_n":strict_by_n,"errors":errors}
print(json.dumps(out,indent=2,sort_keys=True))
sys.exit(0 if out['pass'] else 1)
