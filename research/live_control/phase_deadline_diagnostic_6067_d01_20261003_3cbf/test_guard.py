"""Regression tests for reviewer-required prospective and per-cell gates."""
import copy
import json
from pathlib import Path
import unittest
import guard
import runner
import test_auditor

class GuardTests(unittest.TestCase):
    def test_available_optional_counter_regressions_are_refused(self):
        for kind in ("local", "sched"):
            f=test_auditor.frame()
            for s,raw in zip((f["pre"],f["post"]),("throttled_usec 2\n","throttled_usec 1\n") if kind=="local" else ("2 2 2","1 1 1")):
                s["cpu_stat_local" if kind=="local" else "schedstat"]={"available":True,"raw":raw,"error":None}
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError): guard.frame_valid(f)

    def test_wrong_source_is_rejected_before_output_creation(self):
        plan=json.loads(Path("plan.json").read_text())
        commands={c["id"]:runner.command(plan,c,"/frozen/source","/frozen/out-"+c["id"],"diagnostic-only") for c in plan["cells"]}
        freeze={"commands":commands}
        with self.assertRaises(ValueError):
            guard.preflight(plan,freeze,"/other/source","/frozen/out",runner.command)

    def test_wrong_output_is_rejected_before_output_creation(self):
        plan=json.loads(Path("plan.json").read_text())
        commands={c["id"]:runner.command(plan,c,"/frozen/source","/frozen/out-"+c["id"],"diagnostic-only") for c in plan["cells"]}
        with self.assertRaises(ValueError):
            guard.preflight(plan,{"commands":commands},"/frozen/source","/different/out",runner.command)

    def test_counter_regression_and_malformed_optional_are_rejected(self):
        for kind in ("counter","schedstat"):
            f=test_auditor.frame()
            if kind=="counter": f["post"]["cpu_stat"]["usage_usec"]=-1
            else: f["post"]["schedstat"]={"available":True,"raw":"garbage","error":None}
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError): guard.frame_valid(f)
if __name__=="__main__": unittest.main()
