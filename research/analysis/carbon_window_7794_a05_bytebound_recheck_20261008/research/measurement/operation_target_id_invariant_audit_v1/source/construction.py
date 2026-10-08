import json
from generator import generate
from analyze import analyze
rows=generate(113320260918002,units=2)
r=analyze(rows)
assert r['full_conflicting_groups']==0
assert r['id_invariant_conflicting_groups']>=1
assert all(w['distinct_acceptable_sets']>=2 for w in r['id_invariant_witnesses'])
print(json.dumps({'pass':True,'full_conflicting_groups':r['full_conflicting_groups'],'id_invariant_conflicting_groups':r['id_invariant_conflicting_groups']},sort_keys=True))
