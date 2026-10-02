import copy,json,unittest
from pathlib import Path
import audit,candidate
ROOT=Path(__file__).parent
INPUT=json.loads((ROOT/'inputs.json').read_text(encoding='utf-8-sig'))
ORACLE=json.loads((ROOT/'oracle.json').read_text(encoding='utf-8-sig'))
RAW=candidate.run(INPUT)
class ContractTests(unittest.TestCase):
 def row(self,case,policy,raw=RAW):return next(r for r in raw['rows']if r['case_id']==case and r['policy']==policy)
 def test_exact_policy_case_matrix(self):self.assertEqual(len(RAW['rows']),18)
 def test_positive_budgeted_switch_beats_both_baselines(self):
  c=self.row('blocked_class_positive','class_aware');a=self.row('blocked_class_positive','coverage');b=self.row('blocked_class_positive','backtrack')
  self.assertEqual((c['decision'],c['route_id'],c['class_claim'],c['cost_used'],c['reached_goal'],c['revisits']),('SCOPED_SWITCH','lower_a','LOWER',6,True,0))
  self.assertEqual(a['route_attempts'],['upper_b','upper_c']);self.assertEqual(a['cost_used'],4);self.assertFalse(a['reached_goal']);self.assertEqual(a['revisits'],2)
  self.assertEqual(b['route_attempts'],['upper_b','upper_c']);self.assertEqual(b['cost_used'],6);self.assertFalse(b['reached_goal']);self.assertEqual(b['revisits'],2)
 def test_shared_prefix_retains_both_classes(self):
  c=INPUT['cases'][1];self.assertEqual(candidate.compatible(c['current_prefix'],c['routes'],INPUT['obstacle']),['LOWER','UPPER']);self.assertEqual(self.row('shared_prefix_ambiguous','class_aware')['decision'],'UNKNOWN_CLASS')
 def test_same_class_deceptive_branch_not_switch(self):self.assertEqual(self.row('same_class_deceptive_branch','class_aware')['decision'],'NO_DISTINCT_CLASS_SWITCH')
 def test_map_revision_invalidates_embedding(self):self.assertEqual(self.row('geometry_revision','class_aware')['events'],['INVALIDATE_EMBEDDING','YIELD'])
 def test_false_class_cue_yields(self):self.assertEqual(self.row('false_class_cue','class_aware')['decision'],'UNKNOWN_CLASS')
 def test_single_class_yields(self):self.assertEqual(self.row('single_class_graph','class_aware')['decision'],'SAFE_YIELD')
 def test_independent_raw_audit_passes(self):self.assertEqual(audit.audit(INPUT,ORACLE,RAW)['disposition'],'PASS_METHOD_SCOPED')
 def test_auditor_rejects_missing_policy_row(self):
  m=copy.deepcopy(RAW);m['rows'].pop();self.assertIn('row_coverage_or_identity',audit.audit(INPUT,ORACLE,m)['errors'])
 def test_auditor_rejects_ambiguous_prefix_claim(self):
  m=copy.deepcopy(RAW);r=next(x for x in m['rows']if x['case_id']=='shared_prefix_ambiguous'and x['policy']=='class_aware');r.update(decision='SCOPED_SWITCH',route_id='lower_a',class_claim='LOWER');self.assertTrue(audit.audit(INPUT,ORACLE,m)['errors'])
 def test_auditor_rejects_unsupported_false_cue(self):
  m=copy.deepcopy(RAW);r=next(x for x in m['rows']if x['case_id']=='false_class_cue'and x['policy']=='class_aware');r.update(route_id='lower_a',class_claim='LOWER');self.assertTrue(audit.audit(INPUT,ORACLE,m)['errors'])
 def test_auditor_rejects_stale_geometry_admission(self):
  m=copy.deepcopy(RAW);r=next(x for x in m['rows']if x['case_id']=='geometry_revision'and x['policy']=='class_aware');r.update(decision='SCOPED_SWITCH',route_id='lower_a',class_claim='LOWER',reached_goal=True);self.assertTrue(audit.audit(INPUT,ORACLE,m)['errors'])
 def test_auditor_rejects_privileged_label_leak(self):
  m=copy.deepcopy(RAW);r=next(x for x in m['rows']if x['case_id']=='blocked_class_positive'and x['policy']=='class_aware');r['oracle_class']='LOWER';self.assertTrue(audit.audit(INPUT,ORACLE,m)['errors'])
 def test_auditor_rejects_baseline_gain_mutation(self):
  m=copy.deepcopy(RAW);r=next(x for x in m['rows']if x['case_id']=='blocked_class_positive'and x['policy']=='backtrack');r.update(reached_goal=True,route_id='lower_a',revisits=0);self.assertTrue(audit.audit(INPUT,ORACLE,m)['errors'])
if __name__=='__main__':unittest.main(verbosity=2)
