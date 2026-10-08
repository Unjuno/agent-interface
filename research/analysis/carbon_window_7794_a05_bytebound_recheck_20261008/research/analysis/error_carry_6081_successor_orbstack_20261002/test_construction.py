import json, unittest
from fractions import Fraction as F
from pathlib import Path
import candidate

ROOT=Path(__file__).parent
SPEC=json.loads((ROOT/"fixture.json").read_text())

class Construction(unittest.TestCase):
    def test_fixture_dimensions(self):
        self.assertEqual(len(SPEC["cases"]),10)
        self.assertEqual(set(SPEC["action_sets"]),{"4way","8way"})
    def test_action_tables_explicit(self):
        self.assertEqual(SPEC["action_sets"]["4way"],[[0,0],[1,0],[0,1],[-1,0],[0,-1]])
        self.assertEqual(len(SPEC["action_sets"]["8way"]),9)
    def test_hull_and_finite_horizon_control(self):
        self.assertFalse(candidate.inside_hull((F(1),F(1)),"4way"))
        self.assertTrue(candidate.inside_hull((F(1),F(1)),"8way"))
        self.assertTrue(candidate.inside_hull((F(1,3),F(0)),"4way"))
    def test_baselines_equivalent_stationary_exactly(self):
        for label, actions in SPEC["action_sets"].items():
            aa=[tuple(map(F,p)) for p in actions]
            for c in SPEC["cases"]:
                cc=dict(c,action_set=label)
                self.assertEqual(candidate.simulate(cc,aa,"A_HORIZON_NEAREST"),
                                 candidate.simulate(cc,aa,"B_SLOT_NEAREST"))
    def test_controls_fail_closed_and_release(self):
        c=dict(SPEC["cases"][-1],action_set="4way")
        r=candidate.simulate(c,[tuple(map(F,p)) for p in SPEC["action_sets"]["4way"]],"C_ERROR_CARRY")
        self.assertEqual(r["status"],"REFUSE_UNKNOWN_CALIBRATION")
        self.assertTrue(r["release"])
    def test_candidate_raw_schema_without_execution(self):
        self.assertTrue(callable(candidate.main))
        self.assertEqual(set(SPEC["cases"][0]),{"id","intent","horizon","max_switches","box"})

if __name__=="__main__": unittest.main()
