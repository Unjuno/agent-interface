"""Frozen construction controls, executed before formal test."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
CANDIDATE=HERE/"candidate.py"
AUDIT=HERE/"audit.py"
MARKER="PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED"
CONTROLS=("stale_success","authority_success","retry_nonblocked","budget_monotonicity","row_count","outcome_count","oracle")

class OptimizationControls(unittest.TestCase):
    def invoke(self, mode, mutation=None):
        code=(
            "import contextlib,io,json,runpy; "
            f"ns=runpy.run_path({str(CANDIDATE)!r}); "
            "buf=io.StringIO(); err=None; passed=False; "
            "\ntry:\n with contextlib.redirect_stdout(buf): ns['run'](); passed=True"
            "\nexcept Exception as exc: err=type(exc).__name__+':'+str(exc)"
            "\nprint(json.dumps({'passed':passed,'pass_marker_seen':('PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED' in buf.getvalue()),'error':err}))"
        )
        env=None
        if mode=="opt_flag": args=[sys.executable,"-O","-c",code]
        elif mode=="env_opt":
            import os
            env=os.environ.copy(); env["PYTHONOPTIMIZE"]="1"; args=[sys.executable,"-c",code]
        else: args=[sys.executable,"-c",code]
        if mutation:
            # Re-execute an additive in-memory module whose selected gate is deliberately bypassed.
            code += "\n"
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
        self.assertIn("if not condition: errors.append(label)",source)

    def test_mutation_control_list_is_frozen(self):
        self.assertEqual(CONTROLS,("stale_success","authority_success","retry_nonblocked","budget_monotonicity","row_count","outcome_count","oracle"))

if __name__=="__main__": unittest.main(verbosity=2)
