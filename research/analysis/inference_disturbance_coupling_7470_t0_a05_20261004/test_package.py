import importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; S=json.loads((HERE/"spec.json").read_text()); sp=importlib.util.spec_from_file_location("pearson_candidate",HERE/"candidate.py"); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
class PearsonTests(unittest.TestCase):
 def test_known_pearson_fixture(self): self.assertEqual([r["pearson_r"] for r in m.run(S)["shifts"]],S["expected_pearson_r"])
 def test_two_period_seam_and_fixed_marginals(self):
  for r in m.run(S)["shifts"]:
   self.assertEqual(sorted(r["latency_period"]),sorted(S["latency_period"]))
   self.assertEqual([e["event"] for e in r["interaction"]["events"] if e["is_seam"]],[4])
   self.assertEqual(r["interaction"]["termination_release_tick"],20)
 def test_null_and_planted_response(self):
  rows=m.run(S)["shifts"]; self.assertEqual(len({tuple(x["null"]["state_trace"]) for x in rows}),1); self.assertGreater(len({x["interaction"]["peak_state"] for x in rows}),1)
if __name__=="__main__": unittest.main()
