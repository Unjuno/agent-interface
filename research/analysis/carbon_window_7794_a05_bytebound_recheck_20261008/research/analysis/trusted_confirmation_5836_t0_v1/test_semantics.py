import importlib.util, json, pathlib, unittest
HERE=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location("candidate",HERE/"candidate.py"); candidate=importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
aspec=importlib.util.spec_from_file_location("audit",HERE/"audit.py"); audit=importlib.util.module_from_spec(aspec); aspec.loader.exec_module(audit)
fixture=json.loads((HERE/"fixture.json").read_text(encoding="utf-8-sig"))
class SemanticsTests(unittest.TestCase):
 def test_complete_policy_matrix_matches_independent_oracle(self):
  f=audit.materialize(fixture); raw=candidate.run(f); self.assertEqual(audit.check(f,raw),[])
 def test_trusted_policy_rejects_all_unauthorized_effects(self):
  f=audit.materialize(fixture); raw=candidate.run(f); trusted=[r for r in raw["rows"] if r["policy"]=="TRUSTED_SINGLE_USE"]
  for row in trusted:
   truth=next(q["truth"] for q in f["requests"] if q["id"]==row["request_id"])
   if truth=="DENY": self.assertEqual(row["effect_attempts"],0,row["request_id"])
 def test_weaker_baseline_controls_are_observable(self):
  raw=candidate.run(audit.materialize(fixture)); rows={(r["policy"],r["request_id"]):r for r in raw["rows"]}
  self.assertEqual(rows[("SCREEN_TEXT","page-forgery")]["effect_attempts"],1)
  self.assertEqual(rows[("SCREEN_TEXT","tool-forgery")]["effect_attempts"],1)
  self.assertEqual(rows[("BOUND_REPLAYABLE","target-swap")]["effect_attempts"],1)
  self.assertEqual(rows[("BOUND_REPLAYABLE","replay-second")]["effect_attempts"],1)
 def test_auditor_rejects_six_frozen_mutations(self):
  f=audit.materialize(fixture); raw=candidate.run(f); c=audit.mutation_controls(f,raw)
  self.assertEqual(len(c),6); self.assertTrue(all(x["detected"] for x in c))
 def test_lost_response_stays_unknown_and_consumes_receipt(self):
  raw=candidate.run(audit.materialize(fixture)); rows={(r["policy"],r["request_id"]):r for r in raw["rows"]}
  self.assertEqual(rows[("TRUSTED_SINGLE_USE","lost-response-first")]["effect_outcome"],"UNKNOWN")
  self.assertEqual(rows[("TRUSTED_SINGLE_USE","lost-response-retry")]["effect_attempts"],0)
  self.assertEqual(rows[("TRUSTED_SINGLE_USE","safe-release")]["effect_attempts"],1)
if __name__=="__main__": unittest.main(verbosity=2)
