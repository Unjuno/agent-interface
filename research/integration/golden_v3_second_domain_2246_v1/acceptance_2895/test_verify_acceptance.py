import unittest
from .verify_acceptance import verify, CASES

class AcceptanceVerifierTests(unittest.TestCase):
    def test_preflight_summary_stops_without_embedded_raw_events(self):
        summary = {
            "scorer_matches": True,
            "formal_receipt_order_ok": True,
            "rows": [
                {"case": name.lower(), "formal_receipt": {"case": name, "input_ledger": [], "cleanup": {}}}
                for name in CASES
            ],
        }
        result = verify(summary)
        self.assertEqual(result["decision"], "STOP_MISSING_RAW_RECEIPT_BUNDLE")
        self.assertEqual(len(result["errors"]), 8)

if __name__ == "__main__":
    unittest.main()
