"""Reject a partial or confounded contrast before allocating any container."""
import copy
import json
import unittest
from pathlib import Path
from runner import check_plan, command

class PlanTests(unittest.TestCase):
    def test_admits_complete_four_condition_balanced_block(self):
        plan = json.loads(Path(__file__).with_name("plan.json").read_text())
        check_plan(plan)

    def test_refuses_missing_duplicate_mislabelled_and_bool_cpu(self):
        plan = json.loads(Path(__file__).with_name("plan.json").read_text())
        for case in ("missing", "duplicate", "offset", "cpu", "budget"):
            p = copy.deepcopy(plan)
            if case == "missing": p["cells"].pop()
            elif case == "duplicate": p["cells"][0] = p["cells"][1]
            elif case == "offset": p["cells"][1]["offsets"] = [0]*4
            elif case == "cpu": p["cells"][0]["cpu"] = True
            else: p["samples_per_cell"] = 7
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    check_plan(p)

    def test_command_uses_own_engine_and_only_requested_cpu_limit(self):
        plan = json.loads(Path(__file__).with_name("plan.json").read_text())
        a = command(plan, plan["cells"][0], "/home/taka/frozen", "/home/taka/out", "diagnostic-only")
        self.assertEqual(a[:7], ["orbctl", "run", "-m", "research-6183-t0-20261003", "-u", "root", "docker"])
        self.assertEqual(a[a.index("--cpus")+1], "1")
        self.assertEqual(a[a.index("--memory")+1], "512m")
        self.assertEqual(a[a.index("--network")+1], "none")
        self.assertIn("type=bind,src=/home/taka/frozen,dst=/src,readonly", a)
        self.assertIn("type=bind,src=/home/taka/out,dst=/out", a)
        self.assertIn("--read-only", a)
        self.assertEqual(a[a.index("--cap-drop")+1], "ALL")
        self.assertEqual(a[a.index("--security-opt")+1], "no-new-privileges")
        b = command(plan, plan["cells"][2], "/home/taka/frozen", "/home/taka/out2", "diagnostic-only")
        self.assertEqual(b[b.index("--cpus")+1], "2")

if __name__ == "__main__":
    unittest.main()
