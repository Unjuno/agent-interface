"""Pre-freeze construction and auditor corruption controls for Issue #6081."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+".py"));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
candidate=load("candidate");auditor=load("audit")
DATA=json.loads((ROOT/"cases.json").read_text(encoding="utf-8"))
RESULT=candidate.run(DATA)

class ConstructionTests(unittest.TestCase):
    def test_all_declared_dispositions_and_audit(self):
        result=auditor.audit(DATA,RESULT)
        self.assertEqual(result["disposition"],"PASS_METHOD_SCOPED",result["errors"])
        self.assertGreaterEqual(len(result["independent_improvements"]),3)

    def test_convex_hull_and_finite_lattice_are_separate(self):
        row=next(x for x in RESULT["results"] if x["id"]=="eight_way_convex_but_lattice_gap")
        self.assertEqual(row["reachability"],"RELAXATION_ONLY")
        self.assertEqual(next(x for x in auditor.audit(DATA,RESULT)["summary"] if x["id"]==row["id"])["reachability"],"RELAXATION_ONLY")

    def test_final_release_is_required_and_checked(self):
        bad=copy.deepcopy(RESULT);row=next(x for x in bad["results"] if x["id"]=="four_way_exact_one_slot_release");row["release_at_tick"]=None
        self.assertNotEqual(auditor.audit(DATA,bad)["disposition"],"PASS_METHOD_SCOPED")

    def test_illegal_key_is_rejected(self):
        bad=copy.deepcopy(RESULT);row=next(x for x in bad["results"] if x["id"]=="four_way_exact_one_slot_release");row["policies"]["C_ERROR_CARRY"]["actions"]=["DIAGONAL_MAGIC"]
        self.assertNotEqual(auditor.audit(DATA,bad)["disposition"],"PASS_METHOD_SCOPED")

    def test_outside_hull_and_unavailable_key_refuse(self):
        for cid in ("outside_four_way_convex_hull","unavailable_north_action"):
            row=next(x for x in RESULT["results"] if x["id"]==cid)
            self.assertEqual(row["disposition"],"REFUSE_UNREPRESENTABLE")
            self.assertEqual(row["policies"],{})

    def test_nonlinear_calibration_and_release_controls_refuse(self):
        for cid in ("calibration_mismatch","nonlinear_collision_transfer_control","release_path_missing","release_deadline_too_short"):
            row=next(x for x in RESULT["results"] if x["id"]==cid)
            self.assertTrue(row["disposition"].startswith("REFUSE_"))
            self.assertEqual(row["policies"],{})

if __name__=="__main__":unittest.main(verbosity=2)
