import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).parent
s=importlib.util.spec_from_file_location('candidate',ROOT/'candidate.py'); c=importlib.util.module_from_spec(s); s.loader.exec_module(c)
F=json.loads((ROOT/'fixture.json').read_text(encoding='utf-8-sig')); M=json.loads((ROOT/'model.json').read_text(encoding='utf-8-sig'))
class Construction(unittest.TestCase):
 def test_valid_pairs_under_dynamic_contexts(self):
  for p in F['valid']: self.assertEqual('VALID',c.validate(p['source'],p['target'],M,'m','f')['status'],p['id'])
 def test_each_semantics_mutation_has_counterexample(self):
  by={x['id']:x for x in F['valid']}
  for x in F['mutations']:
   r=c.validate(by[x['source_id']]['source'],x['target'],M,'m','f'); self.assertEqual('COUNTEREXAMPLE',r['status'],x['id']); self.assertIsNotNone(r['counterexample'])
 def test_nominal_baseline_misses_dropped_guard_but_stale_context_detects(self):
  by={x['id']:x for x in F['valid']}; x=F['mutations'][0]; p=by[x['source_id']]; code=c.expand(p['source']['program'],M)
  nominal={'initial_state':{'active_target':'editor','fresh':True},'transition_after':None,'transition_state':None,'cancel_after':None}
  self.assertEqual(c.src(code,nominal),c.tgt(x['target'],nominal))
  stale={'initial_state':{'active_target':'editor','fresh':False},'transition_after':None,'transition_state':None,'cancel_after':None}
  self.assertNotEqual(c.src(code,stale),c.tgt(x['target'],stale))
 def test_oversized_repeat_is_unknown_without_certificate(self):
  u=F['unknown']; r=c.validate(u['source'],u['target'],M,'m','f'); self.assertEqual('UNKNOWN',r['status']); self.assertIsNone(r['certificate'])
 def test_counterexample_context_count_is_actual_replay_count(self):
  by={x['id']:x for x in F['valid']}; x=F['mutations'][0]
  r=c.validate(by[x['source_id']]['source'],x['target'],M,'m','f')
  self.assertEqual('COUNTEREXAMPLE',r['status']); self.assertEqual(1,r['contexts_checked'])
 def test_candidate_allocation_is_A05(self):
  self.assertEqual('UNJUNO-7827-TV-A05-20261005-01',c.ALLOCATION)
if __name__=='__main__': unittest.main(verbosity=2)
