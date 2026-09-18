import copy,json
from audit import audit,evaluate
L=json.load(open('ledger.json')); R=evaluate(L); tests={}
# Each corruption must be detected without changing the frozen source ledger.
for name,mut in [
 ('count',lambda x: x.update(admissible_pairs=1)),
 ('decision',lambda x: x.update(decision='PASS_RETAINED_PGWS_COMPACTION_BENEFIT_IDENTIFIABLE_SCOPED')),
 ('digest',lambda x: x.update(ledger_sha256='0'*64)),
 ('invocation',lambda x: x.update(formal_invocations=2)),
 ('families',lambda x: x.update(families_inspected=2)),
]:
    q=copy.deepcopy(R); mut(q); tests[name]=not audit(L,q)['pass']
# Ledger-side corruptions must make the recomputed result internally invalid or change admissibility.
q=copy.deepcopy(L); q['rows'][0]['gates']['compaction_boundary']='PASS'; q['rows'][0]['gates']['current_evidence']='PASS'; q['rows'][0]['gates']['history_pre_compaction']='PASS'; q['rows'][0]['gates']['model_effort']='PASS'; q['rows'][0]['gates']['task_decision']='PASS'; q['rows'][0]['gates']['prompt_capability']='PASS'; q['rows'][0]['gates']['session_cache_policy']='PASS'; tests['gate_flip_changes_count']=evaluate(q)['admissible_pairs']!=R['admissible_pairs']
q=copy.deepcopy(L); q['rows'][1]['sources'][0]['git_blob']='bad'; tests['bad_source']=bool(evaluate(q)['errors'])
out={'schema':'pgws-compaction-identifiability-corruption-v1','controls':tests,'pass':all(tests.values())}; print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 4)
