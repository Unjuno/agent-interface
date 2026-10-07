import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import audit
import candidate


class EffectOracleTests(unittest.TestCase):
    def test_same_local_bits_are_not_independent_effect_truth(self):
        rows = {(r["effect_truth"], r["effect_record_present"], r["completion_receipt_present"]): r
                for r in candidate.rows()[:12]}
        absent = rows[("NOT_OCCURRED", False, False)]
        happened = rows[("OCCURRED", False, False)]
        unknown = rows[("UNAVAILABLE", False, False)]
        self.assertEqual(absent["a01_bits_only"], "NO_EFFECT_CONFIRMED")
        self.assertEqual(happened["a01_bits_only"], absent["a01_bits_only"])
        self.assertEqual(unknown["a01_bits_only"], absent["a01_bits_only"])
        self.assertEqual(absent["strict_classification"], "NO_EFFECT_CONFIRMED")
        self.assertEqual(happened["strict_classification"], "UNKNOWN_RECONCILE")
        self.assertEqual(unknown["strict_classification"], "UNKNOWN_RECONCILE")

    def test_independent_audit_rejects_mutated_false_no_effect(self):
        data = {"schema": "machine-crash-durability-7802-a02-candidate-v1",
                "rows": candidate.rows()}
        data["rows"][0]["strict_classification"] = "NO_EFFECT_CONFIRMED"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "mutant.json"
            path.write_text(json.dumps(data))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = audit.main(path)
        report = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("row-0", report["errors"])


if __name__ == "__main__":
    unittest.main()
