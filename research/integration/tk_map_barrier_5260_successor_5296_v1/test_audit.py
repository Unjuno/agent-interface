"""Mutation controls for the retained #5296 construction auditor."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "results/construction-02/raw.json"
AUDIT = HERE / "audit.py"
ALLOCATION = "tk-map-barrier-5260-5296-20260930-02"


class AuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(RAW.read_text(encoding="utf-8"))

    def run_audit(self, row):
        with tempfile.TemporaryDirectory(prefix="5296-audit-") as tmp:
            source, report = Path(tmp) / "raw.json", Path(tmp) / "report.json"
            source.write_text(json.dumps(row), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(AUDIT), str(source), str(report), ALLOCATION],
                                  capture_output=True, text=True, check=False)
            return proc.returncode, json.loads(report.read_text(encoding="utf-8"))

    def test_retained_raw_is_accepted(self):
        code, report = self.run_audit(self.baseline)
        self.assertEqual(code, 0)
        self.assertEqual(report["decision"], "PASS_GEOMETRY_MAP_BARRIER_CONSTRUCTION_ONLY")
        self.assertEqual(report["errors"], [])

    def test_corruptions_are_rejected(self):
        mutations = {}
        row = copy.deepcopy(self.baseline); row["schema"] = "wrong"; mutations["schema"] = row
        row = copy.deepcopy(self.baseline); row["app_exit"] = 1; mutations["app_exit"] = row
        row = copy.deepcopy(self.baseline); row["events"]["Map"] = row["post"]["t"] + 1; mutations["map_after_sample"] = row
        row = copy.deepcopy(self.baseline); row["post"]["mapped"] = 0; mutations["unmapped"] = row
        row = copy.deepcopy(self.baseline); row["post"]["w"] = 0; mutations["zero_width"] = row
        row = copy.deepcopy(self.baseline); row["post"]["x"] = 10000; mutations["center_outside_root"] = row
        row = copy.deepcopy(self.baseline); row["post"]["t"] = row["pre"]["t"] - 1; mutations["clock_inversion"] = row

        rejected = {}
        for name, candidate in mutations.items():
            code, report = self.run_audit(candidate)
            rejected[name] = code != 0 and report["decision"] == "STOP_GEOMETRY_MAP_BARRIER"
        self.assertEqual(rejected, {name: True for name in mutations})
        print(json.dumps({"mutations": len(rejected), "rejected": rejected}, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
