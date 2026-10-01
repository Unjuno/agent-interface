from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from fixtures import cases, valid_rows

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "map01_r133_recovery_coast_t1_v1" / "decision_rule_construction_v2" / "adjudicator.py"
spec = importlib.util.spec_from_file_location("upstream_adjudicator", UPSTREAM)
upstream = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(upstream)


class BoundaryConstructionTests(unittest.TestCase):
    def test_positive_is_instrumentation_only(self):
        got = upstream.adjudicate(valid_rows())
        self.assertEqual(got["instrumentation_status"], "PASS_INSTRUMENTATION_AND_RELEASE")
        self.assertEqual(got["comparative_status"], "UNCERTAIN")

    def test_all_wire_controls_reject_with_exact_reason(self):
        for name, rows, status, reason in cases()[1:]:
            with self.subTest(case=name):
                decoded = json.loads(json.dumps(rows, sort_keys=True, separators=(",", ":")))
                got = upstream.adjudicate(decoded)
                self.assertEqual(got["instrumentation_status"], status)
                self.assertEqual(got.get("reason"), reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
