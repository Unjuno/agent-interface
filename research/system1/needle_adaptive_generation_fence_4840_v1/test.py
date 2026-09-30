import importlib.util,pathlib,unittest
p=pathlib.Path(__file__).with_name("study.py")
s=importlib.util.spec_from_file_location("candidate",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FenceTests(unittest.TestCase):
 def test_matrix_is_64_balanced_rows(self):
  x=m.run();self.assertEqual(len(x["rows"]),64);self.assertEqual({z:sum(r["stratum"]==z for r in x["rows"]) for z in m.STRATA},{z:8 for z in m.STRATA})
 def test_control_count(self):self.assertEqual(len(m.mutations()),15)
 def test_current_valid_is_proposal_only(self):self.assertEqual(m.envelope(m.proposal("CURRENT_VALID",0)),"ELIGIBLE_PROPOSAL_ONLY")
 def test_prior_generation_after_switch_yields(self):self.assertEqual(m.envelope(m.proposal("OLD_INFLIGHT_AFTER_SWITCH",0)),"YIELD")
 def test_delayed_old_reply_yields(self):self.assertEqual(m.envelope(m.proposal("DELAYED_OLD_REPLY",0)),"YIELD")
 def test_rollback_uses_monotone_new_generation(self):self.assertEqual((1,2),(m.run()["transition"]["previous_generation"],m.run()["transition"]["rollback_generation"]));self.assertEqual(m.envelope(m.proposal("REPLAYED_PRE_ROLLBACK_GENERATION",0)),"YIELD")
 def test_future_generation_yields(self):self.assertEqual(m.envelope(m.proposal("FUTURE_GENERATION",0)),"YIELD")
 def test_intent_scope_evidence_yield(self):
  self.assertTrue(all(m.envelope(m.proposal("INTENT_MISMATCH",i))=="YIELD" for i in range(8)))
  self.assertTrue(all(m.envelope(m.proposal("SCOPE_OR_EVIDENCE_MISMATCH",i))=="YIELD" for i in range(8)))
 def test_uncommitted_lineage_or_expired_calibration_yield(self):self.assertTrue(all(m.envelope(m.proposal("UPDATE_LINEAGE_OR_CALIBRATION_INVALID",i))=="YIELD" for i in range(8)))
 def test_confidence_only_admits_all_56_negative_rows(self):
  r=m.run()["rows"];self.assertEqual(sum(x["confidence_only"]!="YIELD" for x in r if x["stratum"]!="CURRENT_VALID"),56)
 def test_every_tamper_control_yields_without_mutation(self):
  c=m.mutations();self.assertGreaterEqual(len(c),12);self.assertTrue(all(m.envelope(x["proposal"])=="YIELD" for x in c))
if __name__=="__main__":unittest.main()
