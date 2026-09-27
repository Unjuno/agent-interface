import copy,json,sys
from audit import F
L=json.load(open(sys.argv[1])); R=json.load(open(sys.argv[2])); tests={}
def recompute(X):
    elig=[c['id'] for c in X['candidates'] if all(c.get(k) is True for k in F)]
    return len(elig)
q=copy.deepcopy(L); q['candidates'][0].update(target_bound=True,boundary_identity=True,retained_demonstration=True,is_compaction_operation=True); tests['fabricated_generic_changes_eligibility']=recompute(q)!=recompute(L)
q=copy.deepcopy(L); q['candidates'][3].update(explicit_request=True,target_bound=True,completion_observable=True,boundary_identity=True); tests['fabricated_natural_changes_eligibility']=recompute(q)!=recompute(L)
tests['formal_count_consistent']=(R.get('eligible_count')==recompute(L))
out={'schema':'controlled-compaction-census-corruption-a2-v1','controls':tests,'pass':all(tests.values())};json.dump(out,open(sys.argv[3],'w'),indent=2,sort_keys=True);open(sys.argv[3],'a').write('\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['pass'] else 4)
