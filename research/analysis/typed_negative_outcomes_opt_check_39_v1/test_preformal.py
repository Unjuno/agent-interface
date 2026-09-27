"""Frozen construction controls, executed before formal test."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
CANDIDATE=HERE/"candidate.py"
AUDIT=HERE/"audit.py"
MARKER="PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED"
CONTROLS={
    "stale_success":('value = ("FAILED_UNKNOWN", False, "NEW_OBSERVATION")','value = ("SUCCEEDED", False, "NONE")'),
    "authority_success":('value = ("AUTHORITY_REQUIRED", False, "FOCUS_OR_LEASE")','value = ("SUCCEEDED", False, "NONE")'),
    "retry_nonblocked":('elif e["blocked"] is True:\n        value = ("BLOCKED", budget > 0, "UNBLOCK_OR_WAIT")','elif e["blocked"] is True:\n        value = ("BLOCKED", budget > 0, "UNBLOCK_OR_WAIT")\n    elif e["fresh"] is True:\n        value = ("NO_ACTION", True, "NONE")'),
    "row_count":('if len(rows)!=384: fail("row_count",len(rows))','if len(rows)!=385: fail("row_count",len(rows))'),
    "outcome_count":('if counts!=EXPECTED_COUNTS: fail("outcome_counts",counts)','if counts!={}: fail("outcome_counts",counts)'),
    "oracle":('if e["fresh"] is not True: r=("FAILED_UNKNOWN",False,"NEW_OBSERVATION")','if e["fresh"] is not True: r=("SUCCEEDED",False,"NONE")'),
}

class OptimizationControls(unittest.TestCase):
    def invoke(self, mode, candidate=CANDIDATE):
        env=None
        if mode=="opt_flag": args=[sys.executable,"-O",str(candidate)]
        elif mode=="env_opt":
            env=os.environ.copy(); env["PYTHONOPTIMIZE"]="1"; args=[sys.executable,str(candidate)]
        else: args=[sys.executable,str(candidate)]
        return subprocess.run(args,capture_output=True,text=True,env=env)

    def test_valid_exact_equivalence_each_mode(self):
        for mode in ("normal","opt_flag","env_opt"):
            result=self.invoke(mode)
            self.assertEqual(result.returncode,0,(mode,result.stderr,result.stdout))
            self.assertIn(MARKER,result.stdout)

    def test_decision_gates_are_not_assert_statements(self):
        source=CANDIDATE.read_text(encoding="utf-8")
        self.assertNotIn("assert ",source)
        self.assertIn("if actual != expected",source)
        self.assertIn("if digest!=EXPECTED_DIGEST",source)

    def test_raw_auditor_does_not_depend_on_assertions(self):
        source=AUDIT.read_text(encoding="utf-8")
        self.assertNotIn("assert ",source)
        self.assertIn("def check(condition, label, errors):",source)
        self.assertIn("if not condition:",source)
        self.assertIn("errors.append(label)",source)

    def test_each_mutation_is_rejected_in_all_modes(self):
        original=CANDIDATE.read_text(encoding="utf-8")
        for name,(before,after) in CONTROLS.items():
            self.assertIn(before,original,name)
            mutated=original.replace(before,after,1)
            self.assertNotEqual(mutated,original,name)
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/"candidate.py"
                path.write_text(mutated,encoding="utf-8")
                for mode in ("normal","opt_flag","env_opt"):
                    result=self.invoke(mode,path)
                    self.assertNotEqual(result.returncode,0,(name,mode,result.stdout,result.stderr))
                    self.assertNotIn(MARKER,result.stdout,(name,mode,result.stdout))

    def test_budget_monotonicity_corruption_rejected_in_all_modes(self):
        code=(
            "import runpy; ns=runpy.run_path(" + repr(str(CANDIDATE)) + "); "
            "ns['validate_budget_monotonicity']("
            "{'outcome':'SUCCEEDED','retryable':False},"
            "{'outcome':'BLOCKED','retryable':True},{'probe':'hard-outcome'})"
        )
        for mode in ("normal","opt_flag","env_opt"):
            env=None
            args=[sys.executable,"-c",code]
            if mode=="opt_flag": args=[sys.executable,"-O","-c",code]
            elif mode=="env_opt":
                env=os.environ.copy(); env["PYTHONOPTIMIZE"]="1"
            result=subprocess.run(args,capture_output=True,text=True,env=env)
            self.assertNotEqual(result.returncode,0,(mode,result.stdout,result.stderr))
            self.assertIn("budget_changed_hard_outcome",result.stderr)

if __name__=="__main__": unittest.main(verbosity=2)
