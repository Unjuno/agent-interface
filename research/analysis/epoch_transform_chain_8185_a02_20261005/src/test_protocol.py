import copy,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
import auditor,candidate
PUBLIC=json.loads((ROOT/"results/FORMAL_A02/public/corpus.json").read_text())
ORACLE=json.loads((ROOT/"results/FORMAL_A02/oracle/exact_worlds.json").read_text())

class ExactAffineProtocol(unittest.TestCase):
    def setUp(self): self.raw=candidate.run(PUBLIC)
    def test_fair_baseline_and_exact_oracle_gate(self):
        result=auditor.audit(PUBLIC,ORACLE,self.raw)
        self.assertEqual(result["disposition"],"PASS_METHOD_SCOPED",result["errors"])
        s=result["summary"]
        self.assertEqual(s["false_admissions"],0)
        self.assertEqual((s["invalid_controls"],s["invalid_fail_closed"]),(11,11))
        self.assertEqual(s["exact_safe_composed"],3)
        self.assertEqual(s["baseline_false_unknown_composed"],3)
        self.assertEqual(s["graph_false_unknown_composed"],0)
        self.assertGreaterEqual(s["composed_false_unknown_reduction"],.20)
        # The scalar comparator runs on every composed row; it is never refused for path length.
        rows={r["case_id"]:r for r in self.raw["rows"]}
        self.assertNotEqual(rows["INVERSE_SHEAR_PAIR_IDENTITY"]["baseline"]["decision"],"UNKNOWN")
    def test_oracle_detects_a_mapped_value_mutation(self):
        mutated=copy.deepcopy(self.raw); row=next(r for r in mutated["rows"] if r["case_id"]=="COMPOSE_NONCOMMUTING_ORDER")
        row["point_bounds"][0][0]+=1
        result=auditor.audit(PUBLIC,ORACLE,mutated)
        self.assertEqual(result["disposition"],"FAIL_METHOD")
        self.assertIn("COMPOSE_NONCOMMUTING_ORDER:point_mapping_mismatch",result["errors"])
    def test_oracle_detects_a_forbidden_region_false_admission(self):
        mutated=copy.deepcopy(self.raw); row=next(r for r in mutated["rows"] if r["case_id"]=="INVALID_FORBIDDEN_REGION_OVERLAP")
        row["decision"]="ADMIT"
        result=auditor.audit(PUBLIC,ORACLE,mutated)
        self.assertEqual(result["disposition"],"FAIL_METHOD")
        self.assertEqual(result["summary"]["invalid_fail_closed"],10)
    def test_inverse_shear_and_two_epoch_path_are_hand_checkable(self):
        result=auditor.audit(PUBLIC,ORACLE,self.raw)
        self.assertTrue(result["summary"]["inverse_shear_identity_verified"])
        self.assertEqual(result["summary"]["epoch_path"],[[7,8],[8,9]])
    def test_exact_world_matrices_are_not_in_candidate_input(self):
        for c in PUBLIC["cases"]:
            self.assertNotIn("kind",c)
            self.assertNotIn("expected_invalid",c)
            for edge in c["edges"]:
                self.assertNotIn("maps",edge)
                self.assertNotIn("_oracle_maps",edge)
                self.assertIn("bounds",edge)
                self.assertIn(edge["id"],ORACLE["worlds"][c["case_id"]]["edge_assignments"][0])

if __name__=="__main__": unittest.main()
