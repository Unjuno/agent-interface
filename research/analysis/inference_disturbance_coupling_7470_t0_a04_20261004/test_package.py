import importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=json.loads((HERE/"spec.json").read_text())
spec=importlib.util.spec_from_file_location("seam_candidate",HERE/"candidate.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class SeamTests(unittest.TestCase):
    def test_four_intact_rotations_and_fixed_margins(self):
        r=mod.run(SPEC)["shifts"]; self.assertEqual(len(r),4)
        for row in r:
            self.assertEqual(sorted(row["latency_period"]),sorted(SPEC["latency_period"]))
            self.assertEqual(row["disturbance_period"],SPEC["disturbance_period"])
            self.assertEqual(row["interaction"]["termination_release_tick"],20)
    def test_each_arm_executes_the_period_seam_once(self):
        for row in mod.run(SPEC)["shifts"]:
            for arm in ("null","interaction"):
                ev=row[arm]["events"]; self.assertEqual(len(ev),8)
                self.assertEqual([x["event"] for x in ev if x["is_seam"]],[4])
                self.assertEqual(ev[4]["latency"],ev[0]["latency"])
                self.assertEqual(ev[4]["severity"],ev[0]["severity"])
    def test_null_invariant_interaction_phase_sensitive(self):
        rows=mod.run(SPEC)["shifts"]
        self.assertEqual(len({tuple(x["null"]["state_trace"]) for x in rows}),1)
        self.assertGreater(len({x["interaction"]["peak_state"] for x in rows}),1)
if __name__=="__main__": unittest.main()
