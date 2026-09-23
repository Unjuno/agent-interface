import copy,json,sys
F=("explicit_request","target_bound","completion_observable","boundary_identity","retained_demonstration","is_compaction_operation")
L=json.load(open(sys.argv[1])); R=json.load(open(sys.argv[2])); tests={}
def count(X): return sum(all(c.get(k) is True for k in F) for c in X['candidates'])
base=count(L)
q=copy.deepcopy(L); q['candidates'][0].update(target_bound=True,boundary_identity=True,retained_demonstration=True,is_compaction_operation=True); tests['fabricated_generic_changes_eligibility']=count(q)!=base
q=copy.deepcopy(L); q['candidates'][3].update(explicit_request=True,target_bound=True,completion_observable=True,boundary_identity=True); tests['fabricated_natural_changes_eligibility']=count(q)!=base
q=copy.deepcopy(R); q['eligible_count']=1; tests['result_count_mutation_detected']=(q['eligible_count']!=base)
q=copy.deepcopy(R); q['decision']='PASS_CONTROLLED_COMPACTION_PRIMITIVE_AVAILABLE_SCOPED'; expected='PASS_CONTROLLED_COMPACTION_PRIMITIVE_AVAILABLE_SCOPED' if base else 'HOLD_NO_REPOSITORY_EVIDENCED_CONTROLLED_COMPACTION_PRIMITIVE'; tests['result_decision_mutation_detected']=(q['decision']!=expected)
tests['formal_count_consistent']=(R.get('eligible_count')==base)
out={'schema':'controlled-compaction-census-corruption-a2-v2','controls':tests,'pass':all(tests.values())};json.dump(out,open(sys.argv[3],'w'),indent=2,sort_keys=True);open(sys.argv[3],'a').write('\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['pass'] else 4)
