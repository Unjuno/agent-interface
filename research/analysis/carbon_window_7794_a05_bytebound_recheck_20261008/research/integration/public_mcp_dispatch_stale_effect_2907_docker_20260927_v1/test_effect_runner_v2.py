import json
import os
import unittest

os.environ.setdefault("SOURCE_COMMIT", "construction-only")
os.environ.setdefault("EXPERIMENT_IMAGE_ID", "construction-only")

import runner_effect_v2 as runner


class ResponseProjectionTests(unittest.TestCase):
    def test_nested_review_receipt(self):
        raw = {"status": "returned", "session_id": "s"}
        payload = {"schema": "agent-interface/review-v1", "call_id": "c",
                   "session": {"session_id": "s"}, "receipt": {
                       "schema": "agent-interface/receipt-view-v1",
                       "source": {"raw_report": raw}}}
        projected, report = runner.decode_payload(json.dumps(payload))
        self.assertEqual(projected, payload)
        self.assertEqual(report, raw)

    def test_flat_management_response(self):
        payload = {"status": "closed", "session_id": "s", "call_id": "c",
                   "release_attempted": True}
        projected, report = runner.decode_payload(json.dumps(payload))
        self.assertEqual(projected, payload)
        self.assertIs(report, projected)

    def test_unknown_envelope_rejected(self):
        with self.assertRaisesRegex(AssertionError, "UNKNOWN_PUBLIC_RESPONSE_SCHEMA"):
            runner.decode_payload(json.dumps({"status": "closed"}))


if __name__ == "__main__":
    unittest.main()
