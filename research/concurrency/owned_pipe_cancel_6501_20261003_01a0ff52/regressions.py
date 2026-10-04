"""Ordinary helper/strict-domain regressions, not the formal matrix."""
import json
import unittest

import audit
import candidate


class Regressions(unittest.TestCase):
    def test_owned_close_once(self):
        trace = candidate.Trace()
        trace.pipe("data")
        try:
            trace.close("data_r", "construction")
            with self.assertRaisesRegex(RuntimeError, "double close"):
                trace.close("data_r", "construction")
            self.assertEqual(len([e for e in trace.events if e["kind"] == "fd_closed"]), 1)
        finally:
            trace.close("data_w", "construction")

    def test_boolean_is_not_fd_integer(self):
        self.assertFalse(audit.exact_int(True))
        self.assertFalse(audit.exact_int(1.0))
        self.assertTrue(audit.exact_int(1))

    def test_aggregate_json_preserves_types(self):
        self.assertNotEqual(json.dumps({"done": False}), json.dumps({"done": 0}))

    def test_schema_rejects_empty_matrix(self):
        self.assertEqual(audit.audit([], "unused", {})["status"], "HOLD_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
