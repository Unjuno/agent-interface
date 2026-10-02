"""Construction checks for the Issue #6611 finite synthetic assay."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import audit

ROOT = Path(__file__).resolve().parent


class VersionCrossingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.raw_path = Path(cls.temp.name) / "raw.json"
        subprocess.run([sys.executable, "-B", str(ROOT / "candidate.py"), str(ROOT / "fixture.json"), str(cls.raw_path)],
                       check=True, capture_output=True, text=True)
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.raw = json.loads(cls.raw_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_full_record_passes_independent_oracle(self):
        result = audit.evaluate(self.fixture, self.raw)
        self.assertEqual(result["disposition"], "METHOD_PASS_SCOPED")
        self.assertEqual(result["rows"], 16)

    def test_both_routes_pass_same_initial_contract(self):
        self.assertTrue(all(row["initial"]["pass"] for row in self.raw["rows"]))

    def test_open_failure_is_unknown_not_success(self):
        row = next(x for x in self.raw["rows"] if x["case_id"] == "open-failure" and x["route"] == "portable")
        self.assertEqual(row["post"]["status"], "UNKNOWN")

    def test_cosmetic_change_preserves_significant_properties(self):
        row = next(x for x in self.raw["rows"] if x["case_id"] == "cosmetic-harmless-change" and x["route"] == "compact")
        self.assertTrue(all(row["post"][k] for k in ("value_ok", "formula_ok", "link_ok", "render_ok")))

    def test_hash_or_parse_success_cannot_substitute_for_semantic_flags(self):
        corrupted = json.loads(json.dumps(self.raw))
        row = next(x for x in corrupted["rows"] if x["case_id"] == "silent-formula-drop" and x["route"] == "compact")
        row["post"]["formula_ok"] = True
        self.assertEqual(audit.evaluate(self.fixture, corrupted)["disposition"], "FAIL_METHOD")

    def test_unknown_cannot_be_relabelled_as_pass(self):
        corrupted = json.loads(json.dumps(self.raw))
        row = next(x for x in corrupted["rows"] if x["case_id"] == "open-failure" and x["route"] == "portable")
        row["post"]["status"] = "OBSERVED"
        row["post"]["value_ok"] = True
        self.assertEqual(audit.evaluate(self.fixture, corrupted)["disposition"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
