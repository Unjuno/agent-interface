import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent
spec = importlib.util.spec_from_file_location("historical_audit", DATA / "audit.py")
historical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(historical)
sys.path.insert(0, str(ROOT))
from audit import audit as corrected_audit

trace = json.loads((DATA / "trace.json").read_text(encoding="utf-8"))
rows = [json.loads(line) for line in (DATA / "raw.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


class RecomputedValueAuditTests(unittest.TestCase):
    def test_unmodified_frozen_rows_still_pass_all_existing_controls(self):
        result = corrected_audit(trace, rows)
        self.assertEqual("PASS_DYNAMIC_READSET_SCOPED", result["result"])
        self.assertEqual([], result["errors"])
        self.assertEqual(10, result["metrics"]["mutation_controls_rejected"])
        self.assertEqual(1, result["metrics"]["static_declared_unsafe_reuse"])

    def test_historical_auditor_false_pass_is_reproduced(self):
        targets = [
            ("STATIC_ALL", "s4", "TARGET_MATCH"),
            ("STATIC_DECLARED", "s0", "READY_TO_SUBMIT"),
        ]
        for policy, state, predicate in targets:
            with self.subTest(policy=policy, state=state, predicate=predicate):
                changed = copy.deepcopy(rows)
                row = next(r for r in changed if (r["policy"], r["state"], r["predicate"]) == (policy, state, predicate))
                self.assertEqual("MISS", row["action"])
                row["value"] = "CORRUPTED"
                result = historical.audit(trace, changed)
                self.assertEqual("PASS_DYNAMIC_READSET_SCOPED", result["result"])
                self.assertEqual([], result["errors"])
                self.assertEqual(8, result["metrics"]["mutation_controls_rejected"])

    def test_corrected_auditor_rejects_every_recomputed_value_corruption(self):
        recomputed = [r for r in rows if r["action"] in ("MISS", "RECOMPUTE")]
        self.assertGreater(len(recomputed), 0)
        for expected in recomputed:
            with self.subTest(policy=expected["policy"], state=expected["state"], predicate=expected["predicate"]):
                changed = copy.deepcopy(rows)
                row = next(r for r in changed if (r["policy"], r["state"], r["predicate"]) == (expected["policy"], expected["state"], expected["predicate"]))
                row["value"] = "CORRUPTED"
                result = corrected_audit(trace, changed, controls=False)
                self.assertIn("recomputed_value_mismatch:" + ":".join((row["policy"], row["state"], row["predicate"])), result["errors"])
                self.assertNotEqual("PASS_DYNAMIC_READSET_SCOPED", result["result"])

    def test_expected_stale_static_declared_hit_remains_valid_negative_control(self):
        stale = next(r for r in rows if r["policy"] == "STATIC_DECLARED" and r["action"] == "HIT" and r["value"] != r["oracle_value"])
        self.assertTrue(stale["unsafe_reuse"])
        result = corrected_audit(trace, rows)
        self.assertEqual("PASS_DYNAMIC_READSET_SCOPED", result["result"])
        self.assertEqual(1, result["metrics"]["static_declared_unsafe_reuse"])


if __name__ == "__main__":
    unittest.main()
