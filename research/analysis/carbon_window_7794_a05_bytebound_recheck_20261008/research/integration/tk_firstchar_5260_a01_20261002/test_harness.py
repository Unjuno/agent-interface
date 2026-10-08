import json
from pathlib import Path
import tempfile
import unittest

from audit import inspect
from schedule import schedule


ROOT = Path(__file__).parent
SMOKE = ROOT / "fixture_smoke.json"


class HarnessConstructionTests(unittest.TestCase):
    def test_smoke_fixture_is_one_unique_row(self):
        fixture = json.loads(SMOKE.read_text(encoding="utf-8"))
        rows = schedule(fixture)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["coordinate_method"], "CHILD_ROOT_COORD")
        self.assertEqual(rows[0]["first_key_delay_ms"], 50)
        self.assertEqual(rows[0]["load"], "idle")

    def test_smoke03_raw_passes_independent_audit_without_ocr_gate(self):
        raw = ROOT / "construction/smoke-03/out/candidate_stdout.json"
        if not raw.is_file():
            self.skipTest("construction smoke-03 raw artifact is not present")
        result = inspect(raw, raw.parent, image_audit=False)
        self.assertEqual(result["status"], "PASS_AUDIT", result["errors"])
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["exact_save_failures"], 0)

    def test_formal_fixture_is_96_unique_factorial_rows(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        rows = schedule(fixture)
        self.assertEqual(len(rows), 96)
        self.assertEqual(len({(r["coordinate_method"], r["first_key_delay_ms"], r["load"], r["replicate"]) for r in rows}), 96)


if __name__ == "__main__":
    unittest.main()
