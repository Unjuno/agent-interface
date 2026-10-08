import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location("faded_candidate",ROOT/"candidate.py")
candidate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class FadedDemonstrationConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads((ROOT/"fixtures.json").read_text())
        self.rows=[candidate.evaluate(c) for c in self.fixture["cases"]]

    def audit(self,rows):
        with tempfile.TemporaryDirectory() as tmp:
            raw=pathlib.Path(tmp)/"raw.json"
            out=pathlib.Path(tmp)/"audit.json"
            raw.write_text(json.dumps({"rows":rows}))
            p=subprocess.run([sys.executable,str(ROOT/"auditor.py"),str(ROOT/"fixtures.json"),str(ROOT/"oracle.json"),str(raw),str(out)],capture_output=True,text=True)
            return p.returncode,json.loads(out.read_text())

    def test_clean_candidate_independently_reconstructs(self):
        rc,report=self.audit(self.rows)
        self.assertEqual((rc,report["status"],report["errors"]),(0,"PASS_METHOD_SCOPED",[]))

    def test_uncertainty_false_success_wrong_target_never_teach(self):
        by={r["case_id"]:r for r in self.rows}
        for case in ("uncertain-effect","wrong-target","stale-generation","false-success-claim"):
            self.assertFalse(by[case]["teaching_step_offered"])
            self.assertEqual(by[case]["statement"],"UNKNOWN_NOT_DEMONSTRATED")

    def test_irreversible_ambiguous_and_optout_not_offered(self):
        by={r["case_id"]:r for r in self.rows}
        for case in ("irreversible-step","ambiguous-target","opt-out"):
            self.assertFalse(by[case]["teaching_step_offered"])
        self.assertTrue(by["opt-out"]["safe_completion"])

    def test_stale_target_is_not_reused_and_exit_choices_always_exist(self):
        for row in self.rows:
            self.assertFalse(row["coordinate_reused"])
            self.assertTrue(row["skip_available"])
            self.assertTrue(row["stop_available"])
            self.assertFalse(row["action_authority_granted"])

    def test_mutations_are_rejected(self):
        mutations=[]
        bad=json.loads(json.dumps(self.rows)); bad[0]["statement"]="UNKNOWN_NOT_DEMONSTRATED"; bad[8]["effect_for_task"]=True; mutations.append(bad)
        bad=json.loads(json.dumps(self.rows)); bad[2]["teaching_step_offered"]=True; mutations.append(bad)
        bad=json.loads(json.dumps(self.rows)); bad[3]["coordinate_reused"]=True; mutations.append(bad)
        bad=json.loads(json.dumps(self.rows)); bad[0]["skip_available"]=False; mutations.append(bad)
        bad=json.loads(json.dumps(self.rows)); bad[4]["safe_completion"]=True; mutations.append(bad)
        for raw in mutations:
            rc,_=self.audit(raw)
            self.assertNotEqual(rc,0)


if __name__=="__main__": unittest.main()
