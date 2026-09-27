from __future__ import annotations

import copy
import json
import unittest

from audit_stop import STOP_PATH, audit


class GpuPreflightStopAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(STOP_PATH.read_text(encoding="utf-8"))

    def test_retained_stop_record_passes(self):
        self.assertEqual(audit(self.record), [])

    def test_changed_raw_error_is_rejected(self):
        record = copy.deepcopy(self.record)
        record["probe"]["stderr"] = ""
        self.assertIn("raw_daemon_error", audit(record))

    def test_model_request_cannot_be_smuggled_into_preflight_stop(self):
        record = copy.deepcopy(self.record)
        record["formal_model_requests"] = 1
        self.assertIn("model_request_count", audit(record))

    def test_formal_or_retry_cannot_be_claimed(self):
        record = copy.deepcopy(self.record)
        record["formal_allocations_run"] = 1
        self.assertIn("formal_or_retry_count", audit(record))


if __name__ == "__main__":
    unittest.main(verbosity=2)
