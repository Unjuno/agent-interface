import unittest

from input_evidence_join import join_w_input_samples


class InputEvidenceJoinTests(unittest.TestCase):
    def test_missing_resolver_keeps_expiry_samples_separate(self):
        joined = join_w_input_samples(None, {
            "samples": [{"after_ns": 10, "w_key_down": True}],
            "status": "verified", "lease_deadline_ns": 9,
        })
        self.assertEqual(joined["classification"], "RESOLVER_MISSING")
        self.assertIsNone(joined["resolver"]["samples"])
        self.assertIsNone(joined["resolver"]["terminal_w_down"])
        self.assertEqual(joined["expiry_sampler"]["sample_count"], 1)

    def test_resolver_and_expiry_samples_keep_distinct_provenance(self):
        joined = join_w_input_samples({
            "samples": [{"action_status": "running", "w_key_down": True}],
            "terminal_w_down": False, "claim": "resolver-poll",
        }, {
            "samples": [{"after_ns": 10, "w_key_down": True}],
            "status": "verified", "lease_deadline_ns": 9,
        })
        self.assertEqual(joined["classification"], "BOTH_PRESENT")
        self.assertNotEqual(joined["resolver"]["samples"], joined["expiry_sampler"]["samples"])
        self.assertEqual(joined["resolver"]["claim"], "resolver-poll")

    def test_missing_both_reports_remains_explicit(self):
        joined = join_w_input_samples(None, None)
        self.assertEqual(joined["classification"], "BOTH_MISSING")
        self.assertIsNone(joined["resolver"]["sample_count"])
        self.assertIsNone(joined["expiry_sampler"]["sample_count"])


if __name__ == "__main__":
    unittest.main()
