"""Construction checks for the frozen synthetic Issue #6523 method."""
import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))


class MethodConstructionTests(unittest.TestCase):
    def test_matrix_is_complete_and_independently_reconstructed(self):
        rows = [candidate.run(case, route) for case in SPEC["cases"] for route in SPEC["routes"]]
        raw = {"schema": "ime-commit-effect-raw-v1", "case_count": len(SPEC["cases"]),
               "routes": SPEC["routes"], "row_count": len(rows), "rows": rows}
        self.assertEqual((len(SPEC["cases"]), len(rows)), (12, 48))
        self.assertEqual(audit.audit_object(SPEC, raw), [])
        self.assertTrue(all(audit.corruption_controls(SPEC, raw).values()))

    def test_raw_enter_double_counts_ime_accept_then_submit(self):
        case = next(x for x in SPEC["cases"] if x["id"] == "ime-confirm-then-submit")
        self.assertEqual(candidate.run(case, "RAW_ENTER")["submit_count"], 2)
        self.assertEqual(candidate.run(case, "PHASE_AWARE")["submit_count"], 1)

    def test_phase_aware_waits_for_committed_value_and_submit_intent(self):
        case = next(x for x in SPEC["cases"] if x["id"] == "delayed-value-after-compositionend")
        row = candidate.run(case, "PHASE_AWARE")
        self.assertEqual(row["submit_count"], 1)
        self.assertTrue(row["completion_claim"])

    def test_uncertain_cancelled_stale_or_mismatched_inputs_never_complete(self):
        ids = {"ime-cancel", "stale-focus", "composition-unavailable", "visible-glyph-not-value",
               "literal-enter-without-submit", "native-fill-no-effect", "wrong-effect-value",
               "effect-without-submit"}
        for case in SPEC["cases"]:
            if case["id"] in ids:
                with self.subTest(case=case["id"]):
                    self.assertFalse(candidate.run(case, "PHASE_AWARE")["completion_claim"])

    def test_latin_and_qualified_native_fill_controls_complete(self):
        for case_id, route in (("latin-submit", "PHASE_AWARE"), ("native-fill-exact", "NATIVE_FILL")):
            case = next(x for x in SPEC["cases"] if x["id"] == case_id)
            with self.subTest(case=case_id):
                self.assertTrue(candidate.run(case, route)["completion_claim"])


if __name__ == "__main__":
    unittest.main()
